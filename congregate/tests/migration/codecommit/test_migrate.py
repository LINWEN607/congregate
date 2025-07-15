# import unittest
# from unittest.mock import patch, MagicMock, PropertyMock
# import pytest
# import requests

# from congregate.migration.codecommit.migrate import CodeCommitMigrateClient
# from congregate.helpers.configuration_validator import ConfigurationValidator

# @pytest.mark.unit_test
# class TestCodeCommitMigrateClient(unittest.TestCase):
#     @patch('congregate.helpers.configuration_validator.ConfigurationValidator.dstn_token_validated_in_session', new_callable=PropertyMock)
#     @patch('congregate.helpers.configuration_validator.ConfigurationValidator.src_token_validated_in_session', new_callable=PropertyMock)
#     @patch('congregate.helpers.configuration_validator.ConfigurationValidator.src_aws_session_token', new_callable=PropertyMock)
#     @patch('congregate.helpers.configuration_validator.ConfigurationValidator.src_aws_secret_access_key', new_callable=PropertyMock)
#     @patch('congregate.helpers.conf.Config.destination_host', new_callable=PropertyMock)
#     @patch('congregate.helpers.conf.Config.src_aws_access_key_id', new_callable=PropertyMock)
#     @patch('congregate.helpers.conf.Config.source_type', new_callable=PropertyMock)
#     @patch('congregate.helpers.conf.Config.src_aws_region', new_callable=PropertyMock)
#     def setUp(self, mock_src_aws_region, mock_source_type, mock_src_aws_access_key_id, mock_dstn_host, mock_src_aws_secret_access_key, mock_src_aws_session_token, src_validated, dstn_validated):
#         """Set up test fixtures."""
#         src_validated.return_value = True
#         dstn_validated.return_value = True
#         mock_src_aws_region.return_value = "us-east-1"
#         mock_source_type.return_value = "codecommit"
#         mock_src_aws_access_key_id.return_value = "FAKE_KEY"
#         mock_src_aws_secret_access_key.return_value = "RkFLRV9TRUNSRVQ="
#         mock_src_aws_session_token.return_value = "RkFLRV9UT0tFTg=="
#         mock_dstn_host.return_value = "https://test.gitlab.com"
#         self.migrate_client = CodeCommitMigrateClient()
#         # Add missing attributes
#         self.migrate_client.groups = MagicMock()
#         self.migrate_client.projects = MagicMock()
#         self.migrate_client.groups_api = MagicMock()
#         self.migrate_client.ext_import = MagicMock()
#         self.migrate_client.config = MagicMock()
        
#     @patch('congregate.helpers.migrate_utils.get_staged_projects')
#     @patch('congregate.helpers.migrate_utils.validate_groups_and_projects')
#     @patch('congregate.helpers.migrate_utils.get_staged_user_projects')
#     @patch.object(CodeCommitMigrateClient, 'import_codecommit_repo')
#     def test_migrate_codecommit_repo_info_with_projects(self, mock_import, mock_user_projects, 
#                                                       mock_validate, mock_get_staged):
#         mock_get_staged.return_value = [
#             {"name": "repo1", "path": "/path/to/repo", "id": 123, "path_with_namespace": "/path/to/repo"},
#             {"name": "repo2", "path": "/path/to/repo", "id": 123, "path_with_namespace": "/path/to/repo"}
#         ]
#         mock_user_projects.return_value = []
#         mock_import.side_effect = [
#             {"status": "success", "project": "repo1"},
#             {"status": "success", "project": "repo2"}
#         ]
        
#         self.migrate_client.migrate_codecommit_repo_info("dry-run")
        
#         self.assertEqual(mock_import.call_count, 2)

#     @patch('congregate.helpers.migrate_utils.get_stage_wave_paths')
#     def test_import_codecommit_repo_group_creation_failed(self, mock_paths):
#         """Test importing repository when group creation fails."""
#         mock_paths.return_value = ("test/repo", "test")
#         self.migrate_client.groups.find_group_id_by_path.return_value = None
        
#         mock_response = MagicMock()
#         mock_response.status_code = 403
#         mock_response.text = "Permission denied"
        
#         self.migrate_client.groups_api.create_group = MagicMock(return_value=mock_response)
        
#         # Mock the ext_import.get_result_data to return a structure with an error
#         self.migrate_client.ext_import.get_result_data.return_value = {
#             "test/repo": {
#                 "error": "Failed to create namespace: Permission denied"
#             }
#         }
        
#         result = self.migrate_client.import_codecommit_repo(
#             {"name": "test-repo", "path": "test/repo"},
#             "test-repo"
#         )
        
#         self.assertIn("error", result["test/repo"])
#         self.assertIn("Failed to create namespace", result["test/repo"]["error"])

#     @patch('congregate.helpers.migrate_utils.get_stage_wave_paths')
#     def test_import_codecommit_repo_already_imported(self, mock_paths):
#         """Test importing repository that was already imported."""
#         mock_paths.return_value = ("test/repo", "test")
#         self.migrate_client.groups.find_group_id_by_path.return_value = True
#         self.migrate_client.projects.find_project_by_path.return_value = 123
        
#         expected_result = {
#             "test/repo": {
#                 "id": 123,
#                 "import_status": "success"
#             }
#         }
#         self.migrate_client.ext_import.get_result_data.return_value = expected_result
        
#         result = self.migrate_client.import_codecommit_repo(
#             {"name": "test-repo", "path": "test/repo"}, 
#             "test-repo"
#         )
        
#         self.assertEqual(result["test/repo"]["id"], 123) 