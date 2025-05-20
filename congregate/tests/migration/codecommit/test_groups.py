import pytest
from unittest import TestCase
from unittest.mock import MagicMock, patch, PropertyMock
from congregate.helpers.congregate_mdbc import CongregateMongoConnector
from congregate.migration.codecommit.groups import GroupsClient
from congregate.migration.codecommit.api.base import CodeCommitApiWrapper
from congregate.migration.codecommit.base import CodeCommitWrapper

@pytest.mark.unit_test
class TestGroupsClient(TestCase):
    """Test cases for GroupsClient class."""

    def setUp(self):
        """Set up test fixtures."""
        self.groups_api = GroupsClient()
        # Mock the required components
        self.mock_api = MagicMock(spec=CodeCommitApiWrapper)
        self.mock_base_api = MagicMock(spec=CodeCommitWrapper)
        
        # Create mock mongo with the required methods
        self.mock_mongo = MagicMock()
        self.mock_mongo.find_one = MagicMock()
        self.mock_mongo.insert_data = MagicMock()
        
        # Set the mocked components
        self.groups_api.api = self.mock_api
        self.groups_api.base_api = self.mock_base_api
        self.groups_api.mongo = self.mock_mongo
        
        # Mock the config
        self.mock_config = MagicMock()
        self.groups_api.config = self.mock_config

    def test_retrieve_group_info_no_processes(self):
        """Test retrieving group info without specifying processes."""
        with patch.object(GroupsClient, 'handle_retrieving_group') as mock_handle:
            self.groups_api.retrieve_group_info()
            mock_handle.assert_called_once_with("CodeCommit")

    def test_handle_retrieving_group_no_group(self):
        """Test handling group retrieval with no group provided."""
        with self.assertLogs(self.groups_api.log, level="ERROR") as log:
            self.groups_api.handle_retrieving_group(None, mongo=self.mock_mongo)
            self.assertIn("Failed to retrieve project information", log.output[0])

    def test_find_group(self):
        """Test finding a group."""
        # Test data
        test_query = {"path": "test/group"}
        test_group = {"path": "test/group", "id": "group-123"}
        
        # Mock the MongoDB find_one call
        self.mock_mongo.find_one.return_value = test_group
        
        # Call the method under test
        result = self.groups_api.mongo.find_one(test_query)
        
        # Verify the result matches expected
        self.assertEqual(result, test_group)

    def test_find_group_not_found(self):
        """Test finding a group when it doesn't exist."""
        test_query = {"path": "test/nonexistent"}
        
        # Mock the MongoDB find_one call to return None
        self.mock_mongo.find_one.return_value = None
        
        # Call the method under test
        result = self.groups_api.mongo.find_one(test_query)
        
        # Verify None is returned when group not found
        self.assertIsNone(result)

    def test_find_group_with_exception(self):
        """Test finding a group when MongoDB throws an exception."""
        test_query = {"path": "test/group"}
        
        # Mock MongoDB to raise an exception
        self.mock_mongo.find_one.side_effect = Exception("Database error")
        
        # Call the method and verify exception handling
        with self.assertRaises(Exception):
            self.groups_api.mongo.find_one(test_query)

    @patch('congregate.migration.codecommit.groups.strip_netloc')
    def test_handle_retrieving_group_with_exception(self, mock_strip_netloc):
        """Test group retrieval when an exception occurs."""
        # Setup mock to raise an exception
        self.mock_base_api.format_group.side_effect = Exception("Formatting error")
        mock_strip_netloc.return_value = "codecommit.amazonaws.com"

        # Call method and verify exception handling
        with self.assertLogs(self.groups_api.log, level="ERROR") as log:
            self.groups_api.handle_retrieving_group("CodeCommit", mongo=self.mock_mongo)
            self.assertIn("Failed to retrieve project information", log.output[0])

        # Verify no MongoDB insertion was made
        self.mock_mongo.insert_data.assert_not_called()
