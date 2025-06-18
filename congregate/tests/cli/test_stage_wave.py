import os
import sys
import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
import tempfile
import json

from congregate.cli.stage_wave import WaveStageCLI
from congregate.migration.meta.etl import WaveSpreadsheetHandler


class TestWaveStageCLI:
    
    @pytest.fixture
    def wave_stage_cli(self):
        """Create a WaveStageCLI instance with mocked dependencies."""
        with patch('congregate.cli.stage_wave.ProjectStageCLI'), \
             patch('congregate.cli.stage_wave.GroupsApi'), \
             patch('congregate.cli.stage_wave.BaseStageClass.__init__'):
            cli = WaveStageCLI()
            cli.log = Mock()
            cli.config = Mock()
            cli.staged_projects = []
            cli.staged_groups = []
            cli.staged_users = []
            return cli

    def test_init(self):
        """Test WaveStageCLI initialization."""
        with patch('congregate.cli.stage_wave.ProjectStageCLI') as mock_pcli, \
             patch('congregate.cli.stage_wave.GroupsApi') as mock_groups_api, \
             patch('congregate.cli.stage_wave.BaseStageClass.__init__') as mock_base_init:
            
            cli = WaveStageCLI()
            
            mock_pcli.assert_called_once()
            mock_groups_api.assert_called_once()
            mock_base_init.assert_called_once()
            assert hasattr(cli, 'pcli')
            assert hasattr(cli, 'groups_api')

    def test_parent_path_fail(self, wave_stage_cli):
        """Test parent_path_fail method exits with proper error."""
        parent_path = "invalid_path"
        
        with pytest.raises(SystemExit) as exc_info:
            wave_stage_cli.parent_path_fail(parent_path)
        
        assert exc_info.value.code == os.EX_CONFIG
        wave_stage_cli.log.error.assert_called_once_with(
            f"'Parent Path' column missing or misspelled ({parent_path}). Exiting..."
        )

    @patch('congregate.cli.stage_wave.get_staged_user_projects')
    @patch('congregate.cli.stage_wave.is_dot_com')
    @patch('congregate.cli.stage_wave.remove_dupes')
    @patch('congregate.cli.stage_wave.json_pretty')
    def test_stage_data_with_user_projects_dot_com(self, mock_json_pretty, mock_remove_dupes, 
                                                   mock_is_dot_com, mock_get_staged_user_projects, 
                                                   wave_stage_cli):
        """Test stage_data method with user projects on gitlab.com."""
        # Setup mocks
        wave_stage_cli.stage_wave = Mock()
        wave_stage_cli.are_staged_users_without_public_email = Mock()
        wave_stage_cli.write_staging_files = Mock()
        wave_stage_cli.config.source_type = "gitlab"
        wave_stage_cli.config.direct_transfer = False
        wave_stage_cli.config.destination_host = "gitlab.com"
        
        mock_remove_dupes.return_value = ["project1", "project2"]
        mock_get_staged_user_projects.return_value = ["user_project1"]
        mock_is_dot_com.return_value = True
        mock_json_pretty.return_value = '["user_project1"]'
        
        # Execute
        wave_stage_cli.stage_data("wave1", dry_run=False, skip_users=True, scm_source="source")
        
        # Verify
        wave_stage_cli.stage_wave.assert_called_once_with("wave1", skip_users=True, dry_run=False, scm_source="source")
        wave_stage_cli.log.warning.assert_any_call(
            "USER projects staged (Count : 1):\n[\"user_project1\"]"
        )
        wave_stage_cli.log.warning.assert_any_call(
            "Please manually migrate USER projects to gitlab.com"
        )
        wave_stage_cli.are_staged_users_without_public_email.assert_called_once()
        wave_stage_cli.write_staging_files.assert_called_once_with(skip_users=True)

    @patch('congregate.cli.stage_wave.get_staged_user_projects')
    def test_stage_data_no_user_projects(self, mock_get_staged_user_projects, wave_stage_cli):
        """Test stage_data method with no user projects."""
        wave_stage_cli.stage_wave = Mock()
        wave_stage_cli.are_staged_users_without_public_email = Mock()
        wave_stage_cli.write_staging_files = Mock()
        wave_stage_cli.config.source_type = "gitlab"
        wave_stage_cli.config.direct_transfer = False
        
        mock_get_staged_user_projects.return_value = []
        
        wave_stage_cli.stage_data("wave1", dry_run=True)
        
        # Should not call warning about user projects
        assert not any("USER projects staged" in str(call) for call in wave_stage_cli.log.warning.call_args_list)

    @patch('congregate.cli.stage_wave.WaveSpreadsheetHandler')
    @patch('congregate.cli.stage_wave.rewrite_list_into_dict')
    @patch('os.path.isfile')
    def test_stage_wave_file_not_exists(self, mock_isfile, mock_rewrite, mock_wsh, wave_stage_cli):
        """Test stage_wave method when spreadsheet file doesn't exist."""
        mock_isfile.return_value = False
        wave_stage_cli.config.wave_spreadsheet_path = "/nonexistent/path"
        wave_stage_cli.the_number_of_instance = Mock(return_value=0)
        wave_stage_cli.open_projects_file = Mock(return_value=[])
        wave_stage_cli.open_users_file = Mock(return_value=[])
        wave_stage_cli.open_groups_file = Mock(return_value=[])
        
        with pytest.raises(SystemExit) as exc_info:
            wave_stage_cli.stage_wave("wave1")
        
        assert exc_info.value.code == os.EX_CONFIG
        wave_stage_cli.log.error.assert_called_once()

    @patch('congregate.cli.stage_wave.WaveSpreadsheetHandler')
    @patch('congregate.cli.stage_wave.rewrite_list_into_dict')
    @patch('os.path.isfile')
    def test_stage_wave_no_wave_data(self, mock_isfile, mock_rewrite, mock_wsh, wave_stage_cli):
        """Test stage_wave method when no wave data is found."""
        mock_isfile.return_value = True
        wave_stage_cli.config.wave_spreadsheet_path = "/valid/path"
        wave_stage_cli.config.wave_spreadsheet_columns = ["col1", "col2"]
        wave_stage_cli.the_number_of_instance = Mock(return_value=0)
        wave_stage_cli.open_projects_file = Mock(return_value=[])
        wave_stage_cli.open_users_file = Mock(return_value=[])
        wave_stage_cli.open_groups_file = Mock(return_value=[])
        wave_stage_cli.check_spreadsheet_data = Mock()
        
        mock_wsh_instance = Mock()
        mock_wsh_instance.read_file_as_json.return_value = []
        mock_wsh.return_value = mock_wsh

    def test_check_spreadsheet_kv_all_items_exist(self, wave_stage_cli):
        """Test check_spreadsheet_kv when all mapping items exist in columns"""
        mapping = ['col1', 'col2', 'col3']
        columns = ['col1', 'col2', 'col3', 'col4']
        
        result = wave_stage_cli.check_spreadsheet_kv(mapping, columns)
        
        assert result is True

    def test_check_spreadsheet_kv_some_items_missing(self, wave_stage_cli):
        """Test check_spreadsheet_kv when some mapping items are missing from columns"""
        mapping = ['col1', 'col2', 'col3']
        columns = ['col1', 'col3']  # col2 is missing
        
        result = wave_stage_cli.check_spreadsheet_kv(mapping, columns)
        
        assert result is False

    def test_check_spreadsheet_kv_no_items_exist(self, wave_stage_cli):
        """Test check_spreadsheet_kv when no mapping items exist in columns"""
        mapping = ['col1', 'col2', 'col3']
        columns = ['col4', 'col5', 'col6']
        
        result = wave_stage_cli.check_spreadsheet_kv(mapping, columns)
        
        assert result is False

    def test_check_spreadsheet_kv_empty_mapping(self, wave_stage_cli):
        """Test check_spreadsheet_kv with empty mapping"""
        mapping = []
        columns = ['col1', 'col2', 'col3']
        
        result = wave_stage_cli.check_spreadsheet_kv(mapping, columns)
        
        assert result is True  # 0 == len([]) is True

    def test_check_spreadsheet_kv_empty_columns(self, wave_stage_cli):
        """Test check_spreadsheet_kv with empty columns"""
        mapping = ['col1', 'col2']
        columns = []
        
        result = wave_stage_cli.check_spreadsheet_kv(mapping, columns)
        
        assert result is False  # 0 != len(['col1', 'col2'])

    def test_check_spreadsheet_kv_both_empty(self, wave_stage_cli):
        """Test check_spreadsheet_kv with both mapping and columns empty"""
        mapping = []
        columns = []
        
        result = wave_stage_cli.check_spreadsheet_kv(mapping, columns)
        
        assert result is True  # 0 == len([]) is True

    def test_check_spreadsheet_data_all_valid(self, wave_stage_cli):
        """Test check_spreadsheet_data when all configuration is valid"""
        wave_stage_cli.config.wave_spreadsheet_column_to_project_property_mapping = ['col1', 'col2']
        wave_stage_cli.config.wave_spreadsheet_columns = ['col1', 'col2', 'col3']
        
        wave_stage_cli.check_spreadsheet_data()
        
        # Should not log any warnings
        wave_stage_cli.log.warning.assert_not_called()

    def test_check_spreadsheet_data_missing_mapping(self, wave_stage_cli):
        """Test check_spreadsheet_data when mapping configuration is missing"""
        wave_stage_cli.config.wave_spreadsheet_column_to_project_property_mapping = None
        wave_stage_cli.config.wave_spreadsheet_columns = ['col1', 'col2']
        
        wave_stage_cli.check_spreadsheet_data()
        
        wave_stage_cli.log.warning.assert_called_with(
            "No 'wave_spreadsheet_column_to_project_property_mapping' field in congregate.conf"
        )

    def test_check_spreadsheet_data_empty_mapping(self, wave_stage_cli):
        """Test check_spreadsheet_data when mapping configuration is empty"""
        wave_stage_cli.config.wave_spreadsheet_column_to_project_property_mapping = []
        wave_stage_cli.config.wave_spreadsheet_columns = ['col1', 'col2']
        
        wave_stage_cli.check_spreadsheet_data()
        
        wave_stage_cli.log.warning.assert_called_with(
            "No 'wave_spreadsheet_column_to_project_property_mapping' field in congregate.conf"
        )

    def test_check_spreadsheet_data_missing_columns(self, wave_stage_cli):
        """Test check_spreadsheet_data when columns configuration is missing"""
        wave_stage_cli.config.wave_spreadsheet_column_to_project_property_mapping = ['col1', 'col2']
        wave_stage_cli.config.wave_spreadsheet_columns = None
        
        wave_stage_cli.check_spreadsheet_data()
        
        wave_stage_cli.log.warning.assert_called_with(
            "No 'wave_spreadsheet_columns' field in congregate.conf"
        )

    def test_check_spreadsheet_data_empty_columns(self, wave_stage_cli):
        """Test check_spreadsheet_data when columns configuration is empty"""
        wave_stage_cli.config.wave_spreadsheet_column_to_project_property_mapping = ['col1', 'col2']
        wave_stage_cli.config.wave_spreadsheet_columns = []
        
        wave_stage_cli.check_spreadsheet_data()
        
        wave_stage_cli.log.warning.assert_called_with(
            "No 'wave_spreadsheet_columns' field in congregate.conf"
        )

    def test_check_spreadsheet_data_mismatch_warning(self, wave_stage_cli):
        """Test check_spreadsheet_data when there's a mismatch between mapping and columns"""
        wave_stage_cli.config.wave_spreadsheet_column_to_project_property_mapping = ['col1', 'col2', 'col3']
        wave_stage_cli.config.wave_spreadsheet_columns = ['col1', 'col2']  # col3 missing
        
        wave_stage_cli.check_spreadsheet_data()
        
        # Should log the mismatch warning
        expected_calls = [
            pytest.mock.call("Mismatch between keys in wave_spreadsheet_columns and wave_spreadsheet_column_to_project_property_mapping")
        ]
        wave_stage_cli.log.warning.assert_has_calls(expected_calls)

    def test_check_spreadsheet_data_both_missing(self, wave_stage_cli):
        """Test check_spreadsheet_data when both configurations are missing"""
        wave_stage_cli.config.wave_spreadsheet_column_to_project_property_mapping = None
        wave_stage_cli.config.wave_spreadsheet_columns = None
        
        wave_stage_cli.check_spreadsheet_data()
        
        # Should log both warnings
        expected_calls = [
            pytest.mock.call("No 'wave_spreadsheet_column_to_project_property_mapping' field in congregate.conf"),
            pytest.mock.call("No 'wave_spreadsheet_columns' field in congregate.conf")
        ]
        wave_stage_cli.log.warning.assert_has_calls(expected_calls, any_order=True)

    def test_check_spreadsheet_data_case_sensitive_columns(self, wave_stage_cli):
        """Test check_spreadsheet_data with case-sensitive column matching"""
        wave_stage_cli.config.wave_spreadsheet_column_to_project_property_mapping = ['Col1', 'col2']
        wave_stage_cli.config.wave_spreadsheet_columns = ['col1', 'col2']  # Different case for Col1
        
        wave_stage_cli.check_spreadsheet_data()
        
        # Should log mismatch warning due to case sensitivity
        wave_stage_cli.log.warning.assert_called_with(
            "Mismatch between keys in wave_spreadsheet_columns and wave_spreadsheet_column_to_project_property_mapping"
        )

    def test_check_spreadsheet_data_duplicate_columns(self, wave_stage_cli):
        """Test check_spreadsheet_data with duplicate columns"""
        wave_stage_cli.config.wave_spreadsheet_column_to_project_property_mapping = ['col1', 'col1', 'col2']
        wave_stage_cli.config.wave_spreadsheet_columns = ['col1', 'col2']
        
        wave_stage_cli.check_spreadsheet_data()
        
        # Should log mismatch warning due to duplicates
        wave_stage_cli.log.warning.assert_called_with(
            "Mismatch between keys in wave_spreadsheet_columns and wave_spreadsheet_column_to_project_property_mapping"
        )