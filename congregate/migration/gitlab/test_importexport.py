import unittest
from migration.gitlab.importexport import ImportExportClient

class ImportExportClientTests(unittest.TestCase):
    def setUp(self):
        self.ie = ImportExportClient()

    def test_strip_namespace_single_slash(self):
        fpn = "Top-level-group/subgroup"
        n = "Top-level-group/subgroup_project"
        actual = self.ie.strip_namespace(fpn, n)
        expected = n
        self.assertEqual(expected, actual)
    
    def test_strip_namespace_multi_slash(self):
        fpn = "Top-level-group/subgroup1"
        n = "subgroup1/subgroup2_project"
        actual = self.ie.strip_namespace(fpn, n)
        expected = "subgroup2_project"
        self.assertEqual(expected, actual)
