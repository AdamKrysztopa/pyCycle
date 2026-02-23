from pycycle.unit_utils import STD_DAY, get_unit


def test_get_unit_eng():
    assert get_unit('temperature', 'ENG') == 'degR'
    assert get_unit('pressure', 'ENG') == 'lbf/inch**2'
    assert get_unit('mass_flow', 'ENG') == 'lbm/s'


def test_get_unit_si():
    assert get_unit('temperature', 'SI') == 'degK'
    assert get_unit('pressure', 'SI') == 'Pa'
    assert get_unit('mass_flow', 'SI') == 'kg/s'


def test_std_day_values():
    assert STD_DAY['ENG']['T'] == 518.67
    assert STD_DAY['ENG']['P'] == 14.695951
    assert STD_DAY['SI']['T'] == 288.15
    assert STD_DAY['SI']['P'] == 101325.0
