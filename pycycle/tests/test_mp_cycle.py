import unittest

import networkx as nx

from pycycle.element_base import Element
from pycycle.mp_cycle import Cycle


class DummyElement(Element):
    def setup(self):
        super().setup()

    def pyc_setup_output_ports(self):
        self.Fl_O_data['Fl_O'] = self.Fl_I_data.get('Fl_I', {})


class TestCycle(unittest.TestCase):
    def test_add_subsystem_tracks_elements(self):
        cycle = Cycle()
        cycle.add_subsystem('dummy', DummyElement())
        self.assertEqual(len(cycle._elements), 1)

    def test_pyc_connect_flow_builds_graph(self):
        cycle = Cycle()
        cycle._flow_graph = nx.DiGraph()

        cycle._children = {}
        cycle.add_subsystem('fc', DummyElement())
        cycle.add_subsystem('inlet', DummyElement())

        cycle._flow_graph.add_node('fc', type='element')
        cycle._flow_graph.add_node('inlet', type='element')

        cycle.pyc_connect_flow('fc.Fl_O', 'inlet.Fl_I')

        self.assertIn('fc.Fl_O', cycle._flow_graph)
        self.assertIn('inlet.Fl_I', cycle._flow_graph)


if __name__ == '__main__':
    unittest.main()
