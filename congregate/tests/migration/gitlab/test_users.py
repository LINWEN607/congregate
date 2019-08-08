import unittest
import mock
import json
import responses
from congregate.helpers.mockapi.users import MockUsersApi
from congregate.migration.gitlab.api.users import UsersApi
from congregate.migration.gitlab.users import UsersClient

mock_users = MockUsersApi()
users = UsersClient()

# pylint: disable=no-member
@responses.activate
# pylint: enable=no-member
@mock.patch("congregate.helpers.api.generate_v4_request_url")
def test_find_user_by_email_comparison_incorrect_user(url):
    url_value = "https://gitlabsource.com/api/v4/users/5"
    url.return_value = url_value
    # pylint: disable=no-member
    responses.add(responses.GET, url_value,
                  json=mock_users.get_user_404(), status=404)
    # pylint: enable=no-member
    actual = users.find_user_by_email_comparison(5)
    expected = None
    assert expected == actual


# pylint: disable=no-member
@responses.activate
# pylint: enable=no-member
@mock.patch("congregate.helpers.api.generate_v4_request_url")
@mock.patch.object(UsersApi, "search_for_user_by_email")
def test_find_user_by_email_comparison_found_user(search, url):
    url_value = "https://gitlabsource.com/api/v4/users/5"
    url.return_value = url_value
    # pylint: disable=no-member
    responses.add(responses.GET, url_value,
                  json=mock_users.get_dummy_user(), status=200)
    # pylint: enable=no-member
    search.return_value = [mock_users.get_dummy_user()]
    actual = users.find_user_by_email_comparison(5)
    expected = mock_users.get_dummy_user()
    assert expected == actual


@mock.patch.object(UsersApi, "search_for_user_by_email")
def test_user_exists_true(search):
    search.return_value = [mock_users.get_dummy_user()]
    old_user = {
        "username": "jdoe"
    }
    actual = users.username_exists(old_user)
    expected = True
    assert expected == actual

@mock.patch.object(UsersApi, "search_for_user_by_email")
def test_user_exists_false(search):
    search.return_value = [mock_users.get_dummy_user()]
    old_user = {
        "username": "notjdoe"
    }
    actual = users.username_exists(old_user)
    expected = False
    assert expected == actual

@mock.patch.object(UsersApi, "search_for_user_by_email")
def test_user_exists_over_100(search):
    dummy_large_list = []
    for _ in range(0, 105):
        dummy_large_list.append(mock_users.get_dummy_user())
    search.return_value = dummy_large_list
    old_user = {
        "username": "notjdoe"
    }
    actual = users.username_exists(old_user)
    expected = False
    assert expected == actual

@mock.patch.object(UsersApi, "search_for_user_by_email")
def test_user_exists_no_results(search):
    old_user = {
        "username": "notjdoe"
    }
    search.return_value = []
    actual = users.username_exists(old_user)
    expected = False
    assert expected == actual

@mock.patch.object(UsersApi, "search_for_user_by_email")
def test_user_email_exists_true(search):
    search.return_value = [mock_users.get_dummy_user()]
    old_user = {
        "email": "jdoe@email.com"
    }
    actual = users.user_email_exists(old_user)
    expected = True
    assert expected == actual

@mock.patch.object(UsersApi, "search_for_user_by_email")
def test_user_email_exists_false(search):
    search.return_value = [mock_users.get_dummy_user()]
    old_user = {
        "email": "notjdoe@email.com"
    }
    actual = users.user_email_exists(old_user)
    expected = False
    assert expected == actual

@mock.patch.object(UsersApi, "search_for_user_by_email")
def test_user_email_exists_over_100(search):
    dummy_large_list = []
    for _ in range(0, 105):
        dummy_large_list.append(mock_users.get_dummy_user())
    search.return_value = dummy_large_list
    old_user = {
        "email": "notjdoe@email.com"
    }
    actual = users.user_email_exists(old_user)
    expected = False
    assert expected == actual

@mock.patch.object(UsersApi, "search_for_user_by_email")
def test_user_email_exists_no_results(search):
    old_user = {
        "email": "notjdoe@email.com"
    }
    search.return_value = []
    actual = users.user_email_exists(old_user)
    expected = False
    assert expected == actual

