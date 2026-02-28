import itertools
from collections.abc import Iterable

import numpy as np
import openmdao.api as om

from pycycle.element_base import Element
from pycycle.elements.compressor_map import CompressorMap
from pycycle.flow_in import FlowIn
from pycycle.maps.ncp01 import NCP01
from pycycle.passthrough import PassThrough
from pycycle.thermo.thermo import Thermo
from pycycle.unit_utils import ENTHALPY_FLOW_TO_POWER, POWER_PER_RPM_TO_TORQUE, STD_DAY, get_unit


class CorrectedInputsCalc(om.ExplicitComponent):
    """Compute design corrected flow (Wc) and design corrected speed (Nc)"""

    def initialize(self):
        self.options.declare('unit_system', default='ENG', values=('ENG', 'SI'))

    def setup(self):
        unit_system = self.options['unit_system']
        # inputs
        self.add_input('Tt', val=500., units=get_unit('temperature', unit_system),
                       desc='incoming temperature')
        self.add_input('Pt', val=14., units=get_unit('pressure', unit_system), desc='incoming pressure')
        self.add_input('W_in', val=30.0, units=get_unit('mass_flow', unit_system), desc='mass flow')
        self.add_input('Nmech', val=1000.0, units='rpm', desc='shaft speed')
        # outputs
        self.add_output('Wc', val=30.0, units=get_unit('mass_flow', unit_system),
                        desc='corrected mass flow')
        self.add_output('Nc', val=100., lower=1e-5,
                        units='rpm', desc='corrected shaft speed')

        self.declare_partials('Wc', ['Tt', 'Pt', 'W_in'])
        self.declare_partials('Nc', ['Nmech', 'Tt'])

    def compute(self, inputs, outputs):
        std_day = STD_DAY[self.options['unit_system']]

        self.delta = inputs['Pt'] / std_day['P']
        self.W = inputs['W_in']
        self.theta = inputs['Tt'] / std_day['T']

        outputs['Wc'] = self.W * self.theta**0.5 / self.delta
        outputs['Nc'] = inputs['Nmech'] * self.theta**-0.5

    def compute_partials(self, inputs, J):

        theta = self.theta
        delta = self.delta
        std_day = STD_DAY[self.options['unit_system']]

        J['Wc', 'Tt'] = 0.5 * self.W / delta * theta**-0.5 / std_day['T']
        J['Wc', 'Pt'] = -self.W * theta**0.5 * delta**-2. / std_day['P']
        J['Wc', 'W_in'] = theta**0.5 / delta
        J['Nc', 'Nmech'] = theta**-0.5
        J['Nc', 'Tt'] = -0.5 * inputs['Nmech'] * theta**-1.5 / std_day['T']

class eff_poly_calc(om.ExplicitComponent):
    """ Calculate polytropic efficiency for compressor"""
    def initialize(self):
        self.options.declare('unit_system', default='ENG', values=('ENG', 'SI'))

    def setup(self):
        unit_system = self.options['unit_system']
        self.add_input('PR', 1.0,units=None, desc='element pressure ratio Pt_out/Pt_in')
        self.add_input('S_in', 1.0,units=get_unit('entropy', unit_system), desc='element input entropy')
        self.add_input('S_out', 1.0,units=get_unit('entropy', unit_system), desc='element output entropy')
        self.add_input('Rt', val=0.0686, units=get_unit('gas_constant', unit_system), desc='specific gas constant')
        # list_outputs
        self.add_output('eff_poly', val=1.0, units=None, desc='polytropic efficiency', lower=1e-6)
        # define partials
        self.declare_partials('eff_poly','*')
    def compute(self, inputs, outputs):
        PR = inputs['PR']
        S_in = inputs['S_in']
        S_out = inputs['S_out']
        Rt = inputs['Rt']

        outputs['eff_poly'] = Rt * np.log(PR) / ( Rt*np.log(PR) + S_out - S_in )

    def compute_partials(self, inputs, J):
        PR     = inputs['PR']
        S_in   = inputs['S_in']
        S_out  = inputs['S_out']
        Rt = inputs['Rt']

        J['eff_poly', 'PR'] = (Rt*(S_out - S_in))/(PR*(np.log(PR)*Rt+S_out-S_in)**2)

        J['eff_poly', 'S_in']  =  (np.log(PR)*Rt)/(np.log(PR)*Rt+S_out-S_in)**2
        J['eff_poly', 'S_out'] = -(np.log(PR)*Rt)/(np.log(PR)*Rt+S_out-S_in)**2

        J['eff_poly', 'Rt'] = (np.log(PR)*(S_out-S_in))/(np.log(PR)*Rt+S_out-S_in)**2


