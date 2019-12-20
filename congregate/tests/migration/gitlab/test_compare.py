import mock
import responses
from congregate.migration.gitlab.compare import CompareClient
from congregate.tests.mockapi.groups import MockGroupsApi
from congregate.tests.mockapi.users import MockUsersApi
from congregate.helpers.misc_utils import rewrite_list_into_dict, deobfuscate
from congregate.helpers.configuration_validator import ConfigurationValidator

compare = CompareClient()
groups = MockGroupsApi()
users = MockUsersApi()

@mock.patch.object(CompareClient, "load_group_data")
@mock.patch.object(ConfigurationValidator, 'parent_id', new_callable=mock.PropertyMock)
def test_compare_groups(parent_id, group_data):
    parent_id.return_value = None
    source_groups = groups.get_all_groups_list()
    destination_groups = mock_destination_ids()
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
    
    with mock.patch('congregate.helpers.conf.deobfuscate', lambda x: ""):
        actual_results, actual_unknown_users = compare.create_group_migration_results()
    assert actual_results == expected_results
    assert actual_unknown_users == {}

def test_generate_diff():
    diff_one = "ABC"
    diff_two = "DEF"
    expected = {
        "expected": diff_one,
        "actual": diff_two
    }
    actual = compare.generate_diff(diff_one, diff_two)
    assert expected == actual

def test_generate_matching_diff():
    diff_one = "ABC"
    diff_two = "ABC"
    actual = compare.generate_diff(diff_one, diff_two)
    expected = True
    assert expected == actual

# def test_compare_members_different_ids_same_usernames():
#     source_groups = groups.get_all_groups_list()
#     destination_groups = mock_destination_ids()
#     shared_key = "full_path"
#     rewritten_destination_groups = rewrite_list_into_dict(destination_groups, shared_key)
#     rewritten_source_groups = rewrite_list_into_dict(source_groups, shared_key, prefix="")
#     expected = {
#         'foo-bar-2': {
#             'path': True,
#             'members': {
#                 'member_counts_match': True,
#                 'destination_member_count': 2,
#                 'unknown added members': {},
#                 'missing members': {},
#                 'source_member_count': 2
#             }
#         },
#         'foo-bar-3': {
#             'path': True,
#             'members': {
#                 'member_counts_match': True,
#                 'destination_member_count': 2,
#                 'unknown added members': {},
#                 'missingmembers': {},
#                 'source_member_count': 2
#             }
#         },
#         'foo-bar': {
#             'path': True,
#             'members': {
#                 'member_counts_match': True,
#                 'destination_member_count': 2,
#                 'unknown added members': {},
#                 'missing members': {},
#                 'source_member_count': 2
#             }
#         }
#     }
#     actual = compare.compare_groups(rewritten_source_groups, rewritten_destination_groups)
#     assert sorted(expected) == sorted(actual)

@mock.patch.object(ConfigurationValidator, 'parent_id', new_callable=mock.PropertyMock)
def test_compare_members_different_usernames_same_ids(parent_id):
    parent_id.return_value = None
    source_groups = groups.get_all_groups_list()
    destination_groups = mock_destination_usernames()
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
    actual = compare.compare_groups(rewritten_source_groups, rewritten_destination_groups)
    assert expected == actual

# pylint: disable=no-member
@responses.activate
# pylint: enable=no-member
@mock.patch("congregate.helpers.api.generate_v4_request_url")
def test_user_snapshot(url):
    dummy_members = [{
        "members": [
            users.get_dummy_user()
        ]
    }]
    fake_new_user = users.get_dummy_user()
    fake_new_user["id"] = 1234
    url_value = "https://gitlab.com/api/v4/users/1"
    url.return_value = url_value
    # pylint: disable=no-member
    responses.add(responses.GET, url_value,
                  json=fake_new_user, status=200)
    # pylint: enable=no-member
    expected = {
        27: {
            'email': 'jdoe@email.com', 
            'destination_instance_user_id': 1234, 
            'destination_instance_username': 'jdoe', 
            'source_instance_username': 'jdoe'
        }
    }
    with mock.patch('congregate.helpers.conf.deobfuscate', lambda x: ""):
        actual = compare.generate_user_snapshot_map(dummy_members)
    assert expected == actual

# pylint: disable=no-member
@responses.activate
# pylint: enable=no-member
@mock.patch("congregate.helpers.api.generate_v4_request_url")
def test_unknown_user_snapshot(url):
    dummy_members = [{
        "members": [
            users.get_dummy_user()
        ]
    }]
    fake_new_user = users.get_dummy_user()
    fake_new_user["id"] = 1234
    url_value = "https://gitlab.com/api/v4/users/1"
    url.return_value = url_value
    # pylint: disable=no-member
    responses.add(responses.GET, url_value,
                  json=users.get_user_404(), status=404)
    # pylint: enable=no-member
    expected = {
        27: {
            "message": "404 User Not Found"
        }
    }
    with mock.patch('congregate.helpers.conf.deobfuscate', lambda x: ""):
        actual = compare.generate_user_snapshot_map(dummy_members)
    assert expected == actual

def mock_destination_ids():
    mock_destination = groups.get_all_groups_list()
    for group in mock_destination:
        for member in group["members"]:
            member["id"] = member.get("id") + 10
    return mock_destination

def mock_destination_usernames():
    mock_destination = groups.get_all_groups_list()
    for group in mock_destination:
        for member in group["members"]:
            member["username"] = "not-" + member.get("username")
    return mock_destination
