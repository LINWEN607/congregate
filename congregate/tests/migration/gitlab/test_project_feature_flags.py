import warnings
import unittest
from unittest.mock import patch, PropertyMock, MagicMock

import pytest
from pytest import mark
from requests.exceptions import RequestException
from requests import Response

from congregate.migration.gitlab.api.project_feature_flags import ProjectFeatureFlagsApi
from congregate.migration.gitlab.project_feature_flags import ProjectFeatureFlagClient
from congregate.tests.mockapi.gitlab.project_feature_flags import MockProjectFeatureFlagApi
import logging

LOGGER = logging.getLogger(__name__)

@mark.unit_test
class ProjectFeatureFlagTests(unittest.TestCase):
    def setUp(self):
        self.project_feature_flag_api = ProjectFeatureFlagsApi()
        self.project_feature_flag_api.log.propagate = True
        self.project_feature_flag_client = ProjectFeatureFlagClient(False)
        self.project_feature_flag_client.log.propagate = True
        self.mock_project_feature_flag_api = MockProjectFeatureFlagApi()

    # Client tests
    @patch.object(ProjectFeatureFlagsApi, "get_all_project_feature_flags")
    def test_get_all_feature_flags_for_project_calls_api(self, mock_get_all_project_feature_flags):
        mock_get_all_project_feature_flags.return_value = self.mock_project_feature_flag_api.get_all_project_feature_flags()
        ret_val = self.project_feature_flag_client.get_all_feature_flags_for_project("", "", 1)
        self.assertEqual(len(ret_val), 3)

    def test_create_feature_flag_on_project_all_possible_none(self):
        mock = self.project_feature_flag_client.project_feature_flags_api
        mock.create_feature_flag = MagicMock(return_value="called")
        
        data_to_pass = self.mock_project_feature_flag_api.get_all_project_feature_flags()
        self.project_feature_flag_client.create_feature_flag_on_project("host", "token", 1, data_to_pass[0])
        mock.create_feature_flag.assert_called_with('host', 'token', 1, 'merge_train', 'new_version_flag', 'This feature is about merge train', True, [{'id': 1, 'name': 'userWithId', 'parameters': {'userIds': 'user1'}, 'scopes': [{'id': 1, 'environment_scope': 'production'}], 'user_list': None}])
        
        ## No description
        self.project_feature_flag_client.create_feature_flag_on_project("host", "token", 1, {
            "name":"merge_train",                                                                                
            "active": True,
            "version": "new_version_flag",
            "scopes":[],
            "strategies": []
            }
        )

        mock.create_feature_flag.assert_called_with('host', 'token', 1, 'merge_train', 'new_version_flag', None, True, [])

        ## No active
        self.project_feature_flag_client.create_feature_flag_on_project("host", "token", 1, {
            "name":"merge_train",                                                                                
            "description": "A description",
            "version": "new_version_flag",
            "scopes": [],
            "strategies": []
            }
        )

        mock.create_feature_flag.assert_called_with("host", "token", 1, "merge_train", "new_version_flag", "A description", None, [])

        ## No strategies
        self.project_feature_flag_client.create_feature_flag_on_project("host", "token", 1, {
            "name":"merge_train",                                                                                
            "version": "new_version_flag",
            "description": "A description",            
            "active": True,
            "strategies":[]
            }
        )

        mock.create_feature_flag.assert_called_with("host", "token", 1, "merge_train", "new_version_flag", "A description", True, [])

    def test_migrate_project_feature_flags_for_project_info_message_and_empty_return_on_empty(self):
        """
        Checks the return value is [] and that the proper message is logged if no FF are returned for the source project
        """
        with self.assertLogs(self.project_feature_flag_client.log.name) as captured:
            mock = self.project_feature_flag_client.project_feature_flags_api
            mock.get_all_project_feature_flags = MagicMock(return_value=[])
            self.project_feature_flag_client.migrate_project_feature_flags_for_project(1, 2)
            for out in captured.output:
                self.assertIn("No feature flags found for source_project_id 1", out)

    def test_rewrite_strategies_when_none_feature_flag(self):
        with self.assertLogs(self.project_feature_flag_client.log.name) as captured:
            self.project_feature_flag_client.rewrite_strategies(None, {"1":1})
            for out in captured.output:
                self.assertIn("FeatureFlag is None", out)

    def test_rewrite_strategies_when_no_strategies(self):
        with self.assertLogs(self.project_feature_flag_client.log.name) as captured:
            self.project_feature_flag_client.rewrite_strategies({"strategies": None}, {"1":1})
            for out in captured.output:
                self.assertIn("No strategies found for feature_flag: {'strategies': None}", out)

    def test_error_message_when_old_or_new_strategy_id_is_missing(self):
        with self.assertLogs(self.project_feature_flag_client.log.name) as captured:
            self.project_feature_flag_client.dry_run = False
            self.project_feature_flag_client.rewrite_strategies({"strategies": [{"user_list": {"notid":1}}]}, {"1":1})
            for out in captured.output:
                self.assertIn("Incomplete dictionary:\nstrategy: {'user_list': {'notid': 1}}\nuser_xid_conversion_dict: {'1': 1}",
                            out)

    def test_rewrite_strategies_when_none_user_xid_conversion_dict(self):
        with self.assertLogs(self.project_feature_flag_client.log.name) as captured:
            self.project_feature_flag_client.rewrite_strategies({"strategies": None}, None)
            self.assertIn("ERROR:congregate.helpers.base_class:user_xid_conversion_dict is None", captured.output)
