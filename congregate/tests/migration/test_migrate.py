import unittest
from unittest.mock import patch
from pytest import mark
from congregate.migration.migrate import MigrateClient
# from congregate.tests.mockapi.bitbucket.repos import MockReposApi
from congregate.migration.gitlab.external_import import ImportClient
from congregate.tests.mockapi.gitlab.projects import MockProjectsApi


@mark.unit_test
class MigrateClientTests(unittest.TestCase):
    def setUp(self):
        self.mc = MigrateClient()
        self.mock_projects = MockProjectsApi()
        super().__init__()

    @patch.object(ImportClient, "trigger_import_from_bb_server")
    def test_bb_failure_info(self, tifmms):
        tifmms.side_effect = Exception("This came from raise_error!")
        projects = self.mock_projects.get_all_projects()
        project = projects[0]
        result = self.mc.import_bitbucket_project(project)
        result = dict(result)
        keys = result.keys()
        self.assertIn(
            "Failed to trigger import with error: This came from raise_error!",
            result.get(list(keys)[0]).get("response").get("error")
        )

    def raise_error(self):
        raise Exception("This came from raise_error!")
