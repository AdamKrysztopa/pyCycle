from __future__ import annotations

from typing import Any, Callable

import openmdao.api as om
from openmdao.solvers.linesearch.backtracking import BoundsEnforceLS

from pycycle.constants import ALLOWED_THERMOS
from pycycle.errors import FlowConnectionError
from pycycle.thermo.thermo import ThermoAdd


class CallbackBoundsEnforceLS(BoundsEnforceLS):
    """
    BoundsEnforceLS with a user callback before/after bounds enforcement.

    Callback signature: callback(linesearch, phase, **kwargs)
    where phase is 'pre' or 'post'.
    """

    def __init__(self, callback: Callable[..., None] | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._callback = callback

    def _enforce_bounds(self, step: Any, alpha: Any) -> None:
        if self._callback is not None:
            self._callback(self, 'pre', step=step, alpha=alpha)
        super()._enforce_bounds(step, alpha)
        if self._callback is not None:
            self._callback(self, 'post', step=step, alpha=alpha)


class Element(om.Group):
    """
    Custom pyCycle group for anything that requires input or output ports
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        self.Fl_I_data: dict[str, Any] = {}
        self.Fl_O_data: dict[str, Any] = {}

    def initialize(self) -> None:
        self.options.declare(
            'design',
            default=True,
            desc='Switch between on-design and off-design calculation.',
        )
        self.options.declare(
            'thermo_data',
            default=False,
            desc='thermodynamic data specific to this element',
            recordable=False,
        )
        self.options.declare(
            'thermo_method',
            default='CEA',
            values=ALLOWED_THERMOS,
            desc='Method for computing thermodynamic properties',
        )
        self.options.declare(
            'linesearch_callback',
            default=None,
            recordable=False,
            desc='Optional callback for BoundsEnforceLS linesearch',
        )

    def copy_flow(self, src_port: str | ThermoAdd, output_port: str) -> None:
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
            raise FlowConnectionError(
                'copy_flow argument must be either a string input port name '
                'or a ThermoAdd instance.'
            )

    def init_output_flow(self, port_name: str, port_data: Any) -> None:
        """
        Initialize the given output port with the pord_data
        """

        if isinstance(port_data, ThermoAdd):
            self.Fl_O_data[port_name] = port_data.output_port_data()
        else:
            self.Fl_O_data[port_name] = port_data

    def configure(self) -> None:
        callback = self.options['linesearch_callback']
        if callback is None:
            return

        solver = self.nonlinear_solver
        if solver is None:
            return

        linesearch = getattr(solver, 'linesearch', None)
        if linesearch is None:
            return

        if isinstance(linesearch, BoundsEnforceLS) and not isinstance(
            linesearch, CallbackBoundsEnforceLS
        ):
            wrapped = CallbackBoundsEnforceLS(callback=callback)
            for name in linesearch.options:
                wrapped.options[name] = linesearch.options[name]
            solver.linesearch = wrapped
    def pyc_setup_output_ports(self) -> None:
        """Populate Fl_O_data for output ports (subclasses should override)."""
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement pyc_setup_output_ports()."
        )

    # TODO: at end of setup, compare all the ports to whats in the port data and make sure that there is nothing missing