class Power(om.ExplicitComponent):
    """Power calculates shaft power for the compressor or turbine"""
    def initialize(self):
        self.options.declare('unit_system', default='ENG', values=('ENG', 'SI'))

    def setup(self):
        unit_system = self.options['unit_system']
        # inputs
        self.add_input('W', val=30.0, units=get_unit('mass_flow', unit_system), desc='mass flow')
        self.add_input('ht_out', val=20.0, units=get_unit('enthalpy', unit_system),
                       desc='downstream enthalpy')
        self.add_input('ht_in', val=10.0, units=get_unit('enthalpy', unit_system),
                       desc='incoming enthalpy')
        self.add_input('Nmech', val=1000.0, units='rpm', desc='shaft speed')
        # self.add_input('Tt_in', val=500., units='degR', desc='incoming temperature')
        # outputs
        self.add_output('power', shape=1, units=get_unit('power', unit_system), desc='turbine power')
        self.add_output('trq', shape=1, units=get_unit('torque', unit_system), desc='turbine torque')

        self.declare_partials('power', ['W', 'ht_out', 'ht_in'])
        self.declare_partials('trq', '*')

    def compute(self, inputs, outputs):
        enthalpy_flow_to_power = ENTHALPY_FLOW_TO_POWER[self.options['unit_system']]
        power_per_rpm_to_torque = POWER_PER_RPM_TO_TORQUE[self.options['unit_system']]

        outputs['power'] = inputs['W'] * (inputs['ht_in'] - inputs['ht_out']) * enthalpy_flow_to_power
        outputs['trq'] = power_per_rpm_to_torque * outputs['power'] / inputs['Nmech']


    def compute_partials(self, inputs, J):
        enthalpy_flow_to_power = ENTHALPY_FLOW_TO_POWER[self.options['unit_system']]
        power_per_rpm_to_torque = POWER_PER_RPM_TO_TORQUE[self.options['unit_system']]
        ht_in = inputs['ht_in']
        ht_out = inputs['ht_out']
        W = inputs['W']
        Nmech = inputs['Nmech']

        J['power', 'W'] = (ht_in - ht_out) * enthalpy_flow_to_power
        J['power', 'ht_out'] = -W * enthalpy_flow_to_power
        J['power', 'ht_in'] = W * enthalpy_flow_to_power
        # J['power','Nmech'] = 0.

        J['trq', 'W'] = (ht_in - ht_out) * enthalpy_flow_to_power * power_per_rpm_to_torque / Nmech
        J['trq', 'ht_out'] = -W * enthalpy_flow_to_power * power_per_rpm_to_torque / Nmech
        J['trq', 'ht_in'] = W * enthalpy_flow_to_power * power_per_rpm_to_torque / Nmech
        J['trq', 'Nmech'] = -W * (ht_in - ht_out) * enthalpy_flow_to_power * power_per_rpm_to_torque * Nmech**-2.


