from unittest import TestCase
from pytest import mark

from congregate.helpers.processes import get_no_of_processes


@mark.unit_test
class ProcessesTests(TestCase):

    def test_get_no_of_processes_default(self):
        self.assertEqual(get_no_of_processes(None), 4)

    def test_get_no_of_processes_cli(self):
        self.assertEqual(get_no_of_processes("8"), 8)
