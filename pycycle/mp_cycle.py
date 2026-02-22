
from __future__ import annotations

import warnings
from typing import Any, cast

import networkx as nx
import numpy as np
import openmdao.api as om

from pycycle.constants import ALLOWED_THERMOS
from pycycle.element_base import Element
from pycycle.errors import CycleConfigurationError, FlowConnectionError
from pycycle.thermo.cea import species_data
from pycycle.typing import ProblemLike, SystemLike


class Cycle(om.Group): 


    def initialize(self) -> None:
        self.options.declare('design', default=True,
                              desc='Switch between on-design and off-design calculation.')
        self.options.declare('thermo_method', values=ALLOWED_THERMOS, default='CEA',
                              desc='Method for computing thermodynamic properties')

        self.options.declare('thermo_data', default=species_data.janaf,
                              desc='thermodynamic data set.', 
                              recordable=False)

        self._elements: set[Element] = set()

        self._flow_graph: nx.DiGraph = nx.DiGraph()

        # flag needed for user focused error checking to make sure they called super in their sub-class
        self._base_class_super_called = False

        self._children: dict[str, Any] = {}

    def _setup_check(self) -> None: 

        if not self._base_class_super_called: 
            raise CycleConfigurationError(
                "`super().setup()` has not been called within the setup method of "
                f"{self.__class__.__name__}."
            )
        
    def pyc_add_element(self, name: str, element: Element, **kwargs: Any) -> None:
        """
        A thin wrapper around `add_subsystem` to keep track of 
        the elements in a given cycle, separate from the general 
        components (e.g. BalanceComp, ExecComp, etc.)
        """

        warnings.simplefilter('always', DeprecationWarning)
        warnings.warn("Deprecation warning: `pyc_add_element` function is deprecated because it is no longer needed. " 
                       "Use the `add_subsystem` method." )
        warnings.simplefilter('ignore', DeprecationWarning)

        self.add_subsystem(name, element, **kwargs)


    def add_subsystem(self, name: str, subsys: Any, **kwargs: Any):
        """
        Customized version of the OpenMDAO Group API method that does 
        additional tracking of elements for the Cycle
        """

        self._children[name] = subsys

        if isinstance(subsys, Element): 
            self._elements.add(subsys)
            if 'thermo_method' in subsys.options:
                subsys.options['thermo_method'] = self.options['thermo_method']

            self._flow_graph.add_node(name, type='element')

        #TODO: Find some way to error check based on _base_class_super_called to let user know they forgot a call to super
        return super().add_subsystem(name, subsys, **kwargs)


    def setup(self) -> None: 

        self._base_class_super_called = True


        # Code that follows the flow-graph and propagates thermo setup data down the chain
        node_types = nx.get_node_attributes(self._flow_graph, 'type')
        node_parents = nx.get_node_attributes(self._flow_graph, 'parent')
        node_port_names = nx.get_node_attributes(self._flow_graph, 'port_name')

        G = self._flow_graph

        # put all starting nodes into a FIFO queue
        queue = [node for node in self._flow_graph if G.in_degree(node) == 0]
        visited = set() # use a set, because checking "in" on a queue is slow


        # loop over all child subsystems and push down cycle level options 
        cycle_level_options = ['thermo_method', 'thermo_data', 'design']
        for child_name, child in self._children.items():
            for opt in cycle_level_options: 
                if opt in child.options: 
                    child.options[opt] = self.options[opt]


        # note: three kinds of nodes in graph, elements, in_ports, out_ports. 
        #       The graph is a tree with (potentially) multiple separate root nodes. 
        #       We will do a breadth first search, starting from all starting nodes at the same time. 
        #       This makes sure that Elements with multiple inputs will have all
        #       predecessors set up before we get to them. 
        while queue:
            node = queue.pop(0) 
            node_type = node_types[node]

            # make sure we've already processed all predecessor nodes
            # if not skip this one, we'll hit it again later
            ready_for_node = True

            for p in G.predecessors(node): 
                if p not in visited: 
                    ready_for_node = False
                    break
            if not ready_for_node:
                continue

            queue.extend(G.successors(node))

            if node not in visited: 

                if node_type == 'element': 
                    node_element = cast(Element, self._get_subsystem(node))
                    node_element.pyc_setup_output_ports()

                # connection will be out_port -> in_port
                elif node_type == 'out_port': 
                    src_element = cast(Element, self._get_subsystem(node_parents[node]))
                    links = G.out_edges(node)
                    for link in links: 
                        # in almost every case there should only be one link, because otherwise you are creating extra mass flow 
                        # the one exception is for the cooling calcs, which get some "weak" connections from turbine and bleed srcs
                        
                        target_element = cast(Element, self._get_subsystem(node_parents[link[1]]))

                        # if target element is None there are two options: 
                        # 1) there is a sub-cycle that you need to push into 
                        #        in this case, get the containing sub-cycle and push some starting nodes into its graph based on this linkage
                        # 2) they made a mistake in the element name, so throw an error
                        # print(node_parents[link[1]])

                        out_port = node_port_names[node]
                        in_port = node_port_names[link[1]]
                        # this passes whatever configuration data there was from the src element to the target keyed by port names

                        if out_port not in src_element.Fl_O_data: 
                            raise FlowConnectionError(
                                "Missing output port data while wiring flow graph. "
                                f"cycle={self.pathname}, src={src_element.pathname}, "
                                f"out_port={out_port}"
                            )

                        target_element.Fl_I_data[in_port] = src_element.Fl_O_data[out_port]

                visited.add(node)


    def pyc_connect_flow(
        self,
        fl_src: str,
        fl_target: str,
        connect_stat: bool = True,
        connect_tot: bool = True,
        connect_w: bool = True,
    ) -> None:
        """ 
        helper function to connect all of the flow variables between two ports 
        """

        # always connect compositions, because these are shape_by_conn=True
        self.connect(f'{fl_src}:tot:composition', [f'{fl_target}:tot:composition', f'{fl_target}:stat:composition'])
        # total
        if connect_tot:
            for v_name in ('h','T','P','S','rho','gamma','Cp','Cv', 'R'):
                self.connect('%s:tot:%s'%(fl_src, v_name), '%s:tot:%s'%(fl_target, v_name))

        # static
        if connect_stat:
            for v_name in ('V', 'Vsonic'):  # ('Wc', 'W', 'FAR'):
                self.connect('%s:stat:%s'%(fl_src, v_name), '%s:stat:%s'%(fl_target, v_name))

            for v_name in ('Cp', 'Cv', 'MN', 'P', 'S', 'T', 'area', 'gamma', 'h', 'rho'):
                self.connect('%s:stat:%s'%(fl_src, v_name), '%s:stat:%s'%(fl_target, v_name))

        if connect_w:
           self.connect('%s:stat:W'%(fl_src,), '%s:stat:W'%(fl_target,))

        # build the directed graph of flow connections
        src_element_name = ''.join(fl_src.split('.')[:-1])
        src_port_name = fl_src.split('.')[-1]

        target_elment_name = ''.join(fl_target.split('.')[:-1])
        target_port_name = fl_target.split('.')[-1]

        # element nodes are needed so we can map from flow ports through elements
        # self._flow_graph.add_node(src_element_name, type='element')
        # self._flow_graph.add_node(target_elment_name, type='element')
        
        self._flow_graph.add_node(fl_src, type='out_port', parent=src_element_name, port_name=src_port_name)
        self._flow_graph.add_node(fl_target, type='in_port', parent=target_elment_name, port_name=target_port_name)

        self._flow_graph.add_edge(src_element_name, fl_src)
        self._flow_graph.add_edge(fl_src, fl_target)
        self._flow_graph.add_edge(fl_target, target_elment_name)

