import unittest
import mock
import responses
import json
from congregate.tests.mockapi.users import MockUsersApi
from congregate.migration.gitlab.api.users import UsersApi
from congregate.migration.gitlab.users import UsersClient
from congregate.migration.gitlab.groups import GroupsApi


class UserTests(unittest.TestCase):
    def setUp(self):
        self.mock_users = MockUsersApi()
        self.users = UsersClient()

    # pylint: disable=no-member
    @responses.activate
    # pylint: enable=no-member
    @mock.patch("congregate.helpers.api.generate_v4_request_url")
    def test_find_user_by_email_comparison_incorrect_user(self, url):
        url_value = "https://gitlabsource.com/api/v4/users/5"
        url.return_value = url_value
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                    json=self.mock_users.get_user_404(), status=404)
        # pylint: enable=no-member
        actual = self.users.find_user_by_email_comparison_with_id(5)
        self.assertIsNone(actual)


    # pylint: disable=no-member
    @responses.activate
    # pylint: enable=no-member
    @mock.patch("congregate.helpers.api.generate_v4_request_url")
    @mock.patch.object(UsersApi, "search_for_user_by_email")
    def test_find_user_by_email_comparison_found_user(self, search, url):
        url_value = "https://gitlabsource.com/api/v4/users/5"
        url.return_value = url_value
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                    json=self.mock_users.get_dummy_user(), status=200)
        # pylint: enable=no-member
        search.return_value = [self.mock_users.get_dummy_user()]
        actual = self.users.find_user_by_email_comparison_with_id(5)
        expected = self.mock_users.get_dummy_user()
        self.assertDictEqual(expected, actual)

    @mock.patch.object(UsersClient, "is_username_group_name")
    @mock.patch.object(UsersApi, "search_for_user_by_username")
    def test_user_exists_true(self, search, users_client):
        users_client.return_value = False
        search.return_value = [self.mock_users.get_dummy_user()]
        old_user = {
            "username": "jdoe"
        }
        actual = self.users.username_exists(old_user)
        self.assertTrue(actual)

    @mock.patch.object(UsersClient, "is_username_group_name")
    @mock.patch.object(UsersApi, "search_for_user_by_username")
    def test_user_exists_false(self, search, users_client):
        users_client.return_value = False
        search.return_value = [self.mock_users.get_dummy_user()]
        old_user = {
            "username": "notjdoe"
        }
        actual = self.users.username_exists(old_user)
        self.assertFalse(actual)

    @mock.patch.object(UsersClient, "is_username_group_name")
    @mock.patch.object(UsersApi, "search_for_user_by_username")
    def test_user_exists_over_100(self, search, users_client):
        users_client.return_value = False
        dummy_large_list = []
        for _ in range(0, 105):
            dummy_large_list.append(self.mock_users.get_dummy_user())
        search.return_value = dummy_large_list
        old_user = {
            "username": "notjdoe"
        }
        actual = self.users.username_exists(old_user)
        self.assertFalse(actual)

    @mock.patch.object(UsersClient, "is_username_group_name")
    @mock.patch.object(UsersApi, "search_for_user_by_username")
    def test_user_exists_no_results(self, search, users_client):
        users_client.return_value = False
        old_user = {
            "username": "notjdoe"
        }
        search.return_value = []
        actual = self.users.username_exists(old_user)
        self.assertFalse(actual)

    @mock.patch.object(UsersApi, "search_for_user_by_email")
    def test_user_email_exists_true(self, search):
        search.return_value = [self.mock_users.get_dummy_user()]
        old_user = {
            "email": "jdoe@email.com"
        }
        actual = self.users.user_email_exists(old_user)
        self.assertTrue(actual)

    @mock.patch.object(UsersApi, "search_for_user_by_email")
    def test_user_email_exists_false(self, search):
        search.return_value = [self.mock_users.get_dummy_user()]
        old_user = {
            "email": "notjdoe@email.com"
        }
        actual = self.users.user_email_exists(old_user)
        self.assertFalse(actual)

    @mock.patch.object(UsersApi, "search_for_user_by_email")
    def test_user_email_exists_over_100(self, search):
        dummy_large_list = []
        for _ in range(0, 105):
            dummy_large_list.append(self.mock_users.get_dummy_user())
        search.return_value = dummy_large_list
        old_user = {
            "email": "notjdoe@email.com"
        }
        actual = self.users.user_email_exists(old_user)
        self.assertFalse(actual)

    @mock.patch.object(UsersApi, "search_for_user_by_email")
    def test_user_email_exists_no_results(self, search):
        old_user = {
            "email": "notjdoe@email.com"
        }
        search.return_value = []
        actual = self.users.user_email_exists(old_user)
        self.assertFalse(actual)

    # pylint: disable=no-member
    @responses.activate
    # pylint: enable=no-member
    @mock.patch('congregate.helpers.conf.ig.source_host', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.conf.ig.destination_host', new_callable=mock.PropertyMock)
    def test_update_users(self, destination, source):
        source.return_value = "https://gitlabsource.com"
        destination.return_value = "https://gitlabdestination.com"
        old_users = [
            {
                "name": "test-app",
                "members": self.mock_users.get_all_users_list()
            }
        ]
        new_users = self.mock_users.get_dummy_new_users()

        url_value = "https://gitlabsource.com/api/v4/users/1"
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                    json=self.mock_users.get_dummy_old_users()[0], status=200)
        # pylint: enable=no-member

        url_value = "https://gitlabdestination.com/api/v4/users/27"
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                    json=self.mock_users.get_dummy_new_users()[1], status=200)
        # pylint: enable=no-member

        url_value = "https://gitlabsource.com/api/v4/users/2"
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                    json=self.mock_users.get_dummy_old_users()[1], status=200)

        # pylint: enable=no-member
        url_value = "https://gitlabdestination.com/api/v4/users/28"
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                    json=self.mock_users.get_dummy_new_users()[0], status=200)
        # pylint: enable=no-member

        actual = self.users.update_users(old_users, new_users)

        expected = [
            {
                'name': 'test-app',
                'members': [
                    {
                        'username': 'raymond_smith',
                        'access_level': 30,
                        'state': 'active',
                        'avatar_url': 'https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon',
                        'web_url': 'http://192.168.1.8:3000/root',
                        'name': 'Raymond Smith',
                        'id': 28,
                        'expires_at': '2012-10-22T14:13:35Z'
                    },
                    {
                        'username': 'john_doe',
                        'access_level': 30,
                        'state': 'active',
                        'avatar_url': 'https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon',
                        'web_url': 'http://192.168.1.8:3000/root',
                        'name': 'John Doe',
                        'id': 27,
                        'expires_at': '2012-10-22T14:13:35Z'
                    }
                ]
            }
        ]

        self.assertListEqual(actual, expected)

    # pylint: disable=no-member
    @responses.activate
    # pylint: enable=no-member
    @mock.patch('congregate.helpers.conf.ig.source_host', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.conf.ig.destination_host', new_callable=mock.PropertyMock)
    def test_update_users_no_new_users(self, destination, source):
        source.return_value = "https://gitlabsource.com"
        destination.return_value = "https://gitlabdestination.com"
        old_users = [
            {
                "name": "test-app",
                "members": self.mock_users.get_all_users_list()
            }
        ]
        new_users = []

        url_value = "https://gitlabsource.com/api/v4/users/1"
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                    json=self.mock_users.get_dummy_old_users()[0], status=200)
        # pylint: enable=no-member
        url_value = "https://gitlabsource.com/api/v4/users/2"
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                    json=self.mock_users.get_dummy_old_users()[1], status=200)
        # pylint: enable=no-member
        url_value = "https://gitlabdestination.com/api/v4/users/27"
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                    json=self.mock_users.get_dummy_new_users()[0], status=200)
        # pylint: enable=no-member
        url_value = "https://gitlabdestination.com/api/v4/users/28"
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                    json=self.mock_users.get_dummy_new_users()[1], status=200)
        # pylint: enable=no-member
        url_value = "https://gitlabdestination.com/api/v4/user"
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                    json=self.mock_users.get_current_user(), status=200)
        # pylint: enable=no-member

        actual = self.users.update_users(old_users, new_users)

        expected = [
            {
                'name': 'test-app',
                'members': [
                    {
                        'username': 'raymond_smith',
                        'access_level': 30,
                        'state': 'active',
                        'avatar_url': 'https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon',
                        'web_url': 'http://192.168.1.8:3000/root',
                        'name': 'Raymond Smith',
                        'id': 1,
                        'expires_at': '2012-10-22T14:13:35Z'
                    },
                    {
                        'username': 'john_doe',
                        'access_level': 30,
                        'state': 'active',
                        'avatar_url': 'https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon',
                        'web_url': 'http://192.168.1.8:3000/root',
                        'name': 'John Doe',
                        'id': 1,
                        'expires_at': '2012-10-22T14:13:35Z'
                    }
                ]
            }
        ]

        self.assertListEqual(actual, expected)

    # pylint: disable=no-member
    @responses.activate
    # pylint: enable=no-member
    @mock.patch('congregate.helpers.conf.ig.source_host', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.conf.ig.destination_host', new_callable=mock.PropertyMock)
    def test_update_users_wrong_email(self, destination, source):
        source.return_value = "https://gitlabsource.com"
        destination.return_value = "https://gitlabdestination.com"
        old_users = [
            {
                "name": "test-app",
                "members": self.mock_users.get_all_users_list()
            }
        ]
        new_users = self.mock_users.get_dummy_new_users()

        wrong_raymond_smith = self.mock_users.get_dummy_new_users()[0]
        wrong_raymond_smith["email"] = "not_raymond_smith@email.com"

        url_value = "https://gitlabsource.com/api/v4/users/1"
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                    json=self.mock_users.get_dummy_old_users()[0], status=200)
        # pylint: enable=no-member
        url_value = "https://gitlabsource.com/api/v4/users/2"
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                    json=self.mock_users.get_dummy_old_users()[1], status=200)
        # pylint: enable=no-member
        url_value = "https://gitlabdestination.com/api/v4/users/27"
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                    json=self.mock_users.get_dummy_new_users()[1], status=200)
        # pylint: enable=no-member
        url_value = "https://gitlabdestination.com/api/v4/users/28"
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                    json=wrong_raymond_smith, status=200)
        # pylint: enable=no-member
        url_value = "https://gitlabdestination.com/api/v4/user"
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                    json=self.mock_users.get_current_user(), status=200)
        # pylint: enable=no-member

        actual = self.users.update_users(old_users, new_users)

        expected = [
            {
                'name': 'test-app',
                'members': [
                    {
                        'username': 'raymond_smith',
                        'access_level': 30,
                        'state': 'active',
                        'avatar_url': 'https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon',
                        'web_url': 'http://192.168.1.8:3000/root',
                        'name': 'Raymond Smith',
                        'id': 1,
                        'expires_at': '2012-10-22T14:13:35Z'
                    },
                    {
                        'username': 'john_doe',
                        'access_level': 30,
                        'state': 'active',
                        'avatar_url': 'https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon',
                        'web_url': 'http://192.168.1.8:3000/root',
                        'name': 'John Doe',
                        'id': 27,
                        'expires_at': '2012-10-22T14:13:35Z'
                    }
                ]
            }
        ]

        self.assertListEqual(actual, expected)

    # pylint: disable=no-member
    @responses.activate
    # pylint: enable=no-member
    @mock.patch('congregate.helpers.conf.ig.source_host', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.conf.ig.destination_host', new_callable=mock.PropertyMock)
    def test_update_users_invalid_id(self, destination, source):
        source.return_value = "https://gitlabsource.com"
        destination.return_value = "https://gitlabdestination.com"
        old_users = [
            {
                "name": "test-app",
                "members": self.mock_users.get_all_users_list()
            }
        ]
        new_users = self.mock_users.get_dummy_new_users()

        url_value = "https://gitlabsource.com/api/v4/users/1"
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                    json=self.mock_users.get_dummy_old_users()[0], status=200)
        # pylint: enable=no-member
        url_value = "https://gitlabsource.com/api/v4/users/2"
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                    json=self.mock_users.get_dummy_old_users()[1], status=200)
        # pylint: enable=no-member
        url_value = "https://gitlabdestination.com/api/v4/users/27"
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                    json=self.mock_users.get_dummy_new_users()[1], status=200)
        # pylint: enable=no-member
        url_value = "https://gitlabdestination.com/api/v4/users/28"
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                    json=self.mock_users.get_user_404(), status=200)
        # pylint: enable=no-member
        url_value = "https://gitlabdestination.com/api/v4/user"
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                    json=self.mock_users.get_current_user(), status=200)
        # pylint: enable=no-member

        actual = self.users.update_users(old_users, new_users)

        expected = [
            {
                'name': 'test-app',
                'members': [
                    {
                        'username': 'raymond_smith',
                        'access_level': 30,
                        'state': 'active',
                        'avatar_url': 'https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon',
                        'web_url': 'http://192.168.1.8:3000/root',
                        'name': 'Raymond Smith',
                        'id': 1,
                        'expires_at': '2012-10-22T14:13:35Z'
                    },
                    {
                        'username': 'john_doe',
                        'access_level': 30,
                        'state': 'active',
                        'avatar_url': 'https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon',
                        'web_url': 'http://192.168.1.8:3000/root',
                        'name': 'John Doe',
                        'id': 27,
                        'expires_at': '2012-10-22T14:13:35Z'
                    }
                ]
            }
        ]

        self.assertListEqual(actual, expected)

    # pylint: disable=no-member
    @responses.activate
    # pylint: enable=no-member
    @mock.patch('congregate.helpers.conf.ig.destination_host', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.parent_id', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.api.get_count')
    def test_handle_user_creation(self, count, parent_id, destination):
        count.return_value = 1
        parent_id.return_value = None
        destination.return_value = "https://gitlabdestination.com"
        new_user = self.mock_users.get_dummy_user()
        new_user.pop("id")

        url_value = "https://gitlabdestination.com/api/v4/users"
        # pylint: disable=no-member
        responses.add(responses.POST, url_value,
                    json=self.mock_users.get_dummy_new_users()[1], status=200)
        # pylint: enable=no-member
        url_value = "https://gitlabdestination.com/api/v4/users?search=%s&per_page=50&page=%d" % (new_user["email"], count.return_value)
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                    json=[self.mock_users.get_dummy_user()], status=200)
        # pylint: enable=no-member

        self.assertEqual(self.users.handle_user_creation(new_user), 27)

    # pylint: disable=no-member
    @responses.activate
    # pylint: enable=no-member
    @mock.patch('congregate.helpers.conf.ig.destination_host', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.parent_id', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.api.get_count')
    def test_handle_user_creation_user_already_exists_no_parent_group(self, count, parent_id, destination):
        count.return_value = 1
        parent_id.return_value = None
        destination.return_value = "https://gitlabdestination.com"
        new_user = self.mock_users.get_dummy_user()
        new_user.pop("id")

        url_value = "https://gitlabdestination.com/api/v4/users"
        # pylint: disable=no-member
        responses.add(responses.POST, url_value,
                    json=self.mock_users.get_dummy_new_users()[1], status=409)
        # pylint: enable=no-member
        url_value = "https://gitlabdestination.com/api/v4/users?search=%s&per_page=50&page=%d" % (new_user["email"], count.return_value)
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                    json=[self.mock_users.get_dummy_user()], status=200)
        # pylint: enable=no-member

        self.assertEqual(self.users.handle_user_creation(new_user), 27)

    # pylint: disable=no-member
    @responses.activate
    # pylint: enable=no-member
    @mock.patch('congregate.helpers.conf.ig.destination_host', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.parent_id', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.api.get_count')
    def test_handle_user_creation_user_already_exists_with_parent_group(self, count, parent_id, destination):
        count.return_value = 1
        parent_id.return_value = 10
        destination.return_value = "https://gitlabdestination.com"
        new_user = self.mock_users.get_dummy_user()
        new_user.pop("id")

        url_value = "https://gitlabdestination.com/api/v4/users"
        # pylint: disable=no-member
        responses.add(responses.POST, url_value,
                    json=self.mock_users.get_dummy_new_users()[1], status=409)
        # pylint: enable=no-member
        url_value = "https://gitlabdestination.com/api/v4/users?search=%s&per_page=50&page=%d" % (new_user["email"], count.return_value)
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                    json=[self.mock_users.get_dummy_user()], status=200)
        # pylint: enable=no-member

        self.assertEqual(self.users.handle_user_creation(new_user), 27)

    # pylint: disable=no-member
    @responses.activate
    # pylint: enable=no-member
    @mock.patch('congregate.helpers.conf.ig.destination_host', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.api.get_count')
    def test_block_user(self, count,destination):
        destination.return_value = "https://gitlabdestination.com"
        new_user = self.mock_users.get_dummy_user()

        url_value = "https://gitlabdestination.com/api/v4/users?search=%s&per_page=50&page=%d" % (new_user["email"], count.return_value)
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                    json=[self.mock_users.get_dummy_user()], status=200)
        # pylint: enable=no-member
        url_value = "https://gitlabdestination.com/api/v4/users/27/block"
        # pylint: disable=no-member
        responses.add(responses.POST, url_value,
                    json=self.mock_users.get_dummy_user_blocked(), status=201)

        self.assertEqual(self.users.block_user(new_user).status_code, 201)

    def test_remove_blocked_users(self):
        read_data = json.dumps(self.mock_users.get_dummy_new_users())
        mock_open = mock.mock_open(read_data=read_data)
        with mock.patch('__builtin__.open', mock_open):
            result = self.users.remove("staged_users")
        self.assertEqual(result, self.mock_users.get_dummy_new_users_active())

    def test_remove_blocked_project_members(self):
        read_data = json.dumps(self.mock_users.get_dummy_project())
        mock_open = mock.mock_open(read_data=read_data)
        with mock.patch('__builtin__.open', mock_open):
            result = self.users.remove("stage")
        self.assertEqual(result, self.mock_users.get_dummy_project_active_members())

    def test_remove_blocked_group_members(self):
        read_data = json.dumps(self.mock_users.get_dummy_group())
        mock_open = mock.mock_open(read_data=read_data)
        with mock.patch('__builtin__.open', mock_open):
            result = self.users.remove("staged_groups")
        self.assertEqual(result, self.mock_users.get_dummy_group_active_members())

    @mock.patch('congregate.migration.gitlab.users.UsersClient.find_user_by_email_comparison_without_id')
    @mock.patch('congregate.migration.gitlab.users.UsersClient.user_email_exists')
    def test_create_valid_username_found_email_returns_username(self, mock_email_check, mock_email_find):
        dummy_user = self.mock_users.get_dummy_user()
        mock_email_check.return_value = True
        mock_email_find.return_value = dummy_user
        created_user_name = self.users.create_valid_username(dummy_user)
        self.assertEqual(created_user_name, dummy_user["username"])

    @mock.patch('congregate.migration.gitlab.users.UsersClient.username_exists')
    @mock.patch('congregate.migration.gitlab.users.UsersClient.find_user_by_email_comparison_without_id')
    @mock.patch('congregate.migration.gitlab.users.UsersClient.user_email_exists')
    def test_create_valid_username_not_found_email_not_found_username_returns_passed_username(
            self,
            mock_email_check,
            mock_email_find,
            mock_username_exists):
        dummy_user = self.mock_users.get_dummy_user()
        mock_email_check.return_value = True
        mock_email_find.return_value = dummy_user
        mock_username_exists.return_value = False
        dummy_user["username"] = "JUST NOW CREATED"
        created_user_name = self.users.create_valid_username(dummy_user)
        self.assertEqual(created_user_name, dummy_user["username"])

    @mock.patch('congregate.helpers.conf.ig.username_suffix', new_callable=mock.PropertyMock)
    @mock.patch('congregate.migration.gitlab.users.UsersClient.username_exists')
    @mock.patch('congregate.migration.gitlab.users.UsersClient.find_user_by_email_comparison_without_id')
    @mock.patch('congregate.migration.gitlab.users.UsersClient.user_email_exists')
    def test_create_valid_username_not_found_email_found_username_returns_suffix_username_if_suffix_set(
            self,
            mock_email_check,
            mock_email_find,
            mock_username_exists,
            mock_username_suffix):
        dummy_user = self.mock_users.get_dummy_user()
        mock_email_check.return_value = False
        mock_email_find.return_value = dummy_user
        mock_username_exists.return_value = True
        mock_username_suffix.return_value = "BLEPBLEP"
        dummy_user["username"] = "JUST NOW CREATED"
        created_user_name = self.users.create_valid_username(dummy_user)
        self.assertEqual(created_user_name, dummy_user["username"] + "_BLEPBLEP")

    @mock.patch('congregate.helpers.conf.ig.username_suffix', new_callable=mock.PropertyMock)
    @mock.patch('congregate.migration.gitlab.users.UsersClient.username_exists')
    @mock.patch('congregate.migration.gitlab.users.UsersClient.find_user_by_email_comparison_without_id')
    @mock.patch('congregate.migration.gitlab.users.UsersClient.user_email_exists')
    def test_create_valid_username_not_found_email_found_username_returns_unserscore_username_if_suffix_not_set(
            self,
            mock_email_check,
            mock_email_find,
            mock_username_exists,
            mock_username_suffix):
        dummy_user = self.mock_users.get_dummy_user()
        mock_email_check.return_value = False
        mock_email_find.return_value = dummy_user
        mock_username_exists.return_value = True
        mock_username_suffix.return_value = None
        dummy_user["username"] = "JUST NOW CREATED"
        created_user_name = self.users.create_valid_username(dummy_user)
        self.assertEqual(created_user_name, dummy_user["username"] + "_")


    # pylint: disable=no-member
    @responses.activate
    # pylint: enable=no-member
    @mock.patch("congregate.helpers.api.generate_v4_request_url")
    @mock.patch.object(UsersApi, "search_for_user_by_email")
    @mock.patch('congregate.migration.gitlab.users.UsersClient.user_email_exists')
    def test_find_user_primarily_by_email_with_email(self, check, search, url):
        user = {
            "email": "jdoe@email.com",
            "id": 5
        }
        url_value = "https://gitlabsource.com/api/v4/users/5"
        url.return_value = url_value
        check.return_value = True
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                    json=self.mock_users.get_dummy_user(), status=200)
        # pylint: enable=no-member
        search.return_value = [self.mock_users.get_dummy_user()]
        actual = self.users.find_user_primarily_by_email(user)
        expected = self.mock_users.get_dummy_user()
        self.assertDictEqual(expected, actual)

    # pylint: disable=no-member
    @responses.activate
    # pylint: enable=no-member
    @mock.patch("congregate.helpers.api.generate_v4_request_url")
    @mock.patch.object(UsersApi, "search_for_user_by_email")
    @mock.patch('congregate.migration.gitlab.users.UsersClient.user_email_exists')
    def test_find_user_primarily_by_email_with_id(self, check, search, url):
        user = {
            "id": 5
        }
        url_value = "https://gitlabsource.com/api/v4/users/5"
        url.return_value = url_value
        check.return_value = True
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                    json=self.mock_users.get_dummy_user(), status=200)
        # pylint: enable=no-member
        search.return_value = [self.mock_users.get_dummy_user()]
        actual = self.users.find_user_primarily_by_email(user)
        expected = self.mock_users.get_dummy_user()
        self.assertDictEqual(expected, actual)

    # pylint: disable=no-member
    @responses.activate
    # pylint: enable=no-member
    @mock.patch("congregate.helpers.api.generate_v4_request_url")
    @mock.patch.object(UsersApi, "search_for_user_by_email")
    def test_find_user_primarily_by_email_with_invalid_object(self, search, url):
        user = {}
        url_value = "https://gitlabsource.com/api/v4/users/5"
        url.return_value = url_value
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                    json=self.mock_users.get_dummy_user(), status=200)
        # pylint: enable=no-member
        search.return_value = [self.mock_users.get_dummy_user()]
        actual = self.users.find_user_primarily_by_email(user)
        self.assertIsNone(actual)

    # pylint: disable=no-member
    @responses.activate
    # pylint: enable=no-member
    @mock.patch("congregate.helpers.api.generate_v4_request_url")
    @mock.patch.object(UsersApi, "search_for_user_by_email")
    def test_find_user_primarily_by_email_with_none(self, search, url):
        user = None
        url_value = "https://gitlabsource.com/api/v4/users/5"
        url.return_value = url_value
        # pylint: disable=no-member
        responses.add(responses.GET, url_value,
                    json=self.mock_users.get_dummy_user(), status=200)
        # pylint: enable=no-member
        search.return_value = [self.mock_users.get_dummy_user()]
        actual = self.users.find_user_primarily_by_email(user)
        self.assertIsNone(actual)

    @mock.patch.object(GroupsApi, "search_for_group")
    def test_is_username_group_name_not_found(self, group_api):
        group_api.return_value = {"name": "xyz"}
        response = self.users.is_username_group_name({"username": "abc"})
        self.assertFalse(response)

    @mock.patch.object(GroupsApi, "search_for_group")
    def test_is_username_group_name_found(self, group_api):
        group_api.return_value = {"name": "abc"}
        response = self.users.is_username_group_name({"username": "abc"})
        self.assertTrue(response)

    @mock.patch.object(GroupsApi, "search_for_group")
    def test_is_username_group_name_found_ignore_case(self, group_api):
        group_api.return_value = {"name": "ABC"}
        response = self.users.is_username_group_name({"username": "abc"})
        self.assertTrue(response)

    @mock.patch.object(GroupsApi, "search_for_group")
    def test_is_username_group_name_error_assumes_none(self, group_api):
        group_api.side_effect = Exception("THIS HAPPENED")
        response = self.users.is_username_group_name({"username": "abc"})
        self.assertIsNone(response)
