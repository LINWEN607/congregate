import unittest
from pytest import mark
import responses
from unittest.mock import patch, PropertyMock

from gitlab_ps_utils.api import GitLabApi
import congregate.helpers.migrate_utils as mutils
from congregate.tests.mockapi.gitlab.users import MockUsersApi
from congregate.tests.mockapi.gitlab.groups import MockGroupsApi
from congregate.tests.mockapi.gitlab.projects import MockProjectsApi
from congregate.helpers.configuration_validator import ConfigurationValidator
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.tests.helpers.mock_data.results import MockProjectResults


@mark.unit_test
class MigrateTests(unittest.TestCase):
    def setUp(self):
        self.mock_users = MockUsersApi()
        self.mock_groups = MockGroupsApi()
        self.mock_projects = MockProjectsApi()

    class ThingWithJson:
        def __init__(self, jsons):
            self._json = jsons

        def json(self):
            return self._json

    def test_get_failed_export_from_results_exported_false(self):
        results = [{"darci1": False}, {"darci2": True}, {"darci3": False}]
        failed_results = mutils.get_failed_export_from_results(results)
        expected = ["darci1", "darci3"]
        self.assertListEqual(failed_results, expected)

    def test_get_failed_export_from_results_exported_all_false(self):
        results = [{"darci1": False}, {"darci2": False}, {"darci3": False}]
        failed_results = mutils.get_failed_export_from_results(results)
        expected = ["darci1", "darci2", "darci3"]
        self.assertListEqual(failed_results, expected)

    def test_get_failed_export_from_results_exported_true(self):
        results = [{"darci1": True}, {"darci2": True}]
        failed_results = mutils.get_failed_export_from_results(results)
        expected = []
        self.assertListEqual(failed_results, expected)

    @patch("congregate.helpers.base_class.ConfigurationValidator.dstn_parent_id",
           new_callable=PropertyMock)
    @patch.object(GroupsApi, "get_group")
    @patch.object(ConfigurationValidator, "validate_dstn_parent_group_id")
    def test_get_staged_projects_without_failed_export_with_failure(
            self, cv, ga, pi):
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
                "wiki_access_level": "enabled",
                "forking_access_level": "enabled",
                "pages_access_level": "private"
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
                "wiki_access_level": "enabled",
                "forking_access_level": "enabled",
                "pages_access_level": "private"
            }
        ]
        failed_results = ['dictionary-web_darci1.tar.gz']
        filtered_staged = mutils.get_staged_projects_without_failed_export(
            self.mock_projects.get_staged_projects(), failed_results)
        self.assertListEqual(filtered_staged, expected)
        print(filtered_staged)

    @patch("congregate.helpers.base_class.ConfigurationValidator.dstn_parent_id",
           new_callable=PropertyMock)
    @patch.object(GroupsApi, "get_group")
    @patch.object(ConfigurationValidator, "validate_dstn_parent_group_id")
    def test_get_staged_projects_without_failed_export_with_no_failure_leaves_unchanged(
            self, cv, ga, pi):
        ga.return_value = self.ThingWithJson({"path": "SOME_RANDOM_PATH"})
        cv.return_value = True
        pi.return_value = 1
        failed_results = []
        filtered_staged = mutils.get_staged_projects_without_failed_export(
            self.mock_projects.get_staged_projects(), failed_results)
        self.assertListEqual(
            filtered_staged, self.mock_projects.get_staged_projects())

    @patch("congregate.helpers.base_class.ConfigurationValidator.dstn_parent_id",
           new_callable=PropertyMock)
    @patch.object(GroupsApi, "get_group")
    @patch.object(ConfigurationValidator, "validate_dstn_parent_group_id")
    def test_get_staged_projects_without_failed_export_with_no_all_fail_returns_empty_group_project(
            self, cv, ga, pi):
        pi.return_value = 1
        ga.return_value = self.ThingWithJson({"path": "SOME_RANDOM_PATH"})
        cv.return_value = True
        failed_results = ['dictionary-web_darci1.tar.gz',
                          'dictionary-web_darci2.tar.gz',
                          'dictionary-web_darci3.tar.gz']
        filtered_staged = mutils.get_staged_projects_without_failed_export(
            self.mock_projects.get_staged_projects(), failed_results)
        self.assertListEqual(filtered_staged, [])

    @patch("congregate.helpers.base_class.ConfigurationValidator.dstn_parent_id",
           new_callable=PropertyMock)
    @patch.object(GroupsApi, "get_group")
    @patch.object(ConfigurationValidator, "validate_dstn_parent_group_id")
    def test_get_staged_projects_without_failed_export_with_no_all_fail_returns_empty_user_project(
            self, cv, ga, pi):
        pi.return_value = None
        ga.return_value = self.ThingWithJson({"path": "SOME_RANDOM_PATH"})
        cv.return_value = True
        failed_results = ['dictionary-web_darci1.tar.gz',
                          'dictionary-web_darci2.tar.gz',
                          'dictionary-web_darci3.tar.gz']
        filtered_staged = mutils.get_staged_projects_without_failed_export(
            self.mock_projects.get_staged_projects(), failed_results)
        self.assertListEqual(filtered_staged, [])

    @patch("congregate.helpers.base_class.ConfigurationValidator.dstn_parent_id",
           new_callable=PropertyMock)
    @patch.object(GroupsApi, "get_group")
    @patch.object(ConfigurationValidator, "validate_dstn_parent_group_id")
    def test_get_staged_groups_without_failed_export_with_failure(
            self, cv, ga, pi):
        pi.return_value = 1
        ga.return_value = self.ThingWithJson({"path": "SOME_RANDOM_PATH"})
        cv.return_value = True
        expected = [
            {
                "lfs_enabled": True,
                "request_access_enabled": False,
                "project_creation_level": "developer",
                "subgroup_creation_level": "owner",
                "path": "pmm-demo-2",
                "id": 129,
                "parent_id": 814,
                "share_with_group_lock": False,
                "description": "PMM Demos",
                "two_factor_grace_period": 48,
                "visibility": "public",
                "members": [],
                "name": "pmm-demo-2",
                "require_two_factor_authentication": False,
                "full_path": "pmm-demo-2"
            },
            {
                "lfs_enabled": True,
                "request_access_enabled": False,
                "project_creation_level": "developer",
                "subgroup_creation_level": "owner",
                "path": "pmm-demo-3",
                "id": 129,
                "parent_id": 814,
                "share_with_group_lock": False,
                "description": "PMM Demos",
                "two_factor_grace_period": 48,
                "visibility": "public",
                "members": [],
                "name": "pmm-demo-3",
                "require_two_factor_authentication": False,
                "full_path": "pmm-demo-3"
            }
        ]
        failed_results = ['pmm-demo-1.tar.gz']
        filtered_staged = mutils.get_staged_groups_without_failed_export(
            self.mock_groups.get_staged_groups(), failed_results)
        self.assertListEqual(filtered_staged, expected)
        print(filtered_staged)

    @patch("congregate.helpers.base_class.ConfigurationValidator.dstn_parent_id",
           new_callable=PropertyMock)
    @patch.object(GroupsApi, "get_group")
    @patch.object(ConfigurationValidator, "validate_dstn_parent_group_id")
    def test_get_staged_groups_without_failed_export_with_no_failure_leaves_unchanged(
            self, cv, ga, pi):
        ga.return_value = self.ThingWithJson({"path": "SOME_RANDOM_PATH"})
        cv.return_value = True
        pi.return_value = 1
        failed_results = []
        filtered_staged = mutils.get_staged_groups_without_failed_export(
            self.mock_groups.get_staged_groups(), failed_results)
        self.assertListEqual(
            filtered_staged, self.mock_groups.get_staged_groups())

    @patch("congregate.helpers.base_class.ConfigurationValidator.dstn_parent_id",
           new_callable=PropertyMock)
    @patch.object(GroupsApi, "get_group")
    @patch.object(ConfigurationValidator, "validate_dstn_parent_group_id")
    def test_get_staged_groups_without_failed_export_with_no_all_fail_returns_empty_group(
            self, cv, ga, pi):
        pi.return_value = 1
        ga.return_value = self.ThingWithJson({"path": "SOME_RANDOM_PATH"})
        cv.return_value = True
        failed_results = ['pmm-demo-1.tar.gz',
                          'pmm-demo-2.tar.gz',
                          'pmm-demo-3.tar.gz']
        filtered_staged = mutils.get_staged_groups_without_failed_export(
            self.mock_groups.get_staged_groups(), failed_results)
        self.assertListEqual(filtered_staged, [])

    def test_is_user_project_false(self):
        self.assertFalse(mutils.is_user_project(
            self.mock_projects.get_staged_group_project()))

    def test_is_user_project_true(self):
        self.assertTrue(mutils.is_user_project(
            self.mock_projects.get_staged_user_project()))

    def test_get_export_filename_from_namespace_and_name(self):
        self.assertEqual(mutils.get_export_filename_from_namespace_and_name(
            "Test-Group/Test-SubGroup", "Test-Project"), "test-group_test-subgroup_test-project.tar.gz")
        self.assertEqual(mutils.get_export_filename_from_namespace_and_name(
            "Test-Group/Test-SubGroup"), "test-group_test-subgroup.tar.gz")

    @patch.object(ConfigurationValidator,
                  "dstn_parent_group_path", new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, "dstn_parent_id",
                  new_callable=PropertyMock)
    def test_get_project_dest_namespace(self, dstn_parent_id, dstn_parent_group_path):
        dstn_parent_id.return_value = 4
        dstn_parent_group_path.return_value = "test"
        self.assertEqual(mutils.get_project_dest_namespace(
            self.mock_projects.get_staged_group_project()), "test/pmm-demo")
        dstn_parent_id.return_value = None
        self.assertEqual(mutils.get_project_dest_namespace(
            self.mock_projects.get_staged_group_project()), "pmm-demo")
        dstn_parent_id.return_value = 1
        self.assertEqual(mutils.get_project_dest_namespace(
            self.mock_projects.get_staged_user_project()), "pmm-demo")

    @patch.object(ConfigurationValidator,
                  "dstn_parent_group_path", new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, "dstn_parent_id",
                  new_callable=PropertyMock)
    def test_get_project_dest_namespace_with_src_group(self, dstn_parent_id, dstn_parent_group_path):
        dstn_parent_id.return_value = 4
        dstn_parent_group_path.return_value = "test"
        self.assertEqual(mutils.get_project_dest_namespace(
            self.mock_projects.get_staged_nested_group_project()), "test/marketing/pmm/pmm-demo")
        dstn_parent_id.return_value = None
        self.assertEqual(mutils.get_project_dest_namespace(
            self.mock_projects.get_staged_nested_group_project()), "marketing/pmm/pmm-demo")
        dstn_parent_id.return_value = 1
        self.assertEqual(mutils.get_project_dest_namespace(
            self.mock_projects.get_staged_user_project()), "pmm-demo")

    @patch.object(ConfigurationValidator,
                  "dstn_parent_group_path", new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, "dstn_parent_id",
                  new_callable=PropertyMock)
    def test_get_project_dest_namespace_with_same_subgroup(self, dstn_parent_id, dstn_parent_group_path):
        dstn_parent_id.return_value = 4
        dstn_parent_group_path.return_value = "test/test"
        self.assertEqual(mutils.get_project_dest_namespace(
            self.mock_projects.get_staged_double_nested_group_project()), "test/test/marketing/pmm/pmm/pmm-demo")
        dstn_parent_id.return_value = None
        self.assertEqual(mutils.get_project_dest_namespace(
            self.mock_projects.get_staged_double_nested_group_project()), "marketing/pmm/pmm/pmm-demo")

    # pylint: disable=no-member
    @responses.activate
    # pylint: enable=no-member
    @patch.object(GitLabApi, "generate_v4_request_url")
    @patch.object(ConfigurationValidator, "import_user_id",
                  new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, "destination_host",
                  new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, "destination_token",
                  new_callable=PropertyMock)
    def test_get_user_project_namespace_dot_com(
            self, token, host, user_id, url):
        token.return_value = "abc"
        host.return_value = "https://gitlab.com"
        user_id.return_value = 1
        url_value = "https://gitlab.com/api/v4/users/5"
        url.return_value = url_value
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                      json=self.mock_users.get_dummy_user(), status=200)
        # pylint: enable=no-member
        self.assertEqual(mutils.get_user_project_namespace(
            self.mock_projects.get_staged_user_project()), "jdoe")

    # pylint: disable=no-member
    @responses.activate
    # pylint: enable=no-member
    @patch.object(GitLabApi, "generate_v4_request_url")
    @patch.object(ConfigurationValidator, "import_user_id",
                  new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, "destination_host",
                  new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, "destination_token",
                  new_callable=PropertyMock)
    def test_get_user_project_namespace_root(self, token, host, user_id, url):
        token.return_value = "abc"
        host.return_value = "https://githost.io"
        user_id.return_value = 1
        url_value = "https://gitlab.com/api/v4/users/5"
        url.return_value = url_value
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                      json=self.mock_users.get_dummy_user(), status=200)
        # pylint: enable=no-member
        self.assertEqual(mutils.get_user_project_namespace(
            self.mock_projects.get_staged_root_project()), "jdoe")

    @patch.object(ConfigurationValidator, "import_user_id",
                  new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, "destination_host",
                  new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, "destination_token",
                  new_callable=PropertyMock)
    def test_get_user_project_namespace_non_root_no_user(
            self, token, host, user_id):
        token.return_value = "abc"
        host.return_value = "https://githost.io"
        user_id.return_value = 1
        self.assertEqual(mutils.get_user_project_namespace(
            self.mock_projects.get_staged_user_project()), "pmm-demo")

    @patch.object(ConfigurationValidator, "import_user_id",
                  new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, "destination_host",
                  new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, "destination_token",
                  new_callable=PropertyMock)
    @patch("congregate.helpers.migrate_utils.find_user_by_email_comparison_without_id")
    def test_get_user_project_namespace_non_root(
            self, user, token, host, user_id):
        user.return_value = self.mock_users.get_user_gen()
        token.return_value = "abc"
        host.return_value = "https://githost.io"
        user_id.return_value = 1
        self.assertEqual(mutils.get_user_project_namespace(
            self.mock_projects.get_project()), "jdoe")

    def test_get_project_filename(self):
        self.assertEqual(mutils.get_project_filename(
            self.mock_projects.get_staged_user_project()), "pmm-demo_spring-app-secure-2.tar.gz")

    def test_get_project_filename_no_name(self):
        staged_project = {
            "archived": False,
            "builds_access_level": "enabled",
            "default_branch": "master",
            "description": "",
            "http_url_to_repo": "https://dictionary.githost.io/dictionary-web/darci.git",
            "id": 132,
            "issues_access_level": "enabled",
            "members": [],
            "merge_requests_access_level": "enabled",
            "name": None,
            "namespace": "dictionary-web",
            "project_type": None,
            "repository_access_level": "enabled",
            "shared_runners_enabled": False,
            "snippets_access_level": "disabled",
            "visibility": "private",
            "wiki_access_level": "enabled",
            "forking_access_level": "enabled",
            "pages_access_level": "private"
        }
        self.assertEqual(mutils.get_project_filename(staged_project), "")

    def test_get_project_filename_no_namespace(self):
        staged_project = {
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
            "namespace": None,
            "project_type": None,
            "repository_access_level": "enabled",
            "shared_runners_enabled": False,
            "snippets_access_level": "disabled",
            "visibility": "private",
            "wiki_access_level": "enabled",
            "forking_access_level": "enabled",
            "pages_access_level": "private"
        }
        self.assertEqual(mutils.get_project_filename(staged_project), "")

    # pylint: disable=no-member
    @responses.activate
    # pylint: enable=no-member
    @patch.object(GitLabApi, "generate_v4_request_url")
    @patch.object(ConfigurationValidator, "import_user_id",
                  new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, "destination_host",
                  new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, "destination_token",
                  new_callable=PropertyMock)
    @patch.object(ConfigurationValidator,
                  "dstn_parent_group_path", new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, "dstn_parent_id",
                  new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, "src_parent_group_path",
                  new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, "src_parent_id",
                  new_callable=PropertyMock)
    def test_get_dst_path_with_namespace_with_parent_id(
            self, src_parent_id, src_parent_group_path, dstn_parent_id, dstn_parent_group_path, token, host, user_id, url):
        src_parent_id.return_value = None
        src_parent_group_path.return_value = None
        dstn_parent_id.return_value = 1
        dstn_parent_group_path.return_value = "test-group"
        token.return_value = "abc"
        host.return_value = "https://gitlab.com"
        user_id.return_value = 5
        url_value = "https://gitlab.com/api/v4/users/5"
        url.return_value = url_value
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                      json=self.mock_users.get_dummy_user(), status=200)
        # pylint: enable=no-member
        self.assertEqual(mutils.get_dst_path_with_namespace(
            self.mock_projects.get_staged_group_project()), "test-group/pmm-demo/spring-app-secure-2")
        self.assertEqual(mutils.get_dst_path_with_namespace(
            self.mock_projects.get_staged_user_project()), "jdoe/spring-app-secure-2")

    # pylint: disable=no-member
    @responses.activate
    # pylint: enable=no-member
    @patch.object(GitLabApi, "generate_v4_request_url")
    @patch.object(ConfigurationValidator, "import_user_id",
                  new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, "destination_host",
                  new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, "destination_token",
                  new_callable=PropertyMock)
    @patch.object(ConfigurationValidator,
                  "dstn_parent_group_path", new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, "dstn_parent_id",
                  new_callable=PropertyMock)
    def test_get_dst_path_with_namespace_with_parent_id_root(
            self, parent_id, dstn_parent_group_path, token, host, user_id, url):
        parent_id.return_value = 1
        dstn_parent_group_path.return_value = "test-group"
        token.return_value = "abc"
        host.return_value = "https://gitlab.com"
        user_id.return_value = 5
        url_value = "https://gitlab.com/api/v4/users/5"
        url.return_value = url_value
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                      json=self.mock_users.get_current_user(), status=200)
        # pylint: enable=no-member
        self.assertEqual(mutils.get_dst_path_with_namespace(
            self.mock_projects.get_staged_root_project()), "root/spring-app-secure-2")

    # pylint: disable=no-member
    @responses.activate
    # pylint: enable=no-member
    @patch.object(GitLabApi, "generate_v4_request_url")
    @patch.object(ConfigurationValidator, "import_user_id",
                  new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, "destination_host",
                  new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, "destination_token",
                  new_callable=PropertyMock)
    @patch.object(ConfigurationValidator,
                  "dstn_parent_group_path", new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, "dstn_parent_id",
                  new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, "src_parent_group_path",
                  new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, "src_parent_id",
                  new_callable=PropertyMock)
    def test_get_dst_path_with_namespace_without_parent_id(
            self, src_parent_id, src_parent_group_path, dstn_parent_id, dstn_parent_group_path, token, host, user_id, url):
        src_parent_id.return_value = None
        src_parent_group_path.return_value = None
        dstn_parent_id.return_value = None
        dstn_parent_group_path.return_value = None
        token.return_value = "abc"
        host.return_value = "https://gitlab.com"
        user_id.return_value = 5
        url_value = "https://gitlab.com/api/v4/users/5"
        url.return_value = url_value
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                      json=self.mock_users.get_dummy_user(), status=200)
        # pylint: enable=no-member
        self.assertEqual(mutils.get_dst_path_with_namespace(
            self.mock_projects.get_staged_group_project()), "pmm-demo/spring-app-secure-2")
        self.assertEqual(mutils.get_dst_path_with_namespace(
            self.mock_projects.get_staged_user_project()), "jdoe/spring-app-secure-2")

    # pylint: disable=no-member
    @responses.activate
    # pylint: enable=no-member
    @patch.object(GitLabApi, "generate_v4_request_url")
    @patch.object(ConfigurationValidator, "import_user_id",
                  new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, "destination_host",
                  new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, "destination_token",
                  new_callable=PropertyMock)
    @patch.object(ConfigurationValidator,
                  "dstn_parent_group_path", new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, "dstn_parent_id",
                  new_callable=PropertyMock)
    def test_get_dst_path_with_namespace_without_parent_id_root(
            self, parent_id, dstn_parent_group_path, token, host, user_id, url):
        parent_id.return_value = None
        dstn_parent_group_path.return_value = None
        token.return_value = "abc"
        host.return_value = "https://gitlab.com"
        user_id.return_value = 5
        url_value = "https://gitlab.com/api/v4/users/5"
        url.return_value = url_value
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                      json=self.mock_users.get_current_user(), status=200)
        # pylint: enable=no-member
        self.assertEqual(mutils.get_dst_path_with_namespace(
            self.mock_projects.get_staged_root_project()), "root/spring-app-secure-2")

    @patch.object(ConfigurationValidator, "dstn_parent_id",
                  new_callable=PropertyMock)
    @patch.object(ConfigurationValidator,
                  "dstn_parent_group_path", new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, "src_parent_group_path",
                  new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, "src_parent_id",
                  new_callable=PropertyMock)
    def test_get_full_path_with_parent_namespace_with_parent(
            self, src_parent_id, src_parent_group_path, dstn_parent_group_path, dstn_parent_id):
        src_parent_id.return_value = None
        src_parent_group_path.return_value = None
        dstn_parent_group_path.return_value = "test-parent-group-path"
        dstn_parent_id.return_value = 1
        self.assertEqual(mutils.get_full_path_with_parent_namespace(
            "test-path"), "test-parent-group-path/test-path")

    @patch.object(ConfigurationValidator, "dstn_parent_id",
                  new_callable=PropertyMock)
    @patch.object(ConfigurationValidator,
                  "dstn_parent_group_path", new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, "src_parent_group_path",
                  new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, "src_parent_id",
                  new_callable=PropertyMock)
    def test_get_full_path_with_parent_namespace(
            self, src_parent_id, src_parent_group_path, dstn_parent_group_path, parent_id):
        src_parent_id.return_value = None
        src_parent_group_path.return_value = None
        dstn_parent_group_path.return_value = ""
        parent_id.return_value = ""
        self.assertEqual(mutils.get_full_path_with_parent_namespace(
            "test-path"), "test-path")

    @patch.object(ConfigurationValidator, "dstn_parent_id",
                  new_callable=PropertyMock)
    @patch.object(ConfigurationValidator,
                  "dstn_parent_group_path", new_callable=PropertyMock)
    def test_get_full_path_with_parent_namespace_with_parent_and_src(
            self, dstn_parent_group_path, dstn_parent_id):
        dstn_parent_group_path.return_value = "test-parent-group-path"
        dstn_parent_id.return_value = 1
        self.assertEqual(mutils.get_full_path_with_parent_namespace(
            "groupA/groupB"), "test-parent-group-path/groupA/groupB")

    def test_get_results_export_mix(self):
        results = [
            {"export1": True},
            {"export2": False},
            {"export3": True}
        ]
        self.assertEqual(mutils.get_results(results), {
                         "Total": 3, "Successful": 2})

    def test_get_results_export_happy(self):
        results = [
            {"export1": True},
            {"export2": True},
            {"export3": True}
        ]
        self.assertEqual(mutils.get_results(results), {
                         "Total": 3, "Successful": 3})

    def test_get_results_export_unhappy(self):
        results = [
            {"export1": False},
            {"export2": False},
            {"export3": False}
        ]
        self.assertEqual(mutils.get_results(results), {
                         "Total": 3, "Successful": 0})

    def test_get_results_import_mix(self):
        results = [
            {"import1": {"key": "value"}},
            {"import2": False},
            {"import3": {"key": 1}}
        ]
        self.assertEqual(mutils.get_results(results), {
                         "Total": 3, "Successful": 2})

    def test_get_results_import_happy(self):
        results = [
            {"import1": {"key": "value"}},
            {"import2": {"key": None}},
            {"import3": {"key": 1}}
        ]
        self.assertEqual(mutils.get_results(results), {
                         "Total": 3, "Successful": 3})

    def test_get_results_import_unhappy(self):
        results = [
            {"import1": False},
            {"import2": False},
            {"import3": False}
        ]
        self.assertEqual(mutils.get_results(results), {
                         "Total": 3, "Successful": 0})

    def test_get_results_error_message(self):
        results = [
            {"import1": {"key": "value"}},
            {"import2": {"message": "Failed to import"}},
            {"import3": {"key": 1}}
        ]
        self.assertEqual(mutils.get_results(results), {
                         "Total": 3, "Successful": 2})

    def test_get_results_repository_error_message(self):
        results = [
            {"import1": {"key": "value"}},
            {"import2": {"message": "Failed to import"}},
            {"import3": {"repository": True}},
            {"import4": {"repository": False}}
        ]
        self.assertEqual(mutils.get_results(results), {
                         "Total": 4, "Successful": 2})

    def test_is_top_level_group(self):
        self.assertTrue(mutils.is_top_level_group(
            self.mock_groups.get_group()))
        self.assertFalse(mutils.is_top_level_group(
            self.mock_groups.get_subgroup()))

    @patch("congregate.helpers.base_class.ConfigurationValidator.src_parent_id",
           new_callable=PropertyMock)
    def test_is_top_level_group_src_parent_group(self, src_parent_id):
        src_parent_id.return_value = 4
        self.assertTrue(mutils.is_top_level_group(
            self.mock_groups.get_subgroup()))

    def test_is_loc_supported_true(self):
        self.assertIsNone(mutils.is_loc_supported("aws"))
        self.assertIsNone(mutils.is_loc_supported("filesystem"))

    def test_is_loc_supported_false(self):
        with self.assertRaises(SystemExit):
            mutils.is_loc_supported("not-aws-or-filesystem")

    def test_can_migrate_users_true(self):
        users = [
            {
                "id": 3,
                "username": "gitlab",
                "name": "PS GitLab",
                "email": "proserv@gitlab.com",
                "avatar_url": "",
                "state": "active",
                "is_admin": True
            }
        ]
        self.assertTrue(mutils.can_migrate_users(users))

    def test_can_migrate_users_false(self):
        users = [
            {
                "id": 1,
                "username": "ghost",
                "name": "Ghost",
                "email": None,
                "avatar_url": "",
                "state": "active",
                "is_admin": False
            },
            {
                "id": 3,
                "username": "gitlab",
                "name": "PS GitLab",
                "email": "proserv@gitlab.com",
                "avatar_url": "",
                "state": "active",
                "is_admin": True
            }
        ]
        self.assertFalse(mutils.can_migrate_users(users))

    @patch.object(ConfigurationValidator, "destination_host",
                  new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, "dstn_parent_id",
                  new_callable=PropertyMock)
    def test_get_staged_user_projects_empty(self, mock_parent_id, mock_host):
        mock_host.return_value = "https://self-managed.com"
        mock_parent_id.return_value = None
        self.assertListEqual(mutils.get_staged_user_projects(
            self.mock_projects.get_staged_projects()), [])

    @patch.object(ConfigurationValidator, "destination_host",
                  new_callable=PropertyMock)
    @patch.object(ConfigurationValidator, "dstn_parent_id",
                  new_callable=PropertyMock)
    def test_get_staged_user_projects(self, mock_parent_id, mock_host):
        staged_projects = self.mock_projects.get_mix_staged_projects()
        user_projects = ["pmm-demo/spring-app-secure-2",
                         "pmm-demo/spring-app-secure-3"]
        mock_host.return_value = "https://gitlab.com"
        mock_parent_id.return_value = None
        self.assertListEqual(mutils.get_staged_user_projects(
            staged_projects), user_projects)

        mock_host.return_value = "https://self-managed.com"
        mock_parent_id.return_value = 1
        self.assertListEqual(mutils.get_staged_user_projects(
            staged_projects), user_projects)

    def test_check_is_project_or_group_for_logging_project(self):
        assert mutils.check_is_project_or_group_for_logging(True) is "Project"
        assert mutils.check_is_project_or_group_for_logging(False) is "Group"

    @patch("congregate.helpers.migrate_utils.get_staged_user_projects")
    def test_check_for_staged_user_projects_logs_on_true_and_returns_true(self, mock_get_staged_user_projects):
        mock_get_staged_user_projects.return_value = ["path_with_namespace"]
        with self.assertLogs(mutils.b.log, level="WARN") as al:
            self.assertListEqual(mutils.check_for_staged_user_projects([{}]), [
                                 "path_with_namespace"])
            self.assertListEqual(al.output, [
                                 'WARNING:congregate.helpers.base_class:User projects staged:\npath_with_namespace'])

    @patch("congregate.helpers.migrate_utils.get_staged_user_projects")
    def test_check_for_staged_user_projects_false_when_none_found(self, mock_get_staged_user_projects):
        mock_get_staged_user_projects.return_value = None
        # Looks like the self.assertNoLogs only exists in 3.10 and above, so just check the False
        assert mutils.check_for_staged_user_projects([{}]) is None

    @patch.object(ConfigurationValidator, "dstn_parent_group_path", new_callable=PropertyMock)
    def test_get_external_path_with_namespace(self, dstn_path):
        dstn_path.return_value = None
        path_with_namespace = "test/repo"
        self.assertEqual(mutils.get_external_path_with_namespace(
            path_with_namespace), path_with_namespace)

    @patch.object(ConfigurationValidator, "dstn_parent_group_path", new_callable=PropertyMock)
    def test_get_external_path_with_namespace_with_parent(self, dstn_path):
        dstn_path.return_value = "/parent/group"
        path_with_namespace = "test/repo"
        self.assertEqual(mutils.get_external_path_with_namespace(
            path_with_namespace), f"parent/group/{path_with_namespace}")

    def test_validate_name_project(self):
        assert mutils.validate_name(
            "-:: This.is-how/WE do\n&it#? - šđžčć") == "This.is-how WE do it - šđžčć"

    def test_validate_name_group(self):
        assert mutils.validate_name(
            "-:: This.is-how/WE do\n&it#? - (šđžčć)", is_group=True) == "This.is-how WE do it - (šđžčć)"

    def test_get_duplicate_paths_projects(self):
        data = [{
            "path_with_namespace": "a/b"
        },
            {
            "path_with_namespace": "d/b"
        },
            {
            "path_with_namespace": "d/b"
        },
            {
            "path_with_namespace": "d/b"
        },
            {
            "path_with_namespace": "a/b"
        },
            {
            "path_with_namespace": "b/c"
        }]
        expected = ["a/b", "d/b"]
        actual = mutils.get_duplicate_paths(data)

        self.assertEqual(expected, actual)

    def test_get_duplicate_paths_groups(self):
        data = [{
            "full_path": "a/b"
        },
            {
            "full_path": "d/b"
        },
            {
            "full_path": "d/b"
        },
            {
            "full_path": "d/b"
        },
            {
            "full_path": "a/b"
        },
            {
            "full_path": "b/c"
        }]
        expected = ["a/b", "d/b"]
        actual = mutils.get_duplicate_paths(data, are_projects=False)

        self.assertEqual(expected, actual)
