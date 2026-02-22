import openmdao.api as om
from openmdao.solvers.linesearch.backtracking import BoundsEnforceLS

from pycycle.constants import ALLOWED_THERMOS
from pycycle.thermo.thermo import ThermoAdd


class CallbackBoundsEnforceLS(BoundsEnforceLS):
    """
    BoundsEnforceLS with a user callback before/after bounds enforcement.

    Callback signature: callback(linesearch, phase, **kwargs)
    where phase is 'pre' or 'post'.
    """

    def __init__(self, callback=None, **kwargs):
        super().__init__(**kwargs)
        self._callback = callback

    def _enforce_bounds(self, step, alpha):
        if self._callback is not None:
            self._callback(self, 'pre', step=step, alpha=alpha)
        super()._enforce_bounds(step, alpha)
        if self._callback is not None:
            self._callback(self, 'post', step=step, alpha=alpha)


class Element(om.Group): 
    """
    Custom pyCycle group for anything that requires input or output ports
    """

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        self.Fl_I_data = {}
        self.Fl_O_data = {}

    def initialize(self): 

        self.options.declare('design', default=True, 
                              desc='Switch between on-design and off-design calculation.')
        self.options.declare('thermo_data', default=False,
                              desc='thermodynamic data specific to this element', recordable=False)
        self.options.declare('thermo_method', default='CEA', values=ALLOWED_THERMOS,
                              desc='Method for computing thermodynamic properties')
        self.options.declare('linesearch_callback', default=None, recordable=False,
                              desc='Optional callback for BoundsEnforceLS linesearch')

    def copy_flow(self, src_port, output_port): 
        """
        Copy the flow data from `src_from` port to `target_to` port

        src_port: str or <ThermoAdd>
            the name of the input port to copy from, or the ThermoAdd instance to query
        """

        if isinstance(src_port, str): 
            self.Fl_O_data[output_port] = self.Fl_I_data[src_port]
        elif isinstance(src_port, ThermoAdd): 
            self.Fl_O_data[output_port] = src_port.output_port_data()
        else: 
            raise ValueError('copy_from argument must be either a string that is '
                             'the name of an input port, or a ThermoAdd instance')

    def init_output_flow(self, port_name, port_data): 
        """
        Initialize the given output port with the pord_data
        """

        if isinstance(port_data, ThermoAdd): 
            self.Fl_O_data[port_name] = port_data.output_port_data()
        else: 
            self.Fl_O_data[port_name] = port_data

    def configure(self):
        callback = self.options['linesearch_callback']
        if callback is None:
            return

        solver = self.nonlinear_solver
        if solver is None:
            return

        linesearch = getattr(solver, 'linesearch', None)
        if linesearch is None:
            return

        if isinstance(linesearch, BoundsEnforceLS) and not isinstance(linesearch, CallbackBoundsEnforceLS):
            wrapped = CallbackBoundsEnforceLS(callback=callback)
            for name in linesearch.options:
                wrapped.options[name] = linesearch.options[name]
            solver.linesearch = wrapped


    # TODO: at end of setup, compare all the ports to whats in the port data and make sure that there is nothing missing





