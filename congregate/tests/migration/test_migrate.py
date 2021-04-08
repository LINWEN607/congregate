import base64
import unittest
from pytest import mark
from congregate.migration.migrate import MigrateClient

@mark.unit_test
class MigrateClientTests(unittest.TestCase):
    def setUp(self):
        self.mc = MigrateClient()
        super().__init__()
