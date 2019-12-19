import unittest
import mock
from congregate.helpers.migrate_utils import get_failed_update_from_results, get_staged_projects_without_failed_update
from congregate.helpers.configuration_validator import ConfigurationValidator
from congregate.migration.gitlab.api.groups import GroupsApi


class MigrateTests(unittest.TestCase):
    def setUp(self):
        self.staged_projects = [
            {
                "archived": False,
                "builds_access_level": "enabled",
                "default_branch": "master",
                "description": "",
                "http_url_to_repo": "https://dictionary.githost.io/dictionary-web/darci.git",
                "id": 132,
                "issues_access_level": "enabled",
                "members": [],
                "merge_requests_access_level": "enabled",
                "name": "darci1",
                "namespace": "dictionary-web",
                "project_type": "group",
                "repository_access_level": "enabled",
                "shared_runners_enabled": False,
                "snippets_access_level": "disabled",
                "visibility": "private",
                "wiki_access_level": "enabled"
            },
            {
                "archived": False,
                "builds_access_level": "enabled",
                "default_branch": "master",
                "description": "",
                "http_url_to_repo": "https://dictionary.githost.io/dictionary-web/darci.git",
                "id": 133,
                "issues_access_level": "enabled",
                "members": [],
                "merge_requests_access_level": "enabled",
                "name": "darci2",
                "namespace": "dictionary-web",
                "project_type": "group",
                "repository_access_level": "enabled",
                "shared_runners_enabled": False,
                "snippets_access_level": "disabled",
                "visibility": "private",
                "wiki_access_level": "enabled"
            },
            {
                "archived": True,
                "builds_access_level": "enabled",
                "default_branch": "master",
                "description": "",
                "http_url_to_repo": "https://dictionary.githost.io/dictionary-web/darci.git",
                "id": 134,
                "issues_access_level": "enabled",
                "members": [],
                "merge_requests_access_level": "enabled",
                "name": "darci3",
                "namespace": "dictionary-web",
                "project_type": "group",
                "repository_access_level": "enabled",
                "shared_runners_enabled": False,
                "snippets_access_level": "disabled",
                "visibility": "private",
                "wiki_access_level": "enabled"
            }
        ]

    def test_get_failed_update_from_results_updated_false(self):
        results = [{"exported": True, "updated": False, "filename": "DaRcI1"}]
        failed_results = get_failed_update_from_results(results)
        expected = ["darci1"]
        self.assertListEqual(failed_results, expected)

    def test_get_failed_update_from_results_updated_all_false(self):
        results = [{"exported": True, "updated": False, "filename": "DaRcI1"},
                   {"exported": True, "updated": False, "filename": "DaRcI2"},
                   {"exported": True, "updated": False, "filename": "DaRcI3"}]
        failed_results = get_failed_update_from_results(results)
        expected = ["darci1", "darci2", "darci3"]
        self.assertListEqual(failed_results, expected)

    def test_get_failed_update_from_results_updated_true(self):
        results = [{"exported": True, "updated": True, "filename": "DaRcI1"}]
        failed_results = get_failed_update_from_results(results)
        expected = []
        self.assertListEqual(failed_results, expected)

    @mock.patch("congregate.helpers.base_module.ConfigurationValidator.parent_id", new_callable=mock.PropertyMock)
    @mock.patch.object(GroupsApi, "get_group")
    @mock.patch.object(ConfigurationValidator, "validate_parent_group_id")
    def test_get_staged_projects_without_failed_update_with_failure(self, cv, ga, pi):
        pi.return_value = 1
        ga.return_value = self.ThingWithJson({"path": "SOME_RANDOM_PATH"})
        cv.return_value = True
        expected = [
            {
                "archived": False,
                "builds_access_level": "enabled",
                "default_branch": "master",
                "description": "",
                "http_url_to_repo": "https://dictionary.githost.io/dictionary-web/darci.git",
                "id": 133,
                "issues_access_level": "enabled",
                "members": [],
                "merge_requests_access_level": "enabled",
                "name": "darci2",
                "namespace": "dictionary-web",
                "project_type": "group",
                "repository_access_level": "enabled",
                "shared_runners_enabled": False,
                "snippets_access_level": "disabled",
                "visibility": "private",
                "wiki_access_level": "enabled"
            },
            {
                "archived": True,
                "builds_access_level": "enabled",
                "default_branch": "master",
                "description": "",
                "http_url_to_repo": "https://dictionary.githost.io/dictionary-web/darci.git",
                "id": 134,
                "issues_access_level": "enabled",
                "members": [],
                "merge_requests_access_level": "enabled",
                "name": "darci3",
                "namespace": "dictionary-web",
                "project_type": "group",
                "repository_access_level": "enabled",
                "shared_runners_enabled": False,
                "snippets_access_level": "disabled",
                "visibility": "private",
                "wiki_access_level": "enabled"
            }
        ]
        failed_results = ['some_random_path/dictionary-web_darci1.tar.gz']
        filtered_staged = get_staged_projects_without_failed_update(self.staged_projects, failed_results)
        self.assertListEqual(filtered_staged, expected)
        print(filtered_staged)

    @mock.patch("congregate.helpers.base_module.ConfigurationValidator.parent_id", new_callable=mock.PropertyMock)
    @mock.patch.object(GroupsApi, "get_group")
    @mock.patch.object(ConfigurationValidator, "validate_parent_group_id")
    def test_get_staged_projects_without_failed_update_with_no_failure_leaves_unchanged(self, cv, ga, pi):
        ga.return_value = self.ThingWithJson({"path": "SOME_RANDOM_PATH"})
        cv.return_value = True
        pi.return_value = 1
        failed_results = []
        filtered_staged = get_staged_projects_without_failed_update(self.staged_projects, failed_results)
        self.assertListEqual(filtered_staged, self.staged_projects)

    class ThingWithJson:
        def __init__(self, jsons):
            self._json = jsons

        def json(self):
            return self._json

    @mock.patch("congregate.helpers.base_module.ConfigurationValidator.parent_id", new_callable=mock.PropertyMock)
    @mock.patch.object(GroupsApi, "get_group")
    @mock.patch.object(ConfigurationValidator, "validate_parent_group_id")
    def test_get_staged_projects_without_failed_update_with_no_all_fail_returns_empty_group_project(self, cv, ga, pi):
        pi.return_value = 1
        ga.return_value = self.ThingWithJson({"path": "SOME_RANDOM_PATH"})
        cv.return_value = True
        failed_results = ['some_random_path/dictionary-web_darci1.tar.gz',
                          'some_random_path/dictionary-web_darci2.tar.gz',
                          'some_random_path/dictionary-web_darci3.tar.gz']
        filtered_staged = get_staged_projects_without_failed_update(self.staged_projects, failed_results)
        self.assertListEqual(filtered_staged, [])

    @mock.patch("congregate.helpers.base_module.ConfigurationValidator.parent_id", new_callable=mock.PropertyMock)
    @mock.patch.object(GroupsApi, "get_group")
    @mock.patch.object(ConfigurationValidator, "validate_parent_group_id")
    def test_get_staged_projects_without_failed_update_with_no_all_fail_returns_empty_user_project(self, cv, ga, pi):
        pi.return_value = None
        ga.return_value = self.ThingWithJson({"path": "SOME_RANDOM_PATH"})
        cv.return_value = True
        failed_results = ['dictionary-web_darci1.tar.gz',
                          'dictionary-web_darci2.tar.gz',
                          'dictionary-web_darci3.tar.gz']
        filtered_staged = get_staged_projects_without_failed_update(self.staged_projects, failed_results)
        self.assertListEqual(filtered_staged, [])
