import openmdao.api as om

from pycycle.elements.US1976 import USatm1976Comp
from pycycle.unit_utils import get_unit


class DeltaTs(om.ExplicitComponent):
    """Computes temperature based on delta from atmospheric"""
    def initialize(self):
        self.options.declare('unit_system', default='ENG', values=('ENG', 'SI'))

    def setup(self):
        unit_system = self.options['unit_system']

        # inputs
        self.add_input('Ts_in', val=500.0, units=get_unit('temperature', unit_system), desc='Temperature from atmospheric model')
        self.add_input('dTs', val=0.0, units=get_unit('temperature', unit_system), desc='Delta from standard day temperature')

        self.add_output('Ts', shape=1, units=get_unit('temperature', unit_system), desc='Temperature with delta')

        self.declare_partials('Ts', ['Ts_in', 'dTs'], val=1.0)

    def compute(self, inputs, outputs):
        outputs['Ts'] = inputs['Ts_in'] + inputs['dTs']

    def compute_partials(self, inputs, partials):
        pass


class Ambient(om.Group):
    """Determines pressure, temperature and density base on altitude from an input standard atmosphere table"""
    def initialize(self):
        self.options.declare('unit_system', default='ENG', values=('ENG', 'SI'))

    def setup(self):
        self.add_subsystem('readAtmTable', USatm1976Comp(), promotes=('alt', 'Ps', 'rhos'))

        self.add_subsystem('dTs', DeltaTs(unit_system=self.options['unit_system']), promotes=('dTs', 'Ts'))
        self.connect('readAtmTable.Ts', 'dTs.Ts_in')

        # self.set_order(['readAtmTable','dTs'])


if __name__ == "__main__":

    from pycycle.elements.US1976 import USatm1976Data

    p1 = om.Problem()
    p1.root = Ambient()

    var = (('alt', 30000.0),)
    p1.root.add("idv", om.IndepVarComp(var), promotes=["*"])

    p1.setup()

    p1.run()

    # p1.check_partials()
    # print('Ts: ', p1['Ts'])
    # print('Ps: ', p1['Ps'])
    # print('rhos: ', p1['rhos'])

    T = USatm1976Data.T
    P = USatm1976Data.P
    rho = USatm1976Data.rho

    for i, alt in enumerate(USatm1976Data.alt):
        p1['alt'] = alt
        p1.run()
        print(10*"=")
        print("Ts", p1['Ts'], T[i])
        print("Ps", p1['Ps'], P[i])
        print("rho", p1['rhos'], rho[i])

    p1.model.list_states()
