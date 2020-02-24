import json
import unittest
import mock
from congregate.migration.gitlab.importexport import ImportExportClient


class ImportExportClientTests(unittest.TestCase):

    def setUp(self):
        self.ie = ImportExportClient()
        self.original_project_name = "original_project_name"
        self.original_namespace_path = "original_namespace_path"
        self.name_taken_import_response = json.dumps(
            {"message": "Name has already been taken"})
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
                "web_url": "https://gitlab.com/original_namespace_path"
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

    def test_create_override_name(self):
        original_name = "some_project"
        self.assertEqual(self.ie.create_override_name(
            original_name), "some_project_1")

    @mock.patch("congregate.migration.gitlab.importexport.api.search")
    def test_get_import_id_from_import_response_happy(self, mock_search_api):
        """
        Needs an import_response object
        exported = false
        project entity
        name
        timeout 0

        mock api.search
        :return:
        """
        mock_search_api.return_value = self.search_response
        import_id_entity = self.ie.get_import_id_from_import_response(self.name_taken_import_response,
                                                                      False,
                                                                      self.original_project,
                                                                      self.original_project_name,
                                                                      0)

        self.assertEqual(import_id_entity, {
                         'import_id': 13240969, 'exported': False, 'duped': True})

    @mock.patch("congregate.migration.gitlab.importexport.api.search")
    def test_get_import_id_from_import_response_dupe_not_found(self, mock_search_api):
        """
        Needs an import_response object
        exported = false
        project entity
        name
        timeout 0

        mock api.search
        :return:
        """

        override_search_response = list(self.search_response)
        override_search_response[0]["name"] = "not_found"
        mock_search_api.return_value = override_search_response
        import_id_entity = self.ie.get_import_id_from_import_response(self.name_taken_import_response,
                                                                      False,
                                                                      self.original_project,
                                                                      self.original_project_name,
                                                                      0)

        self.assertEqual(import_id_entity, {
                         'import_id': None, 'exported': False, 'duped': False})

    @mock.patch.object(ImportExportClient, "get_import_id_from_import_response")
    @mock.patch.object(ImportExportClient, "attempt_import")
    def test_dupe_reimport_worker_happy(self, mock_attempt_import, mock_get_import_id_from_import_response):
        mock_attempt_import.return_value = self.name_taken_import_response
        mock_get_import_id_from_import_response.return_value = {
            'import_id': None, 'exported': False, 'duped': False}
        import_results = self.ie.dupe_reimport_worker(
            duped=True,
            append_suffix_on_dupe=True,
            exported=False,
            filename="filename_does_not_matter",
            name=self.original_project_name,
            namespace=self.original_namespace_path,
            override_params=self.override_params,
            project=self.original_project,
            timeout=0)
        self.assertEqual(import_results, {
                         'import_id': None, 'exported': False, 'duped': False})

    @mock.patch.object(ImportExportClient, "get_import_id_from_import_response")
    @mock.patch.object(ImportExportClient, "attempt_import")
    def test_dupe_reimport_worker_none_when_duped_false(
            self,
            mock_attempt_import,
            mock_get_import_id_from_import_response):
        mock_attempt_import.return_value = self.name_taken_import_response
        mock_get_import_id_from_import_response.return_value = {
            'import_id': None, 'exported': False, 'duped': False}
        import_results = self.ie.dupe_reimport_worker(
            duped=False,
            append_suffix_on_dupe=True,
            exported=False,
            filename="filename_does_not_matter",
            name=self.original_project_name,
            namespace=self.original_namespace_path,
            override_params=self.override_params,
            project=self.original_project,
            timeout=0)
        self.assertEqual(import_results, None)

    @mock.patch.object(ImportExportClient, "get_import_id_from_import_response")
    @mock.patch.object(ImportExportClient, "attempt_import")
    def test_dupe_reimport_worker_none_when_exported_true(
            self,
            mock_attempt_import,
            mock_get_import_id_from_import_response):
        mock_attempt_import.return_value = self.name_taken_import_response
        mock_get_import_id_from_import_response.return_value = {
            'import_id': None, 'exported': False, 'duped': False}
        import_results = self.ie.dupe_reimport_worker(
            duped=True,
            append_suffix_on_dupe=True,
            exported=True,
            filename="filename_does_not_matter",
            name=self.original_project_name,
            namespace=self.original_namespace_path,
            override_params=self.override_params,
            project=self.original_project,
            timeout=0)
        self.assertEqual(import_results, None)

    @mock.patch.object(ImportExportClient, "get_import_id_from_import_response")
    @mock.patch.object(ImportExportClient, "attempt_import")
    def test_dupe_reimport_worker_none_when_suffix_false(
            self,
            mock_attempt_import,
            mock_get_import_id_from_import_response):
        mock_attempt_import.return_value = self.name_taken_import_response
        mock_get_import_id_from_import_response.return_value = {
            'import_id': None, 'exported': False, 'duped': False}
        import_results = self.ie.dupe_reimport_worker(
            duped=True,
            append_suffix_on_dupe=False,
            exported=False,
            filename="filename_does_not_matter",
            name=self.original_project_name,
            namespace=self.original_namespace_path,
            override_params=self.override_params,
            project=self.original_project,
            timeout=0)
        self.assertEqual(import_results, None)

    def test_check_is_project_or_group_for_logging_project_on_true(self):
        self.assertEqual(
            self.ie.check_is_project_or_group_for_logging(True), "Project")

    def test_check_is_project_or_group_for_logging_group_on_false(self):
        self.assertEqual(
            self.ie.check_is_project_or_group_for_logging(False), "Group")

    @mock.patch.object(ImportExportClient, "get_group_download_status")
    def test_wait_for_group_download_200(self, mock_get_group_download_status):
        ok_response_mock = mock.MagicMock()
        type(ok_response_mock).status_code = mock.PropertyMock(
            return_value=200)
        mock_get_group_download_status.return_value = ok_response_mock
        self.assertTrue(self.ie.wait_for_group_download(1))

    @mock.patch.object(ImportExportClient, "get_group_download_status")
    @mock.patch('congregate.helpers.conf.Config.importexport_wait', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.conf.Config.max_export_wait_time', new_callable=mock.PropertyMock)
    def test_wait_for_group_download_404(self, max_wait, wait, mock_get_group_download_status):
        max_wait.return_value = 0
        wait.return_value = 0.01
        nok_response_mock = mock.MagicMock()
        type(nok_response_mock).status_code = mock.PropertyMock(
            return_value=404)
        mock_get_group_download_status.return_value = nok_response_mock
        self.assertFalse(self.ie.wait_for_group_download(1))

    @mock.patch('congregate.migration.gitlab.groups.GroupsClient.find_group_by_path')
    def test_wait_for_group_import_200(self, mock_find_group_by_path):
        mock_find_group_by_path.return_value = (True, 1)
        self.assertTrue(self.ie.wait_for_group_import("mock"))

    @mock.patch('congregate.migration.gitlab.groups.GroupsClient.find_group_by_path')
    @mock.patch('congregate.helpers.conf.Config.importexport_wait', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.conf.Config.max_export_wait_time', new_callable=mock.PropertyMock)
    def test_wait_for_group_import_404(self, max_wait, wait, mock_find_group_by_path):
        max_wait.return_value = 0
        wait.return_value = 0.01
        mock_find_group_by_path.return_value = (False, 1)
        self.assertFalse(self.ie.wait_for_group_import("mock"))
