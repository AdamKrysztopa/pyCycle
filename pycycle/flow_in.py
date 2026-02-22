"""FlowIN component which serves as an input flowstation for cycle components."""

from __future__ import annotations

from typing import Any

import openmdao.api as om


class FlowIn(om.ExplicitComponent):
    """
    Provides a central place to connect flow information to in a component
    but doesn't actually do anything on its own.
    """

    def initialize(self) -> None:
        self.options.declare('fl_name', default='flow', desc='thermodynamic data set')

    def setup(self) -> None:
        fl_name = self.options['fl_name']

        self.add_output(
            'foo',
            val=1.0,
            desc=(
                "dummy output that is NOT used for anything other than to keep the framework happy. "
            ),
        )

        self.add_input(f'{fl_name}:tot:h', val=1.0, desc='total enthalpy', units='Btu/lbm')
        self.add_input(f'{fl_name}:tot:T', val=518.0, desc='total temperature', units='degR')
        self.add_input(f'{fl_name}:tot:P', val=1.0, desc='total pressure', units='lbf/inch**2')
        self.add_input(f'{fl_name}:tot:rho', val=1.0, desc='total density', units='lbm/ft**3')
        self.add_input(f'{fl_name}:tot:gamma', val=1.4, desc='total gamma')
        self.add_input(
            f'{fl_name}:tot:Cp',
            val=1.0,
            desc='total Specific heat at constant pressure',
            units='Btu/(lbm*degR)',
        )
        self.add_input(
            f'{fl_name}:tot:Cv',
            val=1.0,
            desc='total Specific heat at constant volume',
            units='Btu/(lbm*degR)',
        )
        self.add_input(
            f'{fl_name}:tot:S',
            val=1.0,
            desc='total entropy',
            units='Btu/(lbm*degR)',
        )
        self.add_input(
            f'{fl_name}:tot:R',
            val=1.0,
            desc='total gas constant',
            units='Btu/(lbm*degR)',
        )
        self.add_input(
            f'{fl_name}:tot:composition', shape_by_conn=True, desc='flow composition vector'
        )

        self.add_input(f'{fl_name}:stat:h', val=1.0, desc='static enthalpy', units='Btu/lbm')
        self.add_input(f'{fl_name}:stat:T', val=518.0, desc='static temperature', units='degR')
        self.add_input(f'{fl_name}:stat:P', val=1.0, desc='static pressure', units='lbf/inch**2')
        self.add_input(f'{fl_name}:stat:rho', val=1.0, desc='static density', units='lbm/ft**3')
        self.add_input(f'{fl_name}:stat:gamma', val=1.4, desc='static gamma')
        self.add_input(
            f'{fl_name}:stat:Cp',
            val=1.0,
            desc='static Specific heat at constant pressure',
            units='Btu/(lbm*degR)',
        )
        self.add_input(
            f'{fl_name}:stat:Cv',
            val=1.0,
            desc='static Specific heat at constant volume',
            units='Btu/(lbm*degR)',
        )
        self.add_input(
            f'{fl_name}:stat:S',
            val=0.0,
            desc='static entropy',
            units='Btu/(lbm*degR)',
        )
        self.add_input(
            f'{fl_name}:stat:R',
            val=1.0,
            desc='static gas constant',
            units='Btu/(lbm*degR)',
        )
        self.add_input(
            f'{fl_name}:stat:composition', shape_by_conn=True, desc='flow composition vector'
        )

        # TODO takes these out of static (keep them top level)
        self.add_input(f'{fl_name}:stat:V', val=1.0, desc='Velocity', units='ft/s')
        self.add_input(
            f'{fl_name}:stat:Vsonic', val=1.0, desc='Speed of sound', units='ft/s'
        )
        self.add_input(f'{fl_name}:stat:MN', val=1.0, desc='Mach number')
        self.add_input(f'{fl_name}:stat:area', val=1.0, desc='flow area', units='inch**2')
        self.add_input(
            f'{fl_name}:stat:Wc', val=1.0, desc='corrected weight flow', units='lbm/s'
        )
        self.add_input(f'{fl_name}:stat:W', val=0.0, desc='weight flow', units='lbm/s')
        self.add_input(f'{fl_name}:FAR', val=0.0, desc='fuel to air ratio')
        # self.add_input(f'{fl_name}:WAR', val=0.0, desc='water to air ratio')
        # self.add_input(f'{fl_name}:nu', val=1.0, desc='dynamic viscosity', units='lbm/(s*ft)')

    def compute(self, inputs: Any, outputs: Any) -> None:
        pass
