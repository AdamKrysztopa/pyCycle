import unittest

from pycycle.maps.axi5 import AXI5
from pycycle.maps.lpt2269 import LPT2269
from pycycle.maps.map_data import normalize_map_data


class TestMapData(unittest.TestCase):
    def test_axi5_shapes_consistent(self):
        expected = (len(AXI5.alphaMap), len(AXI5.NcMap), len(AXI5.RlineMap))
        self.assertEqual(AXI5.WcMap.shape, expected)
        self.assertEqual(AXI5.effMap.shape, expected)
        self.assertEqual(AXI5.PRmap.shape, expected)

    def test_lpt2269_shapes_consistent(self):
        expected = (len(LPT2269.alphaMap), len(LPT2269.NpMap), len(LPT2269.PRmap))
        self.assertEqual(LPT2269.WpMap.shape, expected)
        self.assertEqual(LPT2269.effMap.shape, expected)

    def test_normalize_map_data_aliases(self):
        data = normalize_map_data(AXI5)
        self.assertTrue(hasattr(data, 'NcMap'))
        self.assertTrue(hasattr(data, 'NpMap'))
        self.assertTrue(hasattr(data, 'WcMap'))
        self.assertTrue(hasattr(data, 'WpMap'))

    def test_defaults_present(self):
        self.assertIn('alphaMap', AXI5.defaults)
        self.assertIn('NcMap', AXI5.defaults)
        self.assertIn('RlineMap', AXI5.defaults)
        self.assertIn('alphaMap', LPT2269.defaults)
        self.assertIn('NpMap', LPT2269.defaults)
        self.assertIn('PRmap', LPT2269.defaults)


if __name__ == '__main__':
    unittest.main()
