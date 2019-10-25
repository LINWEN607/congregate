import unittest
import mock
import responses

from congregate.migration.gitlab.groups import GroupsClient
from congregate.tests.mockapi.groups import MockGroupsApi


class GroupsUnitTest(unittest.TestCase):

    class MockReturn:
        status_code = None

        def __init__(self, json_in, status_code_in):
            self.json_string = json_in
            self.status_code = status_code_in

        def json(self):
            return self.json_string

    def setUp(self):
        self.mock_groups = MockGroupsApi()
        self.groups = GroupsClient()

    #   Get
    @mock.patch("congregate.migration.gitlab.groups.api.generate_get_request")
    def test_get_current_group_notifications_returns_none_on_api_none(self, mock_get_api):
        mock_get_api.return_value = None
        return_value = self.groups.get_current_group_notifications(1111)
        assert return_value is None

    @mock.patch("congregate.migration.gitlab.groups.api.generate_get_request")
    def test_get_current_group_notifications_returns_none_on_api_not_200(self, mock_get_api):
        mock_get_api.return_value = {"status_code": 999}
        return_value = self.groups.get_current_group_notifications(1111)
        assert return_value is None

    @mock.patch("congregate.migration.gitlab.groups.api.generate_get_request")
    def test_get_current_group_notifications_returns_none_on_api_no_level(self, mock_get_api):
        mock_get_api.return_value = {"status_code": 200}
        return_value = self.groups.get_current_group_notifications(1111)
        assert return_value is None

    @mock.patch("congregate.migration.gitlab.groups.api.generate_get_request")
    def test_get_current_group_notifications_happy(self, mock_get_api):
        mock_get_api.return_value = self.MockReturn({"status_code": 200, "level": "disabled"}, 200)
        return_value = self.groups.get_current_group_notifications(1111)
        assert return_value == "disabled"

    #   Update
    @mock.patch("congregate.migration.gitlab.groups.api.generate_put_request")
    def test_disable_group_notifications_returns_none_on_api_none(self, mock_put_api):
        mock_put_api.return_value = None
        return_value = self.groups.update_group_notifications(1111)
        assert return_value is None

    @mock.patch("congregate.migration.gitlab.groups.api.generate_put_request")
    def test_disable_group_notifications_returns_none_on_api_not_200(self, mock_put_api):
        mock_put_api.return_value = {"status_code": 999}
        return_value = self.groups.update_group_notifications(1111)
        assert return_value is None

    @mock.patch("congregate.migration.gitlab.groups.api.generate_put_request")
    def test_disable_group_notifications_happy(self, mock_put_api):
        mock_put_api.return_value = self.MockReturn({"some": "json"}, 200)
        return_value = self.groups.update_group_notifications(1111)
        assert return_value.json() == {"some": "json"}

    #   Reset
    @mock.patch("congregate.migration.gitlab.groups.api.generate_put_request")
    def test_enable_group_notifications_returns_none_on_api_none(self, mock_put_api):
        mock_put_api.return_value = None
        return_value = self.groups.reset_group_notifications(1111, "level")
        assert return_value is None

    @mock.patch("congregate.migration.gitlab.groups.api.generate_put_request")
    def test_enable_group_notifications_returns_none_on_api_not_200(self, mock_put_api):
        mock_put_api.return_value = {"status_code": 999}
        return_value = self.groups.reset_group_notifications(1111, "level")
        assert return_value is None

    @mock.patch("congregate.migration.gitlab.groups.api.generate_put_request")
    def test_enable_group_notifications_happy(self, mock_put_api):
        mock_put_api.return_value = self.MockReturn({"some": "json"}, 200)
        return_value = self.groups.reset_group_notifications(1111, "level")
        assert return_value.json() == {"some": "json"}

    # pylint: disable=no-member
    @responses.activate
    # pylint: enable=no-member
    @mock.patch('congregate.helpers.conf.ig.destination_host', new_callable=mock.PropertyMock)
    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.keep_blocked_users', new_callable=mock.PropertyMock)
    def test_add_members_skip_blocked_users(self, keep_blocked_users, destination):
        keep_blocked_users.return_value = False
        destination.return_value = "https://gitlabdestination.com"
        members = self.mock_groups.get_group_members()
        url_value = "https://gitlabdestination.com/api/v4/groups/42/members"
        # pylint: disable=no-member
        responses.add(responses.POST, url_value,
                    json=self.mock_groups.get_group_members()[2], status=202)
        new_members = [
            {
                "user_id": 286,
                "access_level": 50
            }
        ]
        self.assertEqual(self.groups.add_members(members, 42), new_members)

    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.keep_blocked_users', new_callable=mock.PropertyMock)
    def test_add_members_skip_blocked_users_dry_run(self, keep_blocked_users):
        keep_blocked_users.return_value = False
        members = self.mock_groups.get_group_members()
        new_members = [
            {
                "user_id": 286,
                "access_level": 50
            }
        ]
        self.assertEqual(self.groups.add_members(members, 42, dry_run=True), new_members)

    @mock.patch('congregate.helpers.configuration_validator.ConfigurationValidator.keep_blocked_users', new_callable=mock.PropertyMock)
    def test_add_members_keep_blocked_users_dry_run(self, keep_blocked_users):
        keep_blocked_users.return_value = True
        members = self.mock_groups.get_group_members()
        new_members = [
            {
                "user_id": 284,
                "access_level": 30
            },
            {
                "user_id": 285,
                "access_level": 40
            },
            {
                "user_id": 286,
                "access_level": 50
            }
        ]
        self.assertEqual(self.groups.add_members(members, 42, dry_run=True), new_members)
