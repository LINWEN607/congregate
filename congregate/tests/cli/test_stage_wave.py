import os
import pytest

from congregate.cli.stage_wave import WaveStageCLI

@pytest.mark.unit_test
class TestWaveStageCLI:
    
    @pytest.fixture
    def wave_stage_cli(self, monkeypatch):
        """Create a WaveStageCLI instance with mocked dependencies."""
        # Create mock classes using simple callables
        def mock_project_stage_cli():
            return type('MockProjectStageCLI', (), {})()
        
        def mock_groups_api():
            return type('MockGroupsApi', (), {})()
        
        def mock_base_stage_init(self):
            pass
        
        # Apply patches
        monkeypatch.setattr('congregate.cli.stage_wave.ProjectStageCLI', mock_project_stage_cli)
        monkeypatch.setattr('congregate.cli.stage_wave.GroupsApi', mock_groups_api)
        monkeypatch.setattr('congregate.cli.stage_wave.BaseStageClass.__init__', mock_base_stage_init)
        
        cli = WaveStageCLI()
        
        # Create mock objects for the CLI with proper call tracking
        class MockLogger:
            def __init__(self):
                self.error_calls = []
                self.warning_calls = []
            
            def error(self, msg):
                self.error_calls.append(msg)
            
            def warning(self, msg):
                self.warning_calls.append(msg)
            
            def assert_called_once_with(self, msg):
                return len([c for c in self.error_calls if c == msg]) == 1
            
            def assert_any_call(self, msg):
                return msg in self.warning_calls
            
            def assert_not_called(self):
                return len(self.warning_calls) == 0
        
        cli.log = MockLogger()
        cli.config = type('MockConfig', (), {})()
        cli.staged_projects = []
        cli.staged_groups = []
        cli.staged_users = []
        return cli

    def test_init(self, monkeypatch):
        """Test WaveStageCLI initialization."""
        base_init_called = []
        
        def mock_pcli():
            return type('MockProjectStageCLI', (), {})()
        
        def mock_groups_api():
            return type('MockGroupsApi', (), {})()
        
        def mock_base_init(self):
            base_init_called.append(True)
        
        monkeypatch.setattr('congregate.cli.stage_wave.ProjectStageCLI', mock_pcli)
        monkeypatch.setattr('congregate.cli.stage_wave.GroupsApi', mock_groups_api)
        monkeypatch.setattr('congregate.cli.stage_wave.BaseStageClass.__init__', mock_base_init)
        
        cli = WaveStageCLI()
        
        assert len(base_init_called) == 1
        assert hasattr(cli, 'pcli')
        assert hasattr(cli, 'groups_api')

    def test_parent_path_fail(self, wave_stage_cli):
        """Test parent_path_fail method exits with proper error."""
        parent_path = "invalid_path"
        
        with pytest.raises(SystemExit) as exc_info:
            wave_stage_cli.parent_path_fail(parent_path)
        
        assert exc_info.value.code == os.EX_CONFIG
        expected_msg = f"'Parent Path' column missing or misspelled ({parent_path}). Exiting..."
        assert expected_msg in wave_stage_cli.log.error_calls
        assert len(wave_stage_cli.log.error_calls) == 1

    def test_stage_data_no_user_projects(self, wave_stage_cli, monkeypatch):
        """Test stage_data method with no user projects."""
        wave_stage_cli.stage_wave = lambda *args, **kwargs: None
        wave_stage_cli.are_staged_users_without_public_email = lambda: None
        wave_stage_cli.write_staging_files = lambda **kwargs: None
        wave_stage_cli.config.source_type = "gitlab"
        wave_stage_cli.config.direct_transfer = False
        
        wave_stage_cli.stage_data("wave1", dry_run=True)
        
        # Should not call warning about user projects
        assert not any("USER projects staged" in str(call) for call in wave_stage_cli.log.warning_calls)

    def test_stage_data_direct_transfer(self, wave_stage_cli, monkeypatch):
        """Test stage_data method with direct transfer enabled."""
        email_check_calls = []
        
        def mock_email_check():
            email_check_calls.append(True)
        
        wave_stage_cli.stage_wave = lambda *args, **kwargs: None
        wave_stage_cli.are_staged_users_without_public_email = mock_email_check
        wave_stage_cli.write_staging_files = lambda **kwargs: None
        wave_stage_cli.config.source_type = "gitlab"
        wave_stage_cli.config.direct_transfer = True
        
        wave_stage_cli.stage_data("wave1", dry_run=False)
        
        # Should not check for users without public email when direct_transfer is True
        assert len(email_check_calls) == 0

    def test_stage_data_non_gitlab_source(self, wave_stage_cli, monkeypatch):
        """Test stage_data method with non-gitlab source type."""
        email_check_calls = []
        
        def mock_email_check():
            email_check_calls.append(True)
        
        wave_stage_cli.stage_wave = lambda *args, **kwargs: None
        wave_stage_cli.are_staged_users_without_public_email = mock_email_check
        wave_stage_cli.write_staging_files = lambda **kwargs: None
        wave_stage_cli.config.source_type = "github"
        wave_stage_cli.config.direct_transfer = False
        
        wave_stage_cli.stage_data("wave1", dry_run=False)
        
        # Should not check for users without public email when source_type is not gitlab
        assert len(email_check_calls) == 0

    def test_stage_wave_file_not_exists(self, wave_stage_cli, monkeypatch):
        """Test stage_wave method when spreadsheet file doesn't exist."""
        monkeypatch.setattr('os.path.isfile', lambda x: False)
        monkeypatch.setattr('congregate.cli.stage_wave.WaveSpreadsheetHandler', lambda *args, **kwargs: None)
        monkeypatch.setattr('congregate.cli.stage_wave.rewrite_list_into_dict', lambda x, y, **kwargs: x)
        
        wave_stage_cli.config.wave_spreadsheet_path = "/nonexistent/path"
        wave_stage_cli.the_number_of_instance = lambda scm_source=None: 0
        wave_stage_cli.open_projects_file = lambda scm_source=None: []
        wave_stage_cli.open_users_file = lambda scm_source=None: []
        wave_stage_cli.open_groups_file = lambda scm_source=None: []
        
        with pytest.raises(SystemExit) as exc_info:
            wave_stage_cli.stage_wave("wave1")
        
        assert exc_info.value.code == os.EX_CONFIG
        assert len(wave_stage_cli.log.error_calls) == 1

    def test_stage_wave_scm_source_not_found(self, wave_stage_cli, monkeypatch):
        """Test stage_wave method when scm_source instance is not found."""
        monkeypatch.setattr('os.path.isfile', lambda x: True)
        monkeypatch.setattr('congregate.cli.stage_wave.rewrite_list_into_dict', lambda x, y, **kwargs: {})
        
        mock_wsh_instance = type('MockWaveSpreadsheetHandler', (), {})()
        mock_wsh_instance.read_file_as_json = lambda **kwargs: [{"Source Project ID": "123"}]
        
        def mock_wsh_constructor(*args, **kwargs):
            return mock_wsh_instance
        
        monkeypatch.setattr('congregate.cli.stage_wave.WaveSpreadsheetHandler', mock_wsh_constructor)
        
        wave_stage_cli.config.wave_spreadsheet_path = "/valid/path"
        wave_stage_cli.config.wave_spreadsheet_columns = ["col1", "col2"]
        wave_stage_cli.config.wave_spreadsheet_column_mapping = {}
        wave_stage_cli.the_number_of_instance = lambda scm_source: -1  # Returns -1 for not found
        wave_stage_cli.open_projects_file = lambda scm_source=None: []
        wave_stage_cli.open_users_file = lambda scm_source=None: []
        wave_stage_cli.open_groups_file = lambda scm_source=None: []
        wave_stage_cli.check_spreadsheet_data = lambda: None
        
        # Mock pcli.stage_data
        stage_data_calls = []
        def mock_stage_data(*args, **kwargs):
            stage_data_calls.append(args)
        wave_stage_cli.pcli.stage_data = mock_stage_data
        
        wave_stage_cli.stage_wave("wave1", scm_source="unknown_host")
        
        # Should log warning about not finding the instance
        assert any("Couldn't find the correct GH instance with hostname: unknown_host" in call 
                  for call in wave_stage_cli.log.warning_calls)

    def test_stage_wave_no_wave_data(self, wave_stage_cli, monkeypatch):
        """Test stage_wave method when no wave data is found."""
        monkeypatch.setattr('os.path.isfile', lambda x: True)
        
        # Create a mock spreadsheet handler
        def mock_wsh_constructor(*args, **kwargs):
            mock_instance = type('MockWaveSpreadsheetHandler', (), {})()
            mock_instance.read_file_as_json = lambda **kwargs: []
            return mock_instance
        
        monkeypatch.setattr('congregate.cli.stage_wave.WaveSpreadsheetHandler', mock_wsh_constructor)
        monkeypatch.setattr('congregate.cli.stage_wave.rewrite_list_into_dict', lambda x, y, **kwargs: x)
        
        wave_stage_cli.config.wave_spreadsheet_path = "/valid/path"
        wave_stage_cli.config.wave_spreadsheet_columns = ["col1", "col2"]
        wave_stage_cli.the_number_of_instance = lambda scm_source=None: 0
        wave_stage_cli.open_projects_file = lambda scm_source=None: []
        wave_stage_cli.open_users_file = lambda scm_source=None: []
        wave_stage_cli.open_groups_file = lambda scm_source=None: []
        wave_stage_cli.check_spreadsheet_data = lambda: None
        
        with pytest.raises(SystemExit) as exc_info:
            wave_stage_cli.stage_wave("wave1")
        
        assert exc_info.value.code == os.EX_CONFIG
        assert any("No rows for wave wave1 found" in call for call in wave_stage_cli.log.error_calls)

    def test_stage_wave_with_override_flag(self, wave_stage_cli, monkeypatch):
        """Test stage_wave method when override flag is set."""
        monkeypatch.setattr('os.path.isfile', lambda x: True)
        monkeypatch.setattr('congregate.cli.stage_wave.rewrite_list_into_dict', lambda x, y, **kwargs: {})
        
        mock_wsh_instance = type('MockWaveSpreadsheetHandler', (), {})()
        mock_wsh_instance.read_file_as_json = lambda **kwargs: [
            {"Source Project ID": "123", "Override": True}
        ]
        
        def mock_wsh_constructor(*args, **kwargs):
            return mock_wsh_instance
        
        monkeypatch.setattr('congregate.cli.stage_wave.WaveSpreadsheetHandler', mock_wsh_constructor)
        
        wave_stage_cli.config.wave_spreadsheet_path = "/valid/path"
        wave_stage_cli.config.wave_spreadsheet_columns = ["col1", "col2"]
        wave_stage_cli.config.wave_spreadsheet_column_mapping = {}
        wave_stage_cli.the_number_of_instance = lambda scm_source=None: 0
        wave_stage_cli.open_projects_file = lambda scm_source=None: []
        wave_stage_cli.open_users_file = lambda scm_source=None: []
        wave_stage_cli.open_groups_file = lambda scm_source=None: []
        wave_stage_cli.check_spreadsheet_data = lambda: None
        
        # Mock pcli.stage_data to capture what gets staged
        stage_data_calls = []
        def mock_stage_data(ids, *args, **kwargs):
            stage_data_calls.append(ids)
        wave_stage_cli.pcli.stage_data = mock_stage_data
        
        wave_stage_cli.stage_wave("wave1")
        
        # Should log error about override feature not implemented
        assert any("OVERRIDE is flagged True" in call for call in wave_stage_cli.log.error_calls)
        # Should stage empty list since override row is skipped
        assert len(stage_data_calls) == 1
        assert stage_data_calls[0] == []

    def test_stage_wave_success_with_valid_data(self, wave_stage_cli, monkeypatch):
        """Test stage_wave method with valid data and successful execution."""
        monkeypatch.setattr('os.path.isfile', lambda x: True)
        monkeypatch.setattr('congregate.cli.stage_wave.rewrite_list_into_dict', lambda x, y, **kwargs: {})
        
        mock_wsh_instance = type('MockWaveSpreadsheetHandler', (), {})()
        mock_wsh_instance.read_file_as_json = lambda **kwargs: [
            {"Source Project ID": "123", "Override": False},
            {"Source Project ID": "456"}  # No Override key (falsy)
        ]
        
        def mock_wsh_constructor(*args, **kwargs):
            return mock_wsh_instance
        
        monkeypatch.setattr('congregate.cli.stage_wave.WaveSpreadsheetHandler', mock_wsh_constructor)
        
        wave_stage_cli.config.wave_spreadsheet_path = "/valid/path"
        wave_stage_cli.config.wave_spreadsheet_columns = ["col1", "col2"]
        wave_stage_cli.config.wave_spreadsheet_column_mapping = {}
        wave_stage_cli.the_number_of_instance = lambda scm_source=None: 0
        wave_stage_cli.open_projects_file = lambda scm_source=None: []
        wave_stage_cli.open_users_file = lambda scm_source=None: []
        wave_stage_cli.open_groups_file = lambda scm_source=None: []
        wave_stage_cli.check_spreadsheet_data = lambda: None
        
        # Mock pcli.stage_data to capture what gets staged  
        stage_data_calls = []
        def mock_stage_data(ids, *args, **kwargs):
            stage_data_calls.append(ids)
        wave_stage_cli.pcli.stage_data = mock_stage_data
        
        wave_stage_cli.stage_wave("wave1")
        
        # Should stage both project IDs as strings
        assert len(stage_data_calls) == 1
        assert stage_data_calls[0] == ["123", "456"]

    def test_check_spreadsheet_kv_all_items_exist(self, wave_stage_cli):
        """Test check_spreadsheet_kv when all mapping items exist in columns"""
        mapping = {'col1': 'property1', 'col2': 'property2', 'col3': 'property3'}
        columns = ['col1', 'col2', 'col3', 'col4']
        
        result = wave_stage_cli.check_spreadsheet_kv(mapping, columns)
        
        assert result is True

    def test_check_spreadsheet_kv_some_items_missing(self, wave_stage_cli):
        """Test check_spreadsheet_kv when some mapping items are missing from columns"""
        mapping = {'col1': 'property1', 'col2': 'property2', 'col3': 'property3'}
        columns = ['col1', 'col3']  # col2 is missing
        
        result = wave_stage_cli.check_spreadsheet_kv(mapping, columns)
        
        assert result is False

    def test_check_spreadsheet_kv_no_items_exist(self, wave_stage_cli):
        """Test check_spreadsheet_kv when no mapping items exist in columns"""
        mapping = {'col1': 'property1', 'col2': 'property2', 'col3': 'property3'}
        columns = ['col4', 'col5', 'col6']
        
        result = wave_stage_cli.check_spreadsheet_kv(mapping, columns)
        
        assert result is False

    def test_check_spreadsheet_kv_empty_mapping(self, wave_stage_cli):
        """Test check_spreadsheet_kv with empty mapping"""
        mapping = {}
        columns = ['col1', 'col2', 'col3']
        
        result = wave_stage_cli.check_spreadsheet_kv(mapping, columns)
        
        assert result is True  # 0 == len({}) is True

    def test_check_spreadsheet_kv_empty_columns(self, wave_stage_cli):
        """Test check_spreadsheet_kv with empty columns"""
        mapping = {'col1': 'property1', 'col2': 'property2'}
        columns = []
        
        result = wave_stage_cli.check_spreadsheet_kv(mapping, columns)
        
        assert result is False  # 0 != len({'col1': 'property1', 'col2': 'property2'})

    def test_check_spreadsheet_kv_both_empty(self, wave_stage_cli):
        """Test check_spreadsheet_kv with both mapping and columns empty"""
        mapping = {}
        columns = []
        
        result = wave_stage_cli.check_spreadsheet_kv(mapping, columns)
        
        assert result is True  # 0 == len({}) is True

    def test_check_spreadsheet_data_all_valid(self, wave_stage_cli):
        """Test check_spreadsheet_data when all configuration is valid"""
        wave_stage_cli.config.wave_spreadsheet_column_to_project_property_mapping = {'col1': 'prop1', 'col2': 'prop2'}
        wave_stage_cli.config.wave_spreadsheet_columns = ['col1', 'col2', 'col3']
        
        wave_stage_cli.check_spreadsheet_data()
        
        # Should not log any warnings
        assert len(wave_stage_cli.log.warning_calls) == 0

    def test_check_spreadsheet_data_missing_mapping(self, wave_stage_cli):
        """Test check_spreadsheet_data when mapping configuration is missing"""
        wave_stage_cli.config.wave_spreadsheet_column_to_project_property_mapping = None
        wave_stage_cli.config.wave_spreadsheet_columns = ['col1', 'col2']
        
        wave_stage_cli.check_spreadsheet_data()
        
        expected_msg = "No 'wave_spreadsheet_column_to_project_property_mapping' field in congregate.conf"
        assert expected_msg in wave_stage_cli.log.warning_calls

    def test_check_spreadsheet_data_empty_mapping(self, wave_stage_cli):
        """Test check_spreadsheet_data when mapping configuration is empty"""
        wave_stage_cli.config.wave_spreadsheet_column_to_project_property_mapping = {}
        wave_stage_cli.config.wave_spreadsheet_columns = ['col1', 'col2']
        
        wave_stage_cli.check_spreadsheet_data()
        
        expected_msg = "No 'wave_spreadsheet_column_to_project_property_mapping' field in congregate.conf"
        assert expected_msg in wave_stage_cli.log.warning_calls

    def test_check_spreadsheet_data_missing_columns(self, wave_stage_cli):
        """Test check_spreadsheet_data when columns configuration is missing"""
        wave_stage_cli.config.wave_spreadsheet_column_to_project_property_mapping = {'col1': 'prop1', 'col2': 'prop2'}
        wave_stage_cli.config.wave_spreadsheet_columns = None
        
        wave_stage_cli.check_spreadsheet_data()
        
        expected_msg = "No 'wave_spreadsheet_columns' field in congregate.conf"
        assert expected_msg in wave_stage_cli.log.warning_calls

    def test_check_spreadsheet_data_empty_columns(self, wave_stage_cli):
        """Test check_spreadsheet_data when columns configuration is empty"""
        wave_stage_cli.config.wave_spreadsheet_column_to_project_property_mapping = {'col1': 'prop1', 'col2': 'prop2'}
        wave_stage_cli.config.wave_spreadsheet_columns = []
        
        wave_stage_cli.check_spreadsheet_data()
        
        expected_msg = "No 'wave_spreadsheet_columns' field in congregate.conf"
        assert expected_msg in wave_stage_cli.log.warning_calls

    def test_check_spreadsheet_data_mismatch_warning(self, wave_stage_cli):
        """Test check_spreadsheet_data when there's a mismatch between mapping and columns"""
        wave_stage_cli.config.wave_spreadsheet_column_to_project_property_mapping = {'col1': 'prop1', 'col2': 'prop2', 'col3': 'prop3'}
        wave_stage_cli.config.wave_spreadsheet_columns = ['col1', 'col2']  # col3 missing
        
        wave_stage_cli.check_spreadsheet_data()
        
        # Should log the mismatch warning
        expected_msg = "Mismatch between keys in wave_spreadsheet_columns and wave_spreadsheet_column_to_project_property_mapping"
        assert expected_msg in wave_stage_cli.log.warning_calls

    def test_check_spreadsheet_data_case_sensitive_columns(self, wave_stage_cli):
        """Test check_spreadsheet_data with case-sensitive column matching"""
        wave_stage_cli.config.wave_spreadsheet_column_to_project_property_mapping = {'Col1': 'prop1', 'col2': 'prop2'}
        wave_stage_cli.config.wave_spreadsheet_columns = ['col1', 'col2']  # Different case for Col1
        
        wave_stage_cli.check_spreadsheet_data()
        
        # Should log mismatch warning due to case sensitivity
        expected_msg = "Mismatch between keys in wave_spreadsheet_columns and wave_spreadsheet_column_to_project_property_mapping"
        assert expected_msg in wave_stage_cli.log.warning_calls

    def test_check_spreadsheet_data_duplicate_columns(self, wave_stage_cli):
        """Test check_spreadsheet_data with duplicate columns"""
        wave_stage_cli.config.wave_spreadsheet_column_to_project_property_mapping = {'col1': 'prop1', 'col2': 'prop2'}
        wave_stage_cli.config.wave_spreadsheet_columns = ['col1', 'col2']
        
        wave_stage_cli.check_spreadsheet_data()
        
        # Should not log mismatch warning since there are no duplicates in the dictionary keys
        expected_msg = "Mismatch between keys in wave_spreadsheet_columns and wave_spreadsheet_column_to_project_property_mapping"
        assert expected_msg not in wave_stage_cli.log.warning_calls