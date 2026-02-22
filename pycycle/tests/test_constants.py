import unittest

from pycycle import constants


class TestConstants(unittest.TestCase):
    def test_air_jeta_tab_spec_loaded(self):
        spec = constants.AIR_JETA_TAB_SPEC
        self.assertTrue(isinstance(spec, dict))
        self.assertIn('FAR', spec)

    def test_composition_dicts(self):
        self.assertIn('O2', constants.CEA_AIR_COMPOSITION)
        self.assertIn('N2', constants.CEA_AIR_COMPOSITION)


if __name__ == '__main__':
    unittest.main()
