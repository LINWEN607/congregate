import unittest
import responses
from pytest import mark
from unittest import mock
from gitlab_ps_utils.api import GitLabApi
from congregate.migration.gitlab.compare import CompareClient
from congregate.tests.mockapi.gitlab.groups import MockGroupsApi
from congregate.tests.mockapi.gitlab.users import MockUsersApi
from gitlab_ps_utils.dict_utils import rewrite_list_into_dict
from congregate.helpers.configuration_validator import ConfigurationValidator


@mark.unit_test
class CompareTests(unittest.TestCase):
    def setUp(self):
        self.compare = CompareClient()
        self.groups = MockGroupsApi()
        self.users = MockUsersApi()

    @mock.patch.object(CompareClient, "load_group_data")
    @mock.patch.object(ConfigurationValidator,
                       'dstn_parent_id', new_callable=mock.PropertyMock)
    @mock.patch.object(ConfigurationValidator, 'source_token',
                       new_callable=mock.PropertyMock)
    @mock.patch.object(ConfigurationValidator,
                       'destination_token', new_callable=mock.PropertyMock)
    def test_compare_groups(self, dest_token, src_token,
                            parent_id, group_data):
        dest_token.return_value = "test"
        src_token.return_value = "test"
        parent_id.return_value = None
        source_groups = self.groups.get_all_groups_list()
        destination_groups = self.mock_destination_ids()
        group_data.side_effect = [destination_groups, source_groups]
        expected_results = {
            'Total groups in destination instance': 4,
            'Total groups in source instance': 4,
            'results': {
                'foo-bar-2': {
                    'path': True,
                    'members': {
                        'member_counts_match': True,
                        'destination_member_count': 2,
                        'unknown added members': {},
                        'missing members': {},
                        'source_member_count': 2
                    }
                },
                'foo-bar-3': {
                    'path': True,
                    'members': {
                        'member_counts_match': True,
                        'destination_member_count': 2,
                        'unknown added members': {},
                        'missing members': {},
                        'source_member_count': 2
                    }
                },
                'foo-bar': {
                    'path': True,
                    'members': {
                        'member_counts_match': True,
                        'destination_member_count': 2,
                        'unknown added members': {},
                        'missing members': {},
                        'source_member_count': 2
                    }
                }
            }
        }

        actual_results, actual_unknown_users = self.compare.create_group_migration_results()
        self.assertEqual(actual_results, expected_results)
        self.assertEqual(actual_unknown_users, {})

    def test_generate_diff(self):
        diff_one = "ABC"
        diff_two = "DEF"
        expected = {
            "expected": diff_one,
            "actual": diff_two
        }
        actual = self.compare.generate_diff(diff_one, diff_two)
        self.assertEqual(expected, actual)

    def test_generate_matching_diff(self):
        diff_one = "ABC"
        diff_two = "ABC"
        actual = self.compare.generate_diff(diff_one, diff_two)
        expected = True
        self.assertEqual(expected, actual)

    @mock.patch.object(ConfigurationValidator,
                       'dstn_parent_id', new_callable=mock.PropertyMock)
    def test_compare_members_different_usernames_same_ids(self, parent_id):
        parent_id.return_value = None
        source_groups = self.groups.get_all_groups_list()
        destination_groups = self.mock_destination_usernames()
        shared_key = "full_path"
        rewritten_destination_groups = rewrite_list_into_dict(
            destination_groups, shared_key)
        rewritten_source_groups = rewrite_list_into_dict(
            source_groups, shared_key, prefix="")
        expected = {
            "foo-bar-2": {
                "path": True,
                "members": {
                    "member_counts_match": True,
                    "destination_member_count": 2,
                    "unknown added members": {
                        "not-smart4": {
                            "username": "not-smart4",
                            "access_level": 30,
                            "state": "active",
                            "name": "User smart4",
                            "avatar_url": "https://secure.gravatar.com/avatar/77b6da6e1b9aa2527600bc7727f5bad8?s=80&d=identicon",
                            "id": 286,
                            "expires_at": None
                        },
                        "not-smart3": {
                            "username": "not-smart3",
                            "access_level": 50,
                            "state": "active",
                            "name": "User smart3",
                            "avatar_url": "https://secure.gravatar.com/avatar/d549ee47080f3512a835905895c46545?s=80&d=identicon",
                            "id": 285,
                            "expires_at": None
                        }
                    },
                    "missing members": {
                        "smart4": {
                            "username": "smart4",
                            "access_level": 30,
                            "state": "active",
                            "name": "User smart4",
                            "avatar_url": "https://secure.gravatar.com/avatar/77b6da6e1b9aa2527600bc7727f5bad8?s=80&d=identicon",
                            "id": 286,
                            "expires_at": None
                        },
                        "smart3": {
                            "username": "smart3",
                            "access_level": 50,
                            "state": "active",
                            "name": "User smart3",
                            "avatar_url": "https://secure.gravatar.com/avatar/d549ee47080f3512a835905895c46545?s=80&d=identicon",
                            "id": 285,
                            "expires_at": None
                        }
                    },
                    "source_member_count": 2
                }
            },
            "foo-bar-3": {
                "path": True,
                "members": {
                    "member_counts_match": True,
                    "destination_member_count": 2,
                    "unknown added members": {
                        "not-smart4": {
                            "username": "not-smart4",
                            "access_level": 30,
                            "state": "active",
                            "name": "User smart4",
                            "avatar_url": "https://secure.gravatar.com/avatar/77b6da6e1b9aa2527600bc7727f5bad8?s=80&d=identicon",
                            "id": 286,
                            "expires_at": None
                        },
                        "not-smart3": {
                            "username": "not-smart3",
                            "access_level": 50,
                            "state": "active",
                            "name": "User smart3",
                            "avatar_url": "https://secure.gravatar.com/avatar/d549ee47080f3512a835905895c46545?s=80&d=identicon",
                            "id": 285,
                            "expires_at": None
                        }
                    },
                    "missing members": {
                        "smart4": {
                            "username": "smart4",
                            "access_level": 30,
                            "state": "active",
                            "name": "User smart4",
                            "avatar_url": "https://secure.gravatar.com/avatar/77b6da6e1b9aa2527600bc7727f5bad8?s=80&d=identicon",
                            "id": 286,
                            "expires_at": None
                        },
                        "smart3": {
                            "username": "smart3",
                            "access_level": 50,
                            "state": "active",
                            "name": "User smart3",
                            "avatar_url": "https://secure.gravatar.com/avatar/d549ee47080f3512a835905895c46545?s=80&d=identicon",
                            "id": 285,
                            "expires_at": None
                        }
                    },
                    "source_member_count": 2
                }
            },
            "foo-bar": {
                "path": True,
                "members": {
                    "member_counts_match": True,
                    "destination_member_count": 2,
                    "unknown added members": {
                        "not-smart4": {
                            "username": "not-smart4",
                            "access_level": 30,
                            "state": "active",
                            "name": "User smart4",
                            "avatar_url": "https://secure.gravatar.com/avatar/77b6da6e1b9aa2527600bc7727f5bad8?s=80&d=identicon",
                            "id": 286,
                            "expires_at": None
                        },
                        "not-smart3": {
                            "username": "not-smart3",
                            "access_level": 50,
                            "state": "active",
                            "name": "User smart3",
                            "avatar_url": "https://secure.gravatar.com/avatar/d549ee47080f3512a835905895c46545?s=80&d=identicon",
                            "id": 285,
                            "expires_at": None
                        }
                    },
                    "missing members": {
                        "smart4": {
                            "username": "smart4",
                            "access_level": 30,
                            "state": "active",
                            "name": "User smart4",
                            "avatar_url": "https://secure.gravatar.com/avatar/77b6da6e1b9aa2527600bc7727f5bad8?s=80&d=identicon",
                            "id": 286,
                            "expires_at": None
                        },
                        "smart3": {
                            "username": "smart3",
                            "access_level": 50,
                            "state": "active",
                            "name": "User smart3",
                            "avatar_url": "https://secure.gravatar.com/avatar/d549ee47080f3512a835905895c46545?s=80&d=identicon",
                            "id": 285,
                            "expires_at": None
                        }
                    },
                    "source_member_count": 2
                }
            }
        }
        actual = self.compare.compare_groups(
            rewritten_source_groups, rewritten_destination_groups)
        self.assertEqual(expected, actual)

    # pylint: disable=no-member

    # pylint: disable=no-member

    @responses.activate
    # pylint: enable=no-member
    @mock.patch.object(ConfigurationValidator,
                       'destination_token', new_callable=mock.PropertyMock)
    @mock.patch.object(GitLabApi, "generate_v4_request_url")
    def test_unknown_user_snapshot(self, url, dest_token):
        dest_token.return_value = "test"
        dummy_members = [{
            "members": [
                self.users.get_dummy_user()
            ]
        }]
        fake_new_user = self.users.get_dummy_user()
        fake_new_user["id"] = 1234
        url_value = "https://gitlab.com/api/v4/users/1"
        url.return_value = url_value
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                      json=self.users.get_user_404(), status=404)
        # pylint: enable=no-member
        expected = {
            27: {
                "message": "404 User Not Found"
            }
        }
        actual = self.compare.generate_user_snapshot_map(dummy_members)
        self.assertEqual(expected, actual)

    def mock_destination_ids(self):
        mock_destination = self.groups.get_all_groups_list()
        for group in mock_destination:
            for member in group["members"]:
                member["id"] = member.get("id") + 10
        return mock_destination

    def mock_destination_usernames(self):
        mock_destination = self.groups.get_all_groups_list()
        for group in mock_destination:
            for member in group["members"]:
                member["username"] = "not-" + member.get("username")
        return mock_destination
