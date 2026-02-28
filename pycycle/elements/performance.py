from openmdao.api import ExplicitComponent
from pycycle.unit_utils import get_unit


class Performance(ExplicitComponent):
    """Component to calculate overall engine performance parameters"""

    def initialize(self):

        self.options.declare('num_nozzles', default=1, types=int)
        self.options.declare('num_burners', default=1, types=int)
        self.options.declare('unit_system', default='ENG', values=('ENG', 'SI'))

    def setup(self):
        unit_system = self.options['unit_system']
        # inputs
        self.add_input('Pt2', val=14.696, units=get_unit('pressure', unit_system), desc='pressure at the inlet of the first compressor')
        self.add_input('Pt3', val=14.696, units=get_unit('pressure', unit_system), desc='pressure at the exit of the last compressor')
        # self.add_input('Wfuel', val=0.0, units='lbm/s', desc='mass flow rate of fuel to combustor')
        self.add_input('ram_drag', val=0.0, units=get_unit('force', unit_system), desc='ram drag from inlet')
        self.add_input('power', val=1.0, units=get_unit('power', unit_system), desc='shaft power')

        num_nozzles = self.options['num_nozzles']
        self.Fg_vals = []
        for i in range(num_nozzles):
            Fg_val_name = 'Fg_{:d}'.format(i)
            self.add_input(Fg_val_name, val=0., units=get_unit('force', unit_system), desc='gross thrust from nozzle {:d}'.format(i))
            self.Fg_vals.append(Fg_val_name)

        num_burners = self.options['num_burners']
        self.Wfuel_vals = []
        for i in range(num_burners):
            Wfuel_val_name = 'Wfuel_{:d}'.format(i)
            self.add_input(Wfuel_val_name, val=0., units=get_unit('mass_flow', unit_system), desc='fuel flow rate entering combustor {:d}'.format(i))
            self.Wfuel_vals.append(Wfuel_val_name)

        # outputs
        self.add_output('OPR', val=1.0, desc='overall pressure ratio, Pt3/Pt2')
        self.add_output('Fg', val=10000.0, units=get_unit('force', unit_system), desc='gross thrust of all nozzles')
        self.add_output('Fn', val=10000.0, units=get_unit('force', unit_system), desc='net thrust of the engine')

        self.declare_partials('OPR', ['Pt3', 'Pt2'])
        self.declare_partials('Fg', 'Fg_*', val=1.0)
        self.declare_partials('Fn', 'Fg_*', val=1.0)
        self.declare_partials('Fn', 'ram_drag', val=-1.0)

        if num_burners > 0:
            self.add_output('TSFC', val=1.0, units=f"{get_unit('mass_flow', unit_system)}/(h*{get_unit('force', unit_system)})", desc='thrust specific fuel consumption')
            self.add_output('PSFC', val=1.0, units=f"{get_unit('mass_flow', unit_system)}/(h*{get_unit('power', unit_system)})", desc='power specific fuel consumption')
            self.add_output('Wfuel', val=.001, units=get_unit('mass_flow', unit_system), desc='mass flow rate of fuel to combustor')


            self.declare_partials('TSFC', ['Fg_*', 'ram_drag', 'Wfuel_*'])
            self.declare_partials('PSFC', ['power', 'Wfuel_*'])
            self.declare_partials('Wfuel', 'Wfuel_*', val=1.0)


    def compute(self, inputs, outputs):

        outputs['OPR'] = inputs['Pt3'] / inputs['Pt2']

        Fg = 0.0
        for Fg_val in self.Fg_vals:
            Fg += inputs[Fg_val]
        outputs['Fn'] = Fn = Fg - inputs['ram_drag']
        outputs['Fg'] = Fg

        if self.Wfuel_vals:
            Wfuel = 0.0
            for Wfuel_val in self.Wfuel_vals:
                Wfuel += inputs[Wfuel_val]

            outputs['Wfuel'] = Wfuel
            outputs['TSFC'] = Wfuel * 3600. / (Fn+1e-10)
            outputs['PSFC'] = Wfuel * 3600. / inputs['power']

    def compute_partials(self, inputs, J):
        Pt2 = inputs['Pt2']
        power = inputs['power']

        J['OPR', 'Pt3'] = 1 / Pt2
        J['OPR', 'Pt2'] = -inputs['Pt3'] / Pt2 ** 2

        wfuel = 0.0
        for Wfuel_val in self.Wfuel_vals:
            wfuel += inputs[Wfuel_val]

        fg = 0.0
        for Fg_val in self.Fg_vals:
            fg += inputs[Fg_val]
        fn = fg - inputs['ram_drag']

        for Fg_val in self.Fg_vals:
            if self.Wfuel_vals:
                J['TSFC', Fg_val] = -3600.0 * wfuel / fn ** 2

        for Wfuel_val in self.Wfuel_vals:
            J['TSFC', Wfuel_val] = 3600.0 / fn
            J['PSFC', Wfuel_val] = 3600. / power

        # J['TSFC', 'Wfuel'] = 3600.0/(outputs['Fg'] - inputs['ram_drag'])
        if self.Wfuel_vals:
            J['TSFC', 'ram_drag'] = 3600.0 * wfuel / fn ** 2
            J['PSFC', 'power'] = -3600. * wfuel / power ** 2


if __name__ == "__main__":
    from openmdao.core.problem import Problem, IndepVarComp

    p = Problem()

    des_vars = p.model.add_subsystem('des_vars', IndepVarComp(), promotes=['*'])
    des_vars.add_output('power', 200.0, units=get_unit('power', 'ENG'))
    des_vars.add_output('Pt2', 204.696, units=get_unit('pressure', 'ENG'))
    des_vars.add_output('Pt3', 104.696, units=get_unit('pressure', 'ENG'))
    des_vars.add_output('Wfuel_0', 2, units=get_unit('mass_flow', 'ENG'))
    des_vars.add_output('ram_drag', 100, units=get_unit('force', 'ENG'))
    des_vars.add_output('Fg_0', 1200, units=get_unit('force', 'ENG'))
    des_vars.add_output('Fg_1', 2000, units=get_unit('force', 'ENG'))

    p.model.add_subsystem('comp', Performance(num_nozzles=2, num_burners=1), promotes=['*'])
    # p.model.comp.fd_options['form'] = 'complex_step'

    p.setup(check=True)
    p.run_model()

    p.check_partials(compact_print=True)
