import unittest
import mock
import json
from congregate.migration.gitlab.compare import CompareClient
from congregate.helpers.mockapi.groups import MockGroupsApi
from congregate.migration.gitlab.groups import GroupsClient
from congregate.helpers.misc_utils import rewrite_list_into_dict

class CompareClientTests(unittest.TestCase):
    def setUp(self):
        self.compare = CompareClient()
        self.groups = MockGroupsApi()

    def test_generate_diff(self):
        diff_one = "ABC"
        diff_two = "DEF"
        expected = {
            "expected": diff_one,
            "actual": diff_two
        }
        actual = self.compare.generate_diff(diff_one, diff_two)

        self.assertItemsEqual(expected, actual)

    def test_generate_matching_diff(self):
        diff_one = "ABC"
        diff_two = "ABC"
        actual = self.compare.generate_diff(diff_one, diff_two)
        expected = True
        self.assertEqual(expected, actual)

    def test_compare_members_different_ids_same_usernames(self):
        source_groups = self.groups.get_all_groups_list()
        destination_groups = self.mock_destination_ids()
        shared_key = "full_path"
        rewritten_destination_groups = rewrite_list_into_dict(destination_groups, shared_key)
        rewritten_source_groups = rewrite_list_into_dict(source_groups, shared_key, prefix="")
        expected = {
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
                    'missingmembers': {},
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
        actual = self.compare.compare_groups(rewritten_source_groups, rewritten_destination_groups)
        self.assertEqual(sorted(expected), sorted(actual))

    def test_compare_members_different_usernames_same_ids(self):
        source_groups = self.groups.get_all_groups_list()
        destination_groups = self.mock_destination_usernames()
        shared_key = "full_path"
        rewritten_destination_groups = rewrite_list_into_dict(destination_groups, shared_key)
        rewritten_source_groups = rewrite_list_into_dict(source_groups, shared_key, prefix="")
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
                            "web_url": "http://demo.tanuki.cloud/smart4",
                            "name": "User smart4",
                            "avatar_url": "https://secure.gravatar.com/avatar/77b6da6e1b9aa2527600bc7727f5bad8?s=80&d=identicon",
                            "id": 286,
                            "expires_at": None
                        },
                        "not-smart3": {
                            "username": "not-smart3",
                            "access_level": 50,
                            "state": "active",
                            "web_url": "http://demo.tanuki.cloud/smart3",
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
                            "web_url": "http://demo.tanuki.cloud/smart4",
                            "name": "User smart4",
                            "avatar_url": "https://secure.gravatar.com/avatar/77b6da6e1b9aa2527600bc7727f5bad8?s=80&d=identicon",
                            "id": 286,
                            "expires_at": None
                        },
                        "smart3": {
                            "username": "smart3",
                            "access_level": 50,
                            "state": "active",
                            "web_url": "http://demo.tanuki.cloud/smart3",
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
                            "web_url": "http://demo.tanuki.cloud/smart4",
                            "name": "User smart4",
                            "avatar_url": "https://secure.gravatar.com/avatar/77b6da6e1b9aa2527600bc7727f5bad8?s=80&d=identicon",
                            "id": 286,
                            "expires_at": None
                        },
                        "not-smart3": {
                            "username": "not-smart3",
                            "access_level": 50,
                            "state": "active",
                            "web_url": "http://demo.tanuki.cloud/smart3",
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
                            "web_url": "http://demo.tanuki.cloud/smart4",
                            "name": "User smart4",
                            "avatar_url": "https://secure.gravatar.com/avatar/77b6da6e1b9aa2527600bc7727f5bad8?s=80&d=identicon",
                            "id": 286,
                            "expires_at": None
                        },
                        "smart3": {
                            "username": "smart3",
                            "access_level": 50,
                            "state": "active",
                            "web_url": "http://demo.tanuki.cloud/smart3",
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
                            "web_url": "http://demo.tanuki.cloud/smart4",
                            "name": "User smart4",
                            "avatar_url": "https://secure.gravatar.com/avatar/77b6da6e1b9aa2527600bc7727f5bad8?s=80&d=identicon",
                            "id": 286,
                            "expires_at": None
                        },
                        "not-smart3": {
                            "username": "not-smart3",
                            "access_level": 50,
                            "state": "active",
                            "web_url": "http://demo.tanuki.cloud/smart3",
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
                            "web_url": "http://demo.tanuki.cloud/smart4",
                            "name": "User smart4",
                            "avatar_url": "https://secure.gravatar.com/avatar/77b6da6e1b9aa2527600bc7727f5bad8?s=80&d=identicon",
                            "id": 286,
                            "expires_at": None
                        },
                        "smart3": {
                            "username": "smart3",
                            "access_level": 50,
                            "state": "active",
                            "web_url": "http://demo.tanuki.cloud/smart3",
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
        actual = self.compare.compare_groups(rewritten_source_groups, rewritten_destination_groups)
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
