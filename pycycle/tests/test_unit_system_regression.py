import openmdao.api as om
from openmdao.utils.assert_utils import assert_near_equal

import pycycle.api as pyc


class _MiniInletCycle(pyc.Cycle):
    def setup(self):
        self.options['thermo_method'] = 'TABULAR'
        self.options['thermo_data'] = pyc.AIR_JETA_TAB_SPEC
        self.add_subsystem('fc', pyc.FlightConditions())
        self.add_subsystem('inlet', pyc.Inlet())
        self.pyc_connect_flow('fc.Fl_O', 'inlet.Fl_I', connect_w=False)
        super().setup()


def _run(unit_system):
    prob = om.Problem()
    prob.model = _MiniInletCycle(unit_system=unit_system)
    prob.setup()
    prob.set_val('fc.alt', 10000.0, units='ft')
    prob.set_val('fc.MN', 0.8)
    prob.set_val('fc.W', 200.0, units='lbm/s')
    prob.set_val('inlet.ram_recovery', 0.995)
    prob.set_val('inlet.MN', 0.6)
    prob.run_model()
    return prob


def test_eng_si_cycle_equivalence():
    p_eng = _run('ENG')
    p_si = _run('SI')

    fn_eng = float(p_eng.get_val('inlet.F_ram', units='N')[0])
    fn_si = float(p_si.get_val('inlet.F_ram', units='N')[0])
    assert_near_equal(fn_eng, fn_si, tolerance=2e-6)

    pt_eng = float(p_eng.get_val('inlet.Fl_O:tot:P', units='Pa')[0])
    pt_si = float(p_si.get_val('inlet.Fl_O:tot:P', units='Pa')[0])
    assert_near_equal(pt_eng, pt_si, tolerance=2e-6)
