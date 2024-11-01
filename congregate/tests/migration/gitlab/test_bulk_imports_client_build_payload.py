from unittest import TestCase
from unittest.mock import Mock, patch

import pytest

from congregate.migration.gitlab.bulk_imports import BulkImportsClient
from congregate.migration.meta.api_models.bulk_import import BulkImportPayload


@pytest.mark.unit_test
class TestBulkImportsClientBuildPayload(TestCase):

    def client(self):
        client = BulkImportsClient()
        client.config = Mock()
        client.config.source_host = "https://source.gitlab.com"
        client.config.source_token = "test-token"
        client.config.dstn_parent_id = 42
        client.config.dstn_parent_group_path = "destination-group"
        client.log = Mock()
        return client

    def test_build_payload_invalid_entity_type(self):
        client = self.client()
        """Test handling of invalid entity type"""
        result = client.build_payload([], "invalid_type")

        assert result is None
        client.log.error.assert_called_once_with(
            "Unknown entity type invalid_type provided for staged data"
        )

    def test_build_payload_empty_data(self):
        client = self.client()

        """Test building payload with empty staged data"""
        with patch.object(client, 'subset_projects_staged', return_value={}):
            result = client.build_payload([], "group")

            assert isinstance(result, BulkImportPayload)
            assert len(result.entities) == 0
            assert result.configuration.url == "https://source.gitlab.com"
            assert result.configuration.access_token == "test-token"

    def test_build_payload_group_entity(self):
        client = self.client()

        """Test building payload with group entity"""
        staged_data = [{
            'full_path': 'group1',
            'path': 'group1',
            'name': 'Group 1'
        }]

        with patch.object(client, 'subset_projects_staged', return_value={}):
            with patch.object(client, 'parent_group_exists', return_value=False):
                result = client.build_payload(staged_data, "group")

                assert len(result.entities) == 1
                assert result.entities[0].source_type == "group_entity"
                assert result.entities[0].source_full_path == "group1"
                assert result.entities[0].destination_namespace == "destination-group"
                assert result.entities[0].destination_name == "Group 1"

    def test_build_payload_project_entity(self):
        client = self.client()

        """Test building payload with project entity"""
        staged_data = [{
            'path_with_namespace': 'group1/project1',
            'path': 'project1',
            'name': 'Project 1',
            'namespace': 'group1'
        }]

        with patch.object(client, 'subset_projects_staged', return_value={}):
            result = client.build_payload(staged_data, "project")

            assert len(result.entities) == 1
            assert result.entities[0].source_type == "project_entity"
            assert result.entities[0].source_full_path == "group1/project1"
            assert result.entities[0].destination_namespace == "destination-group/group1"
            assert result.entities[0].destination_name == "Project 1"

    def test_build_payload_with_subset_projects(self):
        client = self.client()
        """Test building payload with subset of projects in a group"""
        staged_data = [{
            'full_path': 'group1',
            'path': 'group1',
            'name': 'Group 1'
        }]

        subset_projects = {
            'group1': [{
                'path_with_namespace': 'group1/project1',
                'path': 'project1',
                'name': 'Project 1',
                'namespace': 'group1'
            }]
        }

        with patch.object(client, 'subset_projects_staged', return_value=subset_projects):
            with patch.object(client, 'parent_group_exists', return_value=False):
                result = client.build_payload(staged_data, "group")

                assert len(result.entities) == 2
                assert result.entities[0].source_type == "group_entity"
                assert result.entities[0].migrate_projects is False
                assert result.entities[1].source_type == "project_entity"

    def test_build_payload_skip_subgroup(self):
        client = self.client()

        """Test building payload with subgroup that should be skipped"""
        staged_data = [
            {
                'full_path': 'group1/subgroup1',
                'path': 'subgroup1',
                'name': 'Subgroup 1'
            }
        ]

        with patch.object(client, 'subset_projects_staged', return_value={}):
            with patch.object(client, 'parent_group_exists', return_value=True):
                result = client.build_payload(staged_data, "group")

                assert len(result.entities) == 0