class BleedsAndPower(om.ExplicitComponent):
    """BleedsAndPower calculates the bleed flows and shaft power for the compressor"""

    def initialize(self):
        self.options.declare('bleed_names', types=Iterable,
                              desc='list of names for the bleed ports')
        self.options.declare('unit_system', default='ENG', values=('ENG', 'SI'))

    def setup(self):
        unit_system = self.options['unit_system']
        self.add_input('W_in', val=30.0, units=get_unit('mass_flow', unit_system),
                       desc='entrance mass flow')
        self.add_input('ht_out', val=20.0, units=get_unit('enthalpy', unit_system),
                       desc='exit total enthalpy')
        self.add_input('ht_in', val=10.0, units=get_unit('enthalpy', unit_system),
                       desc='entrance total enthalpy')
        self.add_input('Pt_out', val=20.0, units=get_unit('pressure', unit_system),
                       desc='exit total pressure')
        self.add_input('Pt_in', val=10.0, units=get_unit('pressure', unit_system),
                       desc='entrance total pressure')
        self.add_input('Nmech', val=1000.0, units='rpm', desc='shaft speed')

        self.add_output('W_out', shape=1, units=get_unit('mass_flow', unit_system), desc='exit mass flow')
        self.add_output('power', shape=1, units=get_unit('power', unit_system), desc='shaft power')
        self.add_output('trq', shape=1, units=get_unit('torque', unit_system), desc='shaft torque')

        self.declare_partials('W_out', 'W_in')
        self.declare_partials('power', ['W_in', 'ht_in', 'ht_out'])
        self.declare_partials('trq', ['W_in', 'ht_in', 'ht_out', 'Nmech'])

        # bleed inputs and outputs
        for BN in self.options['bleed_names']:
            self.add_input(BN + ':frac_W', val=0.0,
                           desc='bleed mass flow fraction (W_bld/W_in)')
            self.add_input(BN + ':frac_P', val=0.0,
                           desc='bleed pressure fraction ((P_bld-P_in)/(P_out-P_in))')
            self.add_input(BN + ':frac_work', val=0.0,
                           desc='bleed work fraction ((h_bld-h_in)/(h_out-h_in))')

            self.add_output(BN + ':stat:W', shape=1, lower=0.0,
                            units=get_unit('mass_flow', unit_system), desc='bleed mass flow')
            self.add_output(BN + ':Pt', shape=1, lower=1e-6,
                            units=get_unit('pressure', unit_system), desc='bleed total pressure')
            self.add_output(BN + ':ht', shape=1, units=get_unit('enthalpy', unit_system),
                            desc='bleed total enthalpy')
            # self.add_output(BN+':power', shape=1, desc='bleed power reduction')

            self.declare_partials('W_out', BN+':frac_W')
            self.declare_partials('power', [BN+':frac_W', BN+':frac_work'])
            self.declare_partials(BN+':stat:W', ['W_in', BN+':frac_W'])
            self.declare_partials(BN+':Pt', ['Pt_in', BN+':frac_P', 'Pt_out'])
            self.declare_partials(BN+':ht', ['ht_in', BN+':frac_work', 'ht_out'])
            self.declare_partials('trq', [BN+':frac_W', BN+':frac_work'])

    def compute(self, inputs, outputs):
        enthalpy_flow_to_power = ENTHALPY_FLOW_TO_POWER[self.options['unit_system']]
        power_per_rpm_to_torque = POWER_PER_RPM_TO_TORQUE[self.options['unit_system']]

        Pt_in = inputs['Pt_in']
        Pt_out = inputs['Pt_out']
        ht_in = inputs['ht_in']
        ht_out = inputs['ht_out']
        W_in = inputs['W_in']

        # calculate flow and power without bleed flows
        outputs['W_out'] = W_in
        outputs['power'] = W_in * (ht_in - ht_out) * enthalpy_flow_to_power

        # calculate bleed specific outputs and modify exit flow and power
        for BN in self.options['bleed_names']:
            BN_stat_W = BN + ':stat:W'
            BN_ht = BN + ':ht'

            stat_W = W_in * inputs[BN + ':frac_W']
            outputs[BN + ':Pt'] = Pt_in + inputs[BN + ':frac_P'] * (Pt_out - Pt_in)
            ht = ht_in + inputs[BN + ':frac_work'] * (ht_out - ht_in)

            outputs['W_out'] -= stat_W
            outputs['power'] -= stat_W * (ht - ht_out) * enthalpy_flow_to_power
            outputs[BN_stat_W] = stat_W
            outputs[BN_ht] = ht

        # calculate torque based on revised power and shaft speed
        outputs['trq'] = power_per_rpm_to_torque * outputs['power'] / inputs['Nmech']

    def compute_partials(self, inputs, J):
        enthalpy_flow_to_power = ENTHALPY_FLOW_TO_POWER[self.options['unit_system']]
        power_per_rpm_to_torque = POWER_PER_RPM_TO_TORQUE[self.options['unit_system']]

        ht_in = inputs['ht_in']
        ht_out = inputs['ht_out']
        W_in = inputs['W_in']
        Nmech = inputs['Nmech']
        delta_Pt = inputs['Pt_out'] - inputs['Pt_in']

        # Jacobian elements without bleed flows
        dW_out_dW_in = 1.0

        dpower_dW_in = (ht_in - ht_out) * enthalpy_flow_to_power
        dpower_dht_in = W_in * enthalpy_flow_to_power
        dpower_dht_out = -W_in * enthalpy_flow_to_power

        dtrq_dW_in = (ht_in - ht_out) * enthalpy_flow_to_power * power_per_rpm_to_torque / Nmech
        dtrq_dht_in = W_in * enthalpy_flow_to_power * power_per_rpm_to_torque / Nmech
        dtrq_dht_out = -W_in * enthalpy_flow_to_power * power_per_rpm_to_torque / Nmech
        dtrq_dNmech = -W_in * (ht_in - ht_out) * enthalpy_flow_to_power * power_per_rpm_to_torque * Nmech**-2.

        # Jacobian elements and modifications due to bleed flows
        for BN in self.options['bleed_names']:
            BN_frac_W = BN + ':frac_W'
            BN_frac_work = BN + ':frac_work'
            BN_Pt = BN + ':Pt'
            BN_stat_W = BN + ':stat:W'
            BN_frac_P = BN + ':frac_P'
            BN_ht = BN + ':ht'

            frac_W = inputs[BN_frac_W]
            frac_work = inputs[BN_frac_work]
            frac_P = inputs[BN_frac_P]

            dW_out_dW_in -= frac_W
            J['W_out', BN_frac_W] = -W_in

            dpower_dW_in -= frac_W * (1.0 - frac_work) * (ht_in - ht_out) * enthalpy_flow_to_power
            dpower_dht_in -= W_in * frac_W * (1.0 - frac_work) * enthalpy_flow_to_power
            dpower_dht_out -= -W_in * frac_W * (1.0 - frac_work) * enthalpy_flow_to_power
            J['power', BN_frac_W] = -W_in * (1.0 - frac_work) * (ht_in - ht_out) * enthalpy_flow_to_power
            J['power', BN_frac_work] = W_in * frac_W * (ht_in - ht_out) * enthalpy_flow_to_power

            J[BN_stat_W, 'W_in'] = frac_W
            J[BN_stat_W, BN_frac_W] = W_in

            J[BN_Pt, 'Pt_in'] = 1.0 - frac_P
            J[BN_Pt, BN_frac_P] = delta_Pt
            J[BN_Pt, 'Pt_out'] = frac_P

            J[BN_ht, 'ht_in'] = 1.0 - frac_work
            J[BN_ht, BN_frac_work] = ht_out - ht_in
            J[BN_ht, 'ht_out'] = frac_work

            dtrq_dW_in -= frac_W * (1.0 - frac_work) * (
                ht_in - ht_out) * enthalpy_flow_to_power * power_per_rpm_to_torque / Nmech
            dtrq_dht_in -= W_in * frac_W * (1.0 - frac_work) * enthalpy_flow_to_power * \
                power_per_rpm_to_torque / Nmech
            dtrq_dht_out -= -W_in * frac_W * (1.0 - frac_work) * enthalpy_flow_to_power * \
                power_per_rpm_to_torque / Nmech
            J['trq', BN_frac_W] = -W_in * (1.0 - frac_work) * (
                ht_in - ht_out) * enthalpy_flow_to_power * power_per_rpm_to_torque / Nmech
            J['trq', BN_frac_work] = W_in * frac_W * (ht_in - ht_out) * \
                enthalpy_flow_to_power * power_per_rpm_to_torque / Nmech
            dtrq_dNmech -= -W_in * frac_W * (1.0 - frac_work) * (
                ht_in - ht_out) * enthalpy_flow_to_power * power_per_rpm_to_torque * Nmech**-2

        J['W_out', 'W_in'] = dW_out_dW_in
        J['power', 'W_in'] = dpower_dW_in
        J['power', 'ht_in'] = dpower_dht_in
        J['power', 'ht_out'] = dpower_dht_out
        J['trq', 'W_in'] = dtrq_dW_in
        J['trq', 'ht_in'] = dtrq_dht_in
        J['trq', 'ht_out'] = dtrq_dht_out
        J['trq', 'Nmech'] = dtrq_dNmech

