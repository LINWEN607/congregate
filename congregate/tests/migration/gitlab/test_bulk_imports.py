import unittest
from pytest import mark

from congregate.migration.gitlab.bulk_imports import BulkImportsClient


@mark.unit_test
class BulkImportsTests(unittest.TestCase):
    def setUp(self):
        self.bulk_imports = BulkImportsClient()

    def sort_paths(self, paths):
        return sorted(paths, key=lambda x: x.count('/'))

    def test_parent_group_exists(self):
        entity_paths = {'one', 'two', 'two/three'}
        full_path = 'one/two'
        self.assertTrue(self.bulk_imports.parent_group_exists(
            full_path, self.sort_paths(entity_paths)))

    def test_parent_group_exists_nest(self):
        entity_paths = {'one', 'one/one', 'two/three'}
        full_path = 'one/one/two'
        self.assertTrue(self.bulk_imports.parent_group_exists(
            full_path, self.sort_paths(entity_paths)))

    def test_parent_group_exists_nest_subgroups(self):
        entity_paths = {'one/one', 'two/three'}
        full_path = 'one/one/two'
        self.assertTrue(self.bulk_imports.parent_group_exists(
            full_path, self.sort_paths(entity_paths)))

    def test_parent_group_doesnt_exist(self):
        entity_paths = {'two', 'two/three'}
        full_path = 'one/two'
        self.assertFalse(self.bulk_imports.parent_group_exists(
            full_path, self.sort_paths(entity_paths)))

    def test_parent_group_doesnt_exist_nest(self):
        entity_paths = {'one/one', 'two/three'}
        full_path = 'one/two/two'
        self.assertFalse(self.bulk_imports.parent_group_exists(
            full_path, self.sort_paths(entity_paths)))

    def test_parent_group_doesnt_exist_nest_subgroups(self):
        entity_paths = {'one/one', 'two/three'}
        full_path = 'one/two/three'
        self.assertFalse(self.bulk_imports.parent_group_exists(
            full_path, self.sort_paths(entity_paths)))
