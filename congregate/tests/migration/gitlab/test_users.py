import unittest
import mock
import json
import responses
from congregate.tests.mockapi.users import MockUsersApi
from congregate.migration.gitlab.api.users import UsersApi
from congregate.migration.gitlab.users import UsersClient
from congregate.helpers.conf import ig

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


    @mock.patch.object(UsersApi, "search_for_user_by_email")
    def test_user_exists_true(self, search):
        search.return_value = [self.mock_users.get_dummy_user()]
        old_user = {
            "username": "jdoe"
        }
        actual = self.users.username_exists(old_user)
        self.assertTrue(actual)

    @mock.patch.object(UsersApi, "search_for_user_by_email")
    def test_user_exists_false(self, search):
        search.return_value = [self.mock_users.get_dummy_user()]
        old_user = {
            "username": "notjdoe"
        }
        actual = self.users.username_exists(old_user)
        self.assertFalse(actual)

    @mock.patch.object(UsersApi, "search_for_user_by_email")
    def test_user_exists_over_100(self, search):
        dummy_large_list = []
        for _ in range(0, 105):
            dummy_large_list.append(self.mock_users.get_dummy_user())
        search.return_value = dummy_large_list
        old_user = {
            "username": "notjdoe"
        }
        actual = self.users.username_exists(old_user)
        self.assertFalse(actual)

    @mock.patch.object(UsersApi, "search_for_user_by_email")
    def test_user_exists_no_results(self, search):
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
    #
    # # pylint: disable=no-member
    # @responses.activate
    # # pylint: enable=no-member
    # @mock.patch('congregate.helpers.conf.ig.source_host', new_callable=mock.PropertyMock)
    # @mock.patch('congregate.helpers.conf.ig.destination_host', new_callable=mock.PropertyMock)
    # def test_update_users_no_new_users(self, destination, source):
    #     source.return_value = "https://gitlabsource.com"
    #     destination.return_value = "https://gitlabdestination.com"
    #     old_users = [
    #         {
    #             "name": "test-app",
    #             "members": self.mock_users.get_all_users_list()
    #         }
    #     ]
    #     new_users = []
    #
    #     url_value = "https://gitlabsource.com/api/v4/users/1"
    #     # pylint: disable=no-member
    #     responses.add(responses.GET, url_value,
    #                 json=self.mock_users.get_dummy_old_users()[0], status=200)
    #     # pylint: enable=no-member
    #     url_value = "https://gitlabsource.com/api/v4/users/2"
    #     # pylint: disable=no-member
    #     responses.add(responses.GET, url_value,
    #                 json=self.mock_users.get_dummy_old_users()[1], status=200)
    #     # pylint: enable=no-member
    #     url_value = "https://gitlabdestination.com/api/v4/users/27"
    #     # pylint: disable=no-member
    #     responses.add(responses.GET, url_value,
    #                 json=self.mock_users.get_dummy_new_users()[0], status=200)
    #     # pylint: enable=no-member
    #     url_value = "https://gitlabdestination.com/api/v4/users/28"
    #     # pylint: disable=no-member
    #     responses.add(responses.GET, url_value,
    #                 json=self.mock_users.get_dummy_new_users()[1], status=200)
    #     # pylint: enable=no-member
    #     url_value = "https://gitlabdestination.com/api/v4/user"
    #     # pylint: disable=no-member
    #     responses.add(responses.GET, url_value,
    #                 json=self.mock_users.get_current_user(), status=200)
    #     # pylint: enable=no-member
    #
    #     actual = self.users.update_users(old_users, new_users)
    #
    #     expected = [
    #         {
    #             'name': 'test-app',
    #             'members': [
    #                 {
    #                     'username': 'raymond_smith',
    #                     'access_level': 30,
    #                     'state': 'active',
    #                     'avatar_url': 'https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon',
    #                     'web_url': 'http://192.168.1.8:3000/root',
    #                     'name': 'Raymond Smith',
    #                     'id': 1,
    #                     'expires_at': '2012-10-22T14:13:35Z'
    #                 },
    #                 {
    #                     'username': 'john_doe',
    #                     'access_level': 30,
    #                     'state': 'active',
    #                     'avatar_url': 'https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon',
    #                     'web_url': 'http://192.168.1.8:3000/root',
    #                     'name': 'John Doe',
    #                     'id': 1,
    #                     'expires_at': '2012-10-22T14:13:35Z'
    #                 }
    #             ]
    #         }
    #     ]
    #
    #     self.assertListEqual(actual, expected)

    # # pylint: disable=no-member
    # @responses.activate
    # # pylint: enable=no-member
    # @mock.patch('congregate.helpers.conf.ig.source_host', new_callable=mock.PropertyMock)
    # @mock.patch('congregate.helpers.conf.ig.destination_host', new_callable=mock.PropertyMock)
    # def test_update_users_wrong_email(self, destination, source):
    #     source.return_value = "https://gitlabsource.com"
    #     destination.return_value = "https://gitlabdestination.com"
    #     old_users = [
    #         {
    #             "name": "test-app",
    #             "members": self.mock_users.get_all_users_list()
    #         }
    #     ]
    #     new_users = self.mock_users.get_dummy_new_users()
    #
    #     wrong_raymond_smith = self.mock_users.get_dummy_new_users()[0]
    #     wrong_raymond_smith["email"] = "not_raymond_smith@email.com"
    #
    #     url_value = "https://gitlabsource.com/api/v4/users/1"
    #     # pylint: disable=no-member
    #     responses.add(responses.GET, url_value,
    #                 json=self.mock_users.get_dummy_old_users()[0], status=200)
    #     # pylint: enable=no-member
    #     url_value = "https://gitlabsource.com/api/v4/users/2"
    #     # pylint: disable=no-member
    #     responses.add(responses.GET, url_value,
    #                 json=self.mock_users.get_dummy_old_users()[1], status=200)
    #     # pylint: enable=no-member
    #     url_value = "https://gitlabdestination.com/api/v4/users/27"
    #     # pylint: disable=no-member
    #     responses.add(responses.GET, url_value,
    #                 json=self.mock_users.get_dummy_new_users()[1], status=200)
    #     # pylint: enable=no-member
    #     url_value = "https://gitlabdestination.com/api/v4/users/28"
    #     # pylint: disable=no-member
    #     responses.add(responses.GET, url_value,
    #                 json=wrong_raymond_smith, status=200)
    #     # pylint: enable=no-member
    #     url_value = "https://gitlabdestination.com/api/v4/user"
    #     # pylint: disable=no-member
    #     responses.add(responses.GET, url_value,
    #                 json=self.mock_users.get_current_user(), status=200)
    #     # pylint: enable=no-member
    #
    #     actual = self.users.update_users(old_users, new_users)
    #
    #     expected = [
    #         {
    #             'name': 'test-app',
    #             'members': [
    #                 {
    #                     'username': 'raymond_smith',
    #                     'access_level': 30,
    #                     'state': 'active',
    #                     'avatar_url': 'https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon',
    #                     'web_url': 'http://192.168.1.8:3000/root',
    #                     'name': 'Raymond Smith',
    #                     'id': 1,
    #                     'expires_at': '2012-10-22T14:13:35Z'
    #                 },
    #                 {
    #                     'username': 'john_doe',
    #                     'access_level': 30,
    #                     'state': 'active',
    #                     'avatar_url': 'https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon',
    #                     'web_url': 'http://192.168.1.8:3000/root',
    #                     'name': 'John Doe',
    #                     'id': 27,
    #                     'expires_at': '2012-10-22T14:13:35Z'
    #                 }
    #             ]
    #         }
    #     ]
    #
    #     self.assertListEqual(actual, expected)

    # # pylint: disable=no-member
    # @responses.activate
    # # pylint: enable=no-member
    # @mock.patch('congregate.helpers.conf.ig.source_host', new_callable=mock.PropertyMock)
    # @mock.patch('congregate.helpers.conf.ig.destination_host', new_callable=mock.PropertyMock)
    # def test_update_users_invalid_id(self, destination, source):
    #     source.return_value = "https://gitlabsource.com"
    #     destination.return_value = "https://gitlabdestination.com"
    #     old_users = [
    #         {
    #             "name": "test-app",
    #             "members": self.mock_users.get_all_users_list()
    #         }
    #     ]
    #     new_users = self.mock_users.get_dummy_new_users()
    #
    #
    #
    #     url_value = "https://gitlabsource.com/api/v4/users/1"
    #     # pylint: disable=no-member
    #     responses.add(responses.GET, url_value,
    #                 json=self.mock_users.get_dummy_old_users()[0], status=200)
    #     # pylint: enable=no-member
    #     url_value = "https://gitlabsource.com/api/v4/users/2"
    #     # pylint: disable=no-member
    #     responses.add(responses.GET, url_value,
    #                 json=self.mock_users.get_dummy_old_users()[1], status=200)
    #     # pylint: enable=no-member
    #     url_value = "https://gitlabdestination.com/api/v4/users/27"
    #     # pylint: disable=no-member
    #     responses.add(responses.GET, url_value,
    #                 json=self.mock_users.get_dummy_new_users()[1], status=200)
    #     # pylint: enable=no-member
    #     url_value = "https://gitlabdestination.com/api/v4/users/28"
    #     # pylint: disable=no-member
    #     responses.add(responses.GET, url_value,
    #                 json=self.mock_users.get_user_404(), status=200)
    #     # pylint: enable=no-member
    #     url_value = "https://gitlabdestination.com/api/v4/user"
    #     # pylint: disable=no-member
    #     responses.add(responses.GET, url_value,
    #                 json=self.mock_users.get_current_user(), status=200)
    #     # pylint: enable=no-member
    #
    #     actual = self.users.update_users(old_users, new_users)
    #
    #     expected = [
    #         {
    #             'name': 'test-app',
    #             'members': [
    #                 {
    #                     'username': 'raymond_smith',
    #                     'access_level': 30,
    #                     'state': 'active',
    #                     'avatar_url': 'https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon',
    #                     'web_url': 'http://192.168.1.8:3000/root',
    #                     'name': 'Raymond Smith',
    #                     'id': 1,
    #                     'expires_at': '2012-10-22T14:13:35Z'
    #                 },
    #                 {
    #                     'username': 'john_doe',
    #                     'access_level': 30,
    #                     'state': 'active',
    #                     'avatar_url': 'https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon',
    #                     'web_url': 'http://192.168.1.8:3000/root',
    #                     'name': 'John Doe',
    #                     'id': 27,
    #                     'expires_at': '2012-10-22T14:13:35Z'
    #                 }
    #             ]
    #         }
    #     ]
    #
    #     self.assertListEqual(actual, expected)

    # # pylint: disable=no-member
    # @responses.activate
    # # pylint: enable=no-member
    # @mock.patch('congregate.helpers.conf.ig.destination_host', new_callable=mock.PropertyMock)
    # @mock.patch('congregate.helpers.api.get_count')
    # def test_handle_user_creation(self, count, destination):
    #     count.return_value = 1
    #     destination.return_value = "https://gitlabdestination.com"
    #     new_user = self.mock_users.get_dummy_user()
    #     new_user.pop("id")
    #
    #     url_value = "https://gitlabdestination.com/api/v4/users"
    #     # pylint: disable=no-member
    #     responses.add(responses.POST, url_value,
    #                 json=self.mock_users.get_dummy_new_users()[1], status=200)
    #     # pylint: enable=no-member
    #     url_value = "https://gitlabdestination.com/api/v4/users?search=%s&per_page=50&page=1" % (new_user["email"])
    #     # pylint: disable=no-member
    #     responses.add(responses.GET, url_value,
    #                 json=[self.mock_users.get_dummy_user()], status=200)
    #     # pylint: enable=no-member
    #
    #     actual = self.users.handle_user_creation(new_user)
    #     expected = 27
    #
    #     self.assertEqual(actual, expected)
    #
    # # pylint: disable=no-member
    # @responses.activate
    # # pylint: enable=no-member
    # @mock.patch('congregate.helpers.conf.ig.destination_host', new_callable=mock.PropertyMock)
    # @mock.patch('congregate.helpers.api.get_count')
    # def test_handle_user_creation_user_already_exists(self, count, destination):
    #     count.return_value = 1
    #     destination.return_value = "https://gitlabdestination.com"
    #     new_user = self.mock_users.get_dummy_user()
    #     new_user.pop("id")
    #
    #     url_value = "https://gitlabdestination.com/api/v4/users"
    #     # pylint: disable=no-member
    #     responses.add(responses.POST, url_value,
    #                 json=self.mock_users.get_dummy_new_users()[1], status=409)
    #     # pylint: enable=no-member
    #     url_value = "https://gitlabdestination.com/api/v4/users?search=%s&per_page=50&page=%d" % (new_user["email"], count.return_value)
    #     # pylint: disable=no-member
    #     responses.add(responses.GET, url_value,
    #                 json=[self.mock_users.get_dummy_user()], status=200)
    #     # pylint: enable=no-member
    #
    #     actual = self.users.handle_user_creation(new_user)
    #     expected = 27
    #
    #     self.assertEqual(actual, expected)
    #
    #