class EnthalpyRise(om.ExplicitComponent):
    """Calculates enthalpy rise across a compressor"""
    def initialize(self):
        self.options.declare('unit_system', default='ENG', values=('ENG', 'SI'))

    def setup(self):
        unit_system = self.options['unit_system']

        self.add_input('ideal_ht', val=2.0, units=get_unit('enthalpy', unit_system),
                       desc='ideal exit total enthalpy')
        self.add_input('inlet_ht', val=1.0, units=get_unit('enthalpy', unit_system),
                       desc='entrance total enthalpy')
        self.add_input('eff', val=0.5, desc='design efficiency')

        self.add_output('ht_out', shape=1, units=get_unit('enthalpy', unit_system),
                        desc='exit total enthalpy')

        self.declare_partials('ht_out', '*')

    def compute(self, inputs, outputs):
        inlet_ht = inputs['inlet_ht']
        outputs['ht_out'] = (inputs['ideal_ht'] - inlet_ht) / inputs['eff'] + inlet_ht

    def compute_partials(self, inputs, J):
        eff = inputs['eff']

        J['ht_out', 'ideal_ht'] = 1. / eff
        J['ht_out', 'inlet_ht'] = 1 - 1. / eff
        J['ht_out', 'eff'] = - (inputs['ideal_ht'] -
                                inputs['inlet_ht']) * eff**(-2)


