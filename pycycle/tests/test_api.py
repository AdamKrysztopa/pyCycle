import unittest


class TestApiImports(unittest.TestCase):
    def test_api_imports(self):
        import pycycle.api as api

        self.assertTrue(hasattr(api, 'Cycle'))
        self.assertTrue(hasattr(api, 'MPCycle'))
        self.assertTrue(hasattr(api, 'Nozzle'))
        self.assertTrue(hasattr(api, 'Turbine'))
        self.assertTrue(hasattr(api, 'AXI5'))
        self.assertTrue(hasattr(api, 'LPT2269'))
        self.assertTrue(hasattr(api, 'AIR_FUEL_MIX'))


if __name__ == '__main__':
    unittest.main()
