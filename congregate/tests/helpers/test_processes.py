from unittest import TestCase
from pytest import mark

from congregate.helpers.processes import MultiProcessing


@mark.unit_test
class ProcessesTests(TestCase):
    def setUp(self):
        self.multi = MultiProcessing()

    def test_get_no_of_processes_default(self):
        self.assertEqual(self.multi.get_no_of_processes(None), 4)

    def test_get_no_of_processes_cli(self):
        self.assertEqual(self.multi.get_no_of_processes("8"), 8)
