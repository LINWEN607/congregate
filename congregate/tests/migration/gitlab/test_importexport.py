import json
import unittest
from mock import MagicMock, PropertyMock, patch
import responses
from congregate.migration.gitlab.importexport import ImportExportClient
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.tests.mockapi.gitlab.groups import MockGroupsApi


class ImportExportClientTests(unittest.TestCase):

    def setUp(self):
        self.ie = ImportExportClient()
        self.mock_groups = MockGroupsApi()
        self.original_project_name = "original_project_name"
        self.original_project_filename = "original_project_filename"
        self.original_project_path = "original_project_path"
        self.original_project_override_params = {
            "description": "test description"}
        self.original_namespace_path = "original_namespace_path"
        self.import_response = json.dumps({
            "id": 12345,
            "name": self.original_project_name,
            "name_with_namespace": self.original_namespace_path
        })
        self.search_response = [{
            "id": 13240969,
            "description": "",
            "name": self.original_project_name,
            "namespace": {
                "id": 5345589,
                "name": "original namespace",
                "path": self.original_namespace_path,
                "kind": "user",
                "full_path": self.original_namespace_path,
                "parent_id": None,
                "avatar_url": "/uploads/-/system/user/avatar/4090207/avatar.png",
            }
        }]
        self.original_project = {
            "name": self.original_project_name,
            "namespace": self.original_namespace_path,
            "default_branch": "master",
            "shared_runners_enabled": False,
            "description": "original project description"
        }
        self.override_params = [
            "override_params[description]=%s" % self.original_project["description"],
            "override_params[default_branch]=%s" % self.original_project["default_branch"],
            "override_params[shared_runners_enabled]=%s" % self.original_project["shared_runners_enabled"]
        ]
        self.members = [
            {
                "id": 1,
                "username": "raymond_smith",
                "name": "Raymond Smith",
                "state": "active",
                "avatar_url": "https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon",
                "expires_at": "2012-10-22T14:13:35Z",
                "access_level": 30,
                "group_saml_identity": None
            },
            {
                "id": 2,
                "username": "john_doe",
                "name": "John Doe",
                "state": "active",
                "avatar_url": "https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon",
                "expires_at": "2012-10-22T14:13:35Z",
                "access_level": 30,
                "group_saml_identity": {
                    "extern_uid": "ABC-1234567890",
                    "provider": "group_saml",
                    "saml_provider_id": 10
                }
            }
        ]

    def import_status_failed(self, *args, **kwargs):
        nok_status_mock = MagicMock()
        type(nok_status_mock).status_code = PropertyMock(return_value=200)
        nok_status_mock.json.return_value = {
            "id": 222,
            "import_status": "failed"
        }
        return nok_status_mock

    def import_status_finished(self, *args, **kwargs):
        ok_status_mock = MagicMock()
        type(ok_status_mock).status_code = PropertyMock(return_value=200)
        ok_status_mock.json.return_value = {
            "id": 111,
            "import_status": "finished"
        }
        return ok_status_mock

    def export_group_404(self, *args, **kwargs):
        nok_export_mock = MagicMock()
        type(nok_export_mock).status_code = PropertyMock(return_value=404)
        type(nok_export_mock).text = PropertyMock(
            return_value='{"message": "404 Not Found"}')
        return nok_export_mock

    def test_create_override_name(self):
        original_name = "some_project"
        self.assertEqual(self.ie.create_override_name(
            original_name), "some_project_1")

    @patch.object(ProjectsApi, "get_project_import_status")
    def test_get_import_id_from_response_finished(self, mock_status):
        ok_response_mock = MagicMock()
        type(ok_response_mock).status_code = PropertyMock(return_value=200)
        ok_response_mock.json.return_value = {
            "id": 111,
            "import_status": "finished"
        }
        mock_status.return_value = ok_response_mock
        import_id = self.ie.get_import_id_from_response(self.import_response, self.original_project_filename, self.original_project_name,
                                                        self.original_project_path, self.original_namespace_path, self.original_project_override_params, self.members)
        self.assertEqual(import_id, 12345)

    def test_get_import_id_from_response_import_id_none(self):
        import_response_none = json.dumps({
            "message": "not found"
        })
        import_id = self.ie.get_import_id_from_response(import_response_none, self.original_project_filename, self.original_project_name,
                                                        self.original_project_path, self.original_namespace_path, self.original_project_override_params, self.members)
        self.assertEqual(import_id, None)

    @patch.object(ProjectsApi, "get_project_import_status")
    def test_get_import_id_from_response_status_code_400(self, mock_status):
        nok_status_mock = MagicMock()
        type(nok_status_mock).status_code = PropertyMock(return_value=404)
        mock_status.return_value = nok_status_mock
        import_id = self.ie.get_import_id_from_response(self.import_response, self.original_project_filename, self.original_project_name,
                                                        self.original_project_path, self.original_namespace_path, self.original_project_override_params, self.members)
        self.assertEqual(import_id, None)

    @patch('congregate.helpers.conf.Config.importexport_wait', new_callable=PropertyMock)
    @patch('congregate.migration.gitlab.importexport.ImportExportClient.attempt_import')
    @patch.object(ProjectsApi, "get_project_import_status", side_effect=import_status_finished)
    @patch.object(ProjectsApi, "get_project")
    def test_get_import_id_from_response_finished_retry(self, get_project, mock_status, mock_import_response, wait):
        nok_get_project = MagicMock()
        type(nok_get_project).status_code = PropertyMock(return_value=404)
        get_project.return_value = nok_get_project
        nok_status_mock = MagicMock()
        type(nok_status_mock).status_code = PropertyMock(return_value=200)
        nok_status_mock.json.return_value = {
            "id": 222,
            "import_status": "failed"
        }
        mock_status.return_value = nok_status_mock
        mock_import_response.return_value = {
            "id": 111,
            "import_status": "finished"
        }
        wait.return_value = 0.01
        import_id = self.ie.get_import_id_from_response(self.import_response, self.original_project_filename, self.original_project_name,
                                                        self.original_project_path, self.original_namespace_path, self.original_project_override_params, [])
        self.assertEqual(import_id, 12345)

    @patch('congregate.helpers.conf.Config.destination_host', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.importexport_wait', new_callable=PropertyMock)
    @patch('congregate.migration.gitlab.importexport.ImportExportClient.attempt_import')
    @patch.object(ProjectsApi, "get_project_import_status", side_effect=import_status_failed)
    @patch.object(ProjectsApi, "get_project")
    def test_get_import_id_from_response_failed_retry(self, get_project, mock_status, mock_import_response, wait, dstn_host):
        dstn_host.return_value = "https://gitlab.com"
        nok_get_project = MagicMock()
        type(nok_get_project).status_code = PropertyMock(return_value=404)
        get_project.return_value = nok_get_project
        nok_status_mock = MagicMock()
        type(nok_status_mock).status_code = PropertyMock(return_value=200)
        nok_status_mock.json.return_value = {
            "id": 222,
            "import_status": "failed"
        }
        mock_status.return_value = nok_status_mock
        mock_import_response.return_value = json.dumps({
            "id": 222,
            "import_status": "failed"
        })
        wait.return_value = 0.01
        import_id = self.ie.get_import_id_from_response(self.import_response, self.original_project_filename, self.original_project_name,
                                                        self.original_project_path, self.original_namespace_path, self.original_project_override_params, self.members)
        self.assertEqual(import_id, None)

    @patch('congregate.helpers.conf.Config.importexport_wait', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.max_export_wait_time', new_callable=PropertyMock)
    @patch.object(ProjectsApi, "get_project_import_status")
    def test_get_import_id_from_response_timeout(self, mock_status, max_wait, wait):
        wait.return_value = 0.01
        max_wait.return_value = 0.1
        ok_status_mock = MagicMock()
        type(ok_status_mock).status_code = PropertyMock(return_value=200)
        ok_status_mock.json.return_value = {
            "id": 333,
            "import_status": "scheduled"
        }
        mock_status.return_value = ok_status_mock
        import_id = self.ie.get_import_id_from_response(self.import_response, self.original_project_filename, self.original_project_name,
                                                        self.original_project_path, self.original_namespace_path, self.original_project_override_params, self.members)
        self.assertEqual(import_id, None)

    @patch.object(ProjectsApi, "export_project")
    @patch.object(ProjectsApi, "get_project_export_status")
    def test_wait_for_export_to_finish_project_202_200_finished(self, mock_get_project_export_status, mock_export_project):
        ok_export_mock = MagicMock()
        type(ok_export_mock).status_code = PropertyMock(
            return_value=202)
        type(ok_export_mock).text = PropertyMock(
            return_value='{"message": "202 Accepted"}')
        mock_export_project.return_value = ok_export_mock
        ok_status_mock = MagicMock()
        type(ok_status_mock).status_code = PropertyMock(
            return_value=200)
        ok_status_mock.json.return_value = {"export_status": "finished"}
        mock_get_project_export_status.return_value = ok_status_mock
        self.assertTrue(self.ie.wait_for_export_to_finish(1, "test"))

    @patch('congregate.helpers.conf.Config.importexport_wait', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.max_export_wait_time', new_callable=PropertyMock)
    @patch.object(ProjectsApi, "export_project")
    @patch.object(ProjectsApi, "get_project_export_status")
    def test_wait_for_export_to_finish_project_202_200_none_timeout(self, mock_get_project_export_status, mock_export_project, max_wait, wait):
        wait.return_value = 0.01
        max_wait.return_value = 0.1
        ok_export_mock = MagicMock()
        type(ok_export_mock).status_code = PropertyMock(
            return_value=202)
        type(ok_export_mock).text = PropertyMock(
            return_value='{"message": "202 Accepted"}')
        mock_export_project.return_value = ok_export_mock
        ok_status_mock = MagicMock()
        type(ok_status_mock).status_code = PropertyMock(
            return_value=200)
        ok_status_mock.json.return_value = {"export_status": "none"}
        mock_get_project_export_status.return_value = ok_status_mock
        self.assertFalse(self.ie.wait_for_export_to_finish(1, "test"))

    @patch.object(ProjectsApi, "export_project")
    def test_wait_for_export_to_finish_project_404(self, mock_export_project):
        ok_export_mock = MagicMock()
        type(ok_export_mock).status_code = PropertyMock(
            return_value=404)
        type(ok_export_mock).text = PropertyMock(
            return_value='{"message": "404 Not Found"}')
        mock_export_project.return_value = ok_export_mock
        self.assertFalse(self.ie.wait_for_export_to_finish(
            1, "test", retry=False))

    @patch.object(GroupsApi, "export_group")
    @patch.object(GroupsApi, "get_group_download_status")
    def test_wait_for_group_download_202_200(self, mock_get_group_download_status, mock_export_group):
        ok_export_mock = MagicMock()
        type(ok_export_mock).status_code = PropertyMock(
            return_value=202)
        type(ok_export_mock).text = PropertyMock(
            return_value='{"message": "202 Accepted"}')
        mock_export_group.return_value = ok_export_mock
        ok_status_mock = MagicMock()
        type(ok_status_mock).status_code = PropertyMock(
            return_value=200)
        mock_get_group_download_status.return_value = ok_status_mock
        self.assertTrue(self.ie.wait_for_group_download(1))

    @patch('congregate.helpers.conf.Config.importexport_wait', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.max_export_wait_time', new_callable=PropertyMock)
    @patch.object(GroupsApi, "export_group")
    @patch.object(GroupsApi, "get_group_download_status")
    def test_wait_for_group_download_202_404_timeout(self, mock_get_group_download_status, mock_export_group, max_wait, wait):
        wait.return_value = 0.01
        max_wait.return_value = 0.1
        ok_export_mock = MagicMock()
        type(ok_export_mock).status_code = PropertyMock(
            return_value=202)
        type(ok_export_mock).text = PropertyMock(
            return_value='{"message": "202 Accepted"}')
        mock_export_group.return_value = ok_export_mock
        nok_status_mock = MagicMock()
        type(nok_status_mock).status_code = PropertyMock(
            return_value=404)
        mock_get_group_download_status.return_value = nok_status_mock
        self.assertFalse(self.ie.wait_for_group_download(1))

    @patch.object(GroupsApi, "export_group")
    @patch.object(GroupsApi, "get_group_download_status")
    def test_wait_for_group_download_404(self, mock_get_group_download_status, mock_export_group):
        ok_export_mock = MagicMock()
        type(ok_export_mock).status_code = PropertyMock(
            return_value=404)
        type(ok_export_mock).text = PropertyMock(
            return_value='{"message": "404 Not Found"}')
        mock_export_group.return_value = ok_export_mock
        self.assertFalse(self.ie.wait_for_group_download(1, retry=False))

    # pylint: disable=no-member
    @responses.activate
    # pylint: enable=no-member
    @patch("congregate.helpers.api.generate_v4_request_url")
    @patch('congregate.migration.gitlab.groups.GroupsClient.find_group_by_path')
    def test_wait_for_group_import_200(self, mock_find_group_by_path, url):
        mock_find_group_by_path.return_value = self.mock_groups.get_group()
        url_value = "https://gitlabdestination.com/api/v4/groups/1"
        url.return_value = url_value
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                      json=self.mock_groups.get_group(), status=200)
        # pylint: enable=no-member
        self.assertTrue(self.ie.wait_for_group_import("mock"))

    @patch('congregate.migration.gitlab.groups.GroupsClient.find_group_by_path')
    @patch('congregate.helpers.conf.Config.importexport_wait', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.max_export_wait_time', new_callable=PropertyMock)
    def test_wait_for_group_import_404(self, max_wait, wait, mock_find_group_by_path):
        max_wait.return_value = 0.1
        wait.return_value = 0.01
        mock_find_group_by_path.return_value = None
        self.assertFalse(self.ie.wait_for_group_import("mock"))