class MPCycle(om.Group): 

    def __init__(self, **kwargs: Any) -> None: 
        self._cycle_params: dict[str, tuple[Any, str | None]] = {}
        self._des_pnt: Any | None = None
        self._od_pnts: list[Any] = []
        self._des_od_connections: list[tuple[str, str]] = []
        self._use_default_des_od_conns = False
        super(MPCycle, self).__init__(**kwargs)


    def pyc_add_cycle_param(self, name: str, val: Any, units: str | None = None) -> None: 

        # TODO: Throw error if this is called after setup

        if name in self._cycle_params: 
            raise CycleConfigurationError(
                f"Cycle parameter `{name}` already exists."
            )

        self._cycle_params[name] = (val, units)

    def pyc_connect_des_od(self, src: str, target: str) -> None: 
        if self._des_pnt is None:
            raise CycleConfigurationError(
                "Cannot connect between design and off-design: no design point created. "
                "Use pyc_add_pnt to add a design point."
            )

        elif self._od_pnts == []:
            raise CycleConfigurationError(
                "Cannot connect between design and off-design: no off-design point created. "
                "Use pyc_add_pnt to add an off-design point."
            )

        self._des_od_connections.append((src, target))

    def pyc_use_default_des_od_conns(self, skip: set[str] | None = None) -> None: 
        if self._des_pnt is None:
            raise CycleConfigurationError(
                "Cannot connect between design and off-design: no design point created. "
                "Use pyc_add_pnt to add a design point."
            )

        elif self._od_pnts == []:
            raise CycleConfigurationError(
                "Cannot connect between design and off-design: no off-design point created. "
                "Use pyc_add_pnt to add an off-design point."
            )

        self._default_des_od_cons_skip = skip
        self._use_default_des_od_conns = True

    def pyc_add_pnt(self, name: str, pnt: Any, **kwargs: Any) -> Any:
        if pnt.options['design'] is True:
            if self._des_pnt is not None:
                raise CycleConfigurationError(
                    "Only one design point is allowed. "
                    f"Design point `{self._des_pnt.name}` already exists."
                )

            self.add_subsystem(name, pnt, **kwargs)
            self._des_pnt = pnt
        elif pnt.options['design'] is False:
            self.add_subsystem(name, pnt, **kwargs)
            self._od_pnts.append(pnt)
            
        return pnt


    def configure(self) -> None: 
        # after all child pts have been set up, 
        # promote any cycle parameters to this level and set their default values
        # then issue connections between the design and off-design points

        if self._des_pnt is None:
            return

        des_pnt = self._des_pnt

        for param, (val, units) in self._cycle_params.items(): 
            self.set_input_defaults(name=param, val=val, units=units)
        
            self.promotes(des_pnt.name, inputs=[param])
            for pnt in self._od_pnts: 
                self.promotes(pnt.name, inputs=[param])


        for src, target in self._des_od_connections: 
            for od_pnt in self._od_pnts: 
                self.connect(f'{des_pnt.name}.{src}', f'{od_pnt.name}.{target}')
        
        if self._use_default_des_od_conns: 
            skip = self._default_des_od_cons_skip
            for elem in des_pnt._elements: 
                if  skip is not None and elem.name in skip: 
                    continue
                try: 
                    for src, target in elem.default_des_od_conns: 
                        for od_pnt in self._od_pnts: 
                            self.connect( f'{des_pnt.name}.{elem.name}.{src}', f'{od_pnt.name}.{elem.name}.{target}')
                except AttributeError: 
                    pass # no des-to-od conns defined

    def _resolve_point_name(self, point_name: str | None = None) -> str:
        if point_name is not None:
            return point_name

        if self._od_pnts:
            return self._od_pnts[0].name

        if self._des_pnt is not None:
            return self._des_pnt.name

        raise CycleConfigurationError(
            'No points have been created on this MPCycle instance.'
        )

    def checkpoint_state(
        self, point_name: str | None = None, include_inputs: bool = False
    ) -> dict[str, Any]:
        """
        Capture a snapshot of solver state for a point (outputs, and optionally inputs).

        Parameters
        ----------
        point_name : str, optional
            Name of the point to checkpoint. Defaults to first off-design point, else design point.
        include_inputs : bool
            If True, include inputs as well as outputs in the checkpoint.
        """
        point_name = self._resolve_point_name(point_name)
        pnt = cast(SystemLike, self._get_subsystem(point_name))

        outputs = pnt.list_outputs(out_stream=None, return_format='list', prom_name=False)
        state = {
            'point_name': point_name,
            'outputs': {name: np.copy(meta['val']) for name, meta in outputs},
        }

        if include_inputs:
            inputs = pnt.list_inputs(out_stream=None, return_format='list', prom_name=False)
            state['inputs'] = {name: np.copy(meta['val']) for name, meta in inputs}

        return state

    def restore_state(
        self,
        state: dict[str, Any],
        point_name: str | None = None,
        include_inputs: bool = False,
        strict: bool = False,
    ) -> None:
        """
        Restore a previously captured solver state for a point.

        Parameters
        ----------
        state : dict
            Checkpoint dict returned by checkpoint_state().
        point_name : str, optional
            Override point name from the checkpoint.
        include_inputs : bool
            If True, also restore inputs contained in the checkpoint.
        strict : bool
            If True, raise on any set_val failure. If False, ignore missing vars.
        """
        if not isinstance(state, dict) or 'outputs' not in state:
            raise CycleConfigurationError(
                'State must be a dict returned by checkpoint_state().' 
                ' Expected keys: outputs (and optional inputs, point_name).'
            )

        point_name = self._resolve_point_name(point_name or state.get('point_name'))
        pnt = cast(SystemLike, self._get_subsystem(point_name))

        def _set_vars(var_dict: dict[str, Any]) -> None:
            for name, val in var_dict.items():
                try:
                    pnt.set_val(name, val)
                except Exception:
                    if strict:
                        raise

        _set_vars(state.get('outputs', {}))
        if include_inputs:
            _set_vars(state.get('inputs', {}))

    def solve_case_sequence(
        self,
        cases: list[dict[str, tuple[Any, str | None]]],
        point_name: str | None = None,
        prob: ProblemLike | None = None,
        outputs: list[str] | None = None,
        warm_start: bool = True,
        continue_on_failure: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Run a sequence of operating points with optional warm-starting.

        Parameters
        ----------
        cases : list of dict
            Sequence of operating conditions: {var_name: (value, units)}.
        point_name : str, optional
            Which operating point to sweep. Defaults to first off-design point, else design.
        prob : om.Problem
            Problem instance used to execute run_model().
        outputs : list[str], optional
            Variables to extract after each converged case.
        warm_start : bool
            If True, restore previous converged state before each new case.
        continue_on_failure : bool
            If True, continue to next case after failure; otherwise re-raise.
        """
        if prob is None:
            raise CycleConfigurationError(
                'solve_case_sequence requires an om.Problem instance via prob=...'
            )

        point_name = self._resolve_point_name(point_name)

        results: list[dict[str, Any]] = []
        last_state = None

        for case in cases:
            for var, (val, units) in case.items():
                target = var if '.' in var else f'{point_name}.{var}'
                if units is None:
                    prob.set_val(target, val)
                else:
                    prob.set_val(target, val, units=units)

            if warm_start and last_state is not None:
                self.restore_state(last_state, point_name=point_name)

            try:
                prob.run_model()
                last_state = self.checkpoint_state(point_name)

                result: dict[str, Any] = {'success': True}
                if outputs:
                    extracted = {}
                    for name in outputs:
                        out_name = name if '.' in name else f'{point_name}.{name}'
                        extracted[name] = np.copy(prob.get_val(out_name))
                    result['outputs'] = extracted
                results.append(result)
            except Exception as err:
                results.append({'success': False, 'error': str(err)})
                if not continue_on_failure:
                    raise

        return results
