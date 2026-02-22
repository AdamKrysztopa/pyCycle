import unittest

from pycycle.element_base import Element


class DummyElement(Element):
    def setup(self):
        super().setup()

    def pyc_setup_output_ports(self):
        self.Fl_O_data['Fl_O'] = self.Fl_I_data.get('Fl_I', {'dummy': True})


class TestElement(unittest.TestCase):
    def test_flow_data_init(self):
        elem = DummyElement()
        self.assertEqual(elem.Fl_I_data, {})
        self.assertEqual(elem.Fl_O_data, {})

    def test_copy_flow_from_string(self):
        elem = DummyElement()
        elem.Fl_I_data['Fl_I'] = {'key': 'value'}
        elem.copy_flow('Fl_I', 'Fl_O')
        self.assertEqual(elem.Fl_O_data['Fl_O'], {'key': 'value'})

    def test_copy_flow_invalid_type(self):
        elem = DummyElement()
        with self.assertRaises(ValueError):
            elem.copy_flow(123, 'Fl_O')

    def test_init_output_flow(self):
        elem = DummyElement()
        elem.init_output_flow('Fl_O', {'foo': 'bar'})
        self.assertEqual(elem.Fl_O_data['Fl_O'], {'foo': 'bar'})


if __name__ == '__main__':
    unittest.main()