class PressureRise(om.ExplicitComponent):
    """A Component that calculates ..."""
    def initialize(self):
        self.options.declare('unit_system', default='ENG', values=('ENG', 'SI'))

    def setup(self):
        unit_system = self.options['unit_system']
        self.add_input('PR', 3.0, desc="design pressure ratio")
        self.add_input('Pt_in', 5.0, units=get_unit('pressure', unit_system),
                       desc="incomming total pressure")

        self.add_output('Pt_out', shape=1, lower=1e-5,
                        units=get_unit('pressure', unit_system), desc="exit total pressure")

        self.declare_partials('Pt_out', '*')

    def compute(self, inputs, outputs):
        outputs['Pt_out'] = inputs['PR'] * inputs['Pt_in']

    def compute_partials(self, inputs, J):
        J['Pt_out', 'Pt_in'] = inputs['PR']
        J['Pt_out', 'PR'] = inputs['Pt_in']


class Compressor(Element):
    """
    Calculates pressure and temperature rise of a flow through a non-ideal compressors,
    using turbomachinery performance maps.

    --------------
    Flow Stations
    --------------
    Fl_I
    Fl_O

    -------------
    Design
    -------------
        inputs
        --------
        map.PRdes
        map.effDes
        map.RlineMap
        alphaMap
        MN

        outputs
        --------
        s_PR
        s_Wc
        s_eff
        s_Nc

    -------------
    Off-Design
    -------------
        inputs
        --------
        s_PR
        s_Wc
        s_eff
        s_Nc
        area

        outputs
        --------
        Wc
        PR
        eff_poly
        Nc
        power
        map.RlineMap
        map.readmap.NcMap
    """

    def initialize(self):
        self.options.declare('map_data', default=NCP01,
                              desc='data container for raw compressor map data')
        self.options.declare('statics', default=True,
                              desc='If True, calculate static properties.')
        self.options.declare('bleed_names', types=(list,tuple), desc='list of names for the bleed ports',
                              default=[])
        self.options.declare('map_interp_method', default='slinear',
                              desc='Method to use for map interpolation. \
                              Options are `slinear`, `cubic`, `quintic`.')
        self.options.declare('map_extrap', default=False, desc='Switch to allow extrapoloation off map')

        self.default_des_od_conns = [
            # (design src, off-design target)
            ('s_Wc', 's_Wc'),
            ('s_PR', 's_PR'),
            ('s_eff', 's_eff'),
            ('s_Nc', 's_Nc'),
            ('Fl_O:stat:area', 'area')
        ]

        super().initialize()

    def pyc_setup_output_ports(self):

        self.copy_flow('Fl_I', 'Fl_O')

        bleeds = self.options['bleed_names']
        for BN in bleeds:
            self.copy_flow('Fl_I', BN)

    def setup(self):

        interp_method = self.options['map_interp_method']
        map_extrap = self.options['map_extrap']
        # self.linear_solver = ScipyGMRES()
        # self.linear_solver.options['atol'] = 2e-8
        # self.linear_solver.options['maxiter'] = 100
        # self.linear_solver.options['restart'] = 100

        # self.nonlinear_solver = Newton()
        # self.nonlinear_solver.options['utol'] = 1e-9

        thermo_method = self.options['thermo_method']
        design = self.options['design']
        bleeds = self.options['bleed_names']
        thermo_data = self.options['thermo_data']
        statics = self.options['statics']
        unit_system = self.options['unit_system']

        composition = self.Fl_I_data['Fl_I']

        # Create inlet flow station
        flow_in = FlowIn(fl_name='Fl_I', unit_system=unit_system)
        self.add_subsystem('flow_in', flow_in, promotes_inputs=['Fl_I:*'])

        self.add_subsystem('corrinputs', CorrectedInputsCalc(unit_system=unit_system),
                           promotes_inputs=(
                               'Nmech', ('W_in', 'Fl_I:stat:W'),
                               ('Pt', 'Fl_I:tot:P'), ('Tt', 'Fl_I:tot:T')),
                           promotes_outputs=('Nc', 'Wc'))

        map_data = self.options['map_data']
        map_calcs = CompressorMap(map_data=map_data, design=design,
                             interp_method=interp_method, extrap=map_extrap, unit_system=unit_system)
        self.add_subsystem('map', map_calcs,
                            promotes=['s_Nc','s_eff','s_Wc','s_PR','Nc','Wc',
                                    'PR','eff','SMN','SMW'])

        # Calculate pressure rise across compressor
        self.add_subsystem('press_rise', PressureRise(unit_system=unit_system), promotes_inputs=[
                           'PR', ('Pt_in', 'Fl_I:tot:P')])

        # Calculate ideal flow station properties
        ideal_flow = Thermo(mode='total_SP',
                            method=thermo_method,
                            thermo_kwargs={'composition':composition,
                                           'spec':thermo_data},
                            unit_system=unit_system)
        self.add_subsystem('ideal_flow', ideal_flow,
                           promotes_inputs=[('S', 'Fl_I:tot:S'),
                                            ('composition', 'Fl_I:tot:composition')])
        self.connect("press_rise.Pt_out", "ideal_flow.P")

        # Calculate enthalpy rise across compressor
        self.add_subsystem("enth_rise", EnthalpyRise(unit_system=unit_system),
                           promotes_inputs=['eff', ('inlet_ht', 'Fl_I:tot:h')])
        self.connect("ideal_flow.h", "enth_rise.ideal_ht")

        # Calculate real flow station properties
        real_flow = Thermo(mode='total_hP', fl_name='Fl_O:tot',
                                  method=thermo_method,
                                  thermo_kwargs={'composition':composition,
                                                 'spec':thermo_data},
                           unit_system=unit_system)
        self.add_subsystem('real_flow', real_flow,
                           promotes_inputs=[
                               ('composition', 'Fl_I:tot:composition')],
                           promotes_outputs=['Fl_O:tot:*'])
        self.connect("enth_rise.ht_out", "real_flow.h")
        self.connect("press_rise.Pt_out", "real_flow.P")
        #clculate Polytropic Efficiency
        self.add_subsystem('eff_poly_calc', eff_poly_calc(unit_system=unit_system),
                            promotes_inputs=[('PR','PR'),
                                             ('S_in','Fl_I:tot:S'),
                                             ('S_out','Fl_O:tot:S'),
                                             # ('Cp','Fl_I:tot:Cp'),
                                             # ('Cv','Fl_I:tot:Cv'),
                                             ('Rt', 'Fl_I:tot:R')],
                            promotes_outputs=['eff_poly'] )

        # Calculate shaft power consumption
        blds_pwr = BleedsAndPower(bleed_names=bleeds, unit_system=unit_system)
        bld_inputs = ['frac_W', 'frac_P', 'frac_work']
        bld_in_vars = ['{0}:{1}'.format(
            bn, in_name) for bn, in_name in itertools.product(bleeds, bld_inputs)]
        bld_out_globs = ['{}:*'.format(bn) for bn in bleeds]

        self.add_subsystem('blds_pwr', blds_pwr,
                           promotes_inputs=['Nmech', ('W_in', 'Fl_I:stat:W'),
                                            ('ht_in', 'Fl_I:tot:h'),
                                            ('Pt_in', 'Fl_I:tot:P'),
                                            ('Pt_out', 'Fl_O:tot:P'), ] + bld_in_vars,
                           promotes_outputs=['power', 'trq', 'W_out'] + bld_out_globs)
        self.connect('enth_rise.ht_out', 'blds_pwr.ht_out')

        bleed_names = []
        for BN in bleeds:

            bleed_names.append(f'{BN}_flow')
            bleed_flow = Thermo(mode='total_hP', fl_name=BN + ":tot",
                                  method=thermo_method,
                                  thermo_kwargs={'composition':composition,
                                                 'spec':thermo_data},
                               unit_system=unit_system)
            self.add_subsystem(BN + '_flow', bleed_flow,
                               promotes_inputs=[
                                   ('composition', 'Fl_I:tot:composition')],
                               promotes_outputs=[f'{BN}:tot:*'])
            self.connect(BN + ':ht', BN + "_flow.h")
            self.connect(BN + ':Pt', BN + "_flow.P")


        if statics:
            if design:
                #   Calculate static properties
                out_stat = Thermo(mode='static_MN', fl_name='Fl_O:stat',
                                  method=thermo_method,
                                  thermo_kwargs={'composition':composition,
                                                 'spec':thermo_data},
                                  unit_system=unit_system)
                self.add_subsystem('out_stat', out_stat,
                                   promotes_inputs=[
                                       'MN', ('composition', 'Fl_I:tot:composition')],
                                   promotes_outputs=['Fl_O:stat:*'])
                self.connect('Fl_O:tot:S', 'out_stat.S')
                self.connect('Fl_O:tot:h', 'out_stat.ht')
                self.connect('W_out', 'out_stat.W')
                self.connect('Fl_O:tot:P', 'out_stat.guess:Pt')
                self.connect('Fl_O:tot:gamma', 'out_stat.guess:gamt')

            else:  # Calculate static properties
                out_stat = Thermo(mode='static_A', fl_name='Fl_O:stat',
                                  method=thermo_method,
                                  thermo_kwargs={'composition':composition,
                                                 'spec':thermo_data},
                                  unit_system=unit_system)
                self.add_subsystem('out_stat', out_stat,
                                   promotes_inputs=[
                                       'area', ('composition', 'Fl_I:tot:composition')],
                                   promotes_outputs=['Fl_O:stat:*'])

                self.connect('Fl_O:tot:S', 'out_stat.S')
                self.connect('Fl_O:tot:h', 'out_stat.ht')
                self.connect('W_out', 'out_stat.W')
                self.connect('Fl_O:tot:P', 'out_stat.guess:Pt')
                self.connect('Fl_O:tot:gamma', 'out_stat.guess:gamt')

            self.set_order(['flow_in', 'corrinputs', 'map',
                            'press_rise','ideal_flow', 'enth_rise',
                            'real_flow','eff_poly_calc' ,'blds_pwr',]
                            + bleed_names + ['out_stat'])

        else:
            self.add_subsystem('W_passthru', PassThrough('W_out',
                                                         'Fl_O:stat:W',
                                                         1.0,
                                                         units=get_unit('mass_flow', unit_system)),
                               promotes=['*'])
            self.set_order(['flow_in', 'corrinputs', 'map',
                            'press_rise','ideal_flow', 'enth_rise',
                            'real_flow','eff_poly_calc' , 'blds_pwr']
                            + bleed_names + ['W_passthru'])


        # define the group level defaults
        self.set_input_defaults('Fl_I:FAR', val=0., units=None)
        self.set_input_defaults('PR', val=2., units=None)
        self.set_input_defaults('eff', val=0.99, units=None)
        if not design:
            self.set_input_defaults('s_PR', val=1.0)
            self.set_input_defaults('s_Wc', val=1.0)
            self.set_input_defaults('s_eff', val=1.0)
            self.set_input_defaults('s_Nc', val=1.0)

            try:
                self.set_input_defaults('map.RlineMap', val=map_data.defaults['RlineMap'])
                self.set_input_defaults('map.NcMap', val=map_data.defaults['NcMap'], units='rpm')
            except Exception:
                pass

        # if not design:
        #     self.set_input_defaults('area', val=1, units='inch**2')

        super().setup()
