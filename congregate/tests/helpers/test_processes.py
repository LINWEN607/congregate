from unittest import TestCase
from unittest.mock import patch, PropertyMock
from pytest import mark

from congregate.helpers.processes import get_no_of_processes


@mark.unit_test
class ProcessesTests(TestCase):

    @patch("congregate.helpers.conf.Config.processes", new_callable=PropertyMock)
    def test_get_no_of_processes_default(self, mock_proc):
        mock_proc.return_value = None
        self.assertEqual(get_no_of_processes(None), 4)

    @patch("congregate.helpers.conf.Config.processes", new_callable=PropertyMock)
    def test_get_no_of_processes_config(self, mock_proc):
        mock_proc.return_value = 6
        self.assertEqual(get_no_of_processes(None), 6)

    @patch("congregate.helpers.conf.Config.processes", new_callable=PropertyMock)
    def test_get_no_of_processes_cli(self, mock_proc):
        mock_proc.return_value = 6
        self.assertEqual(get_no_of_processes("8"), 8)
