import mock
import unittest
from congregate.migration.gitlab.groups import GroupsClient


class GroupsUnitTest(unittest.TestCase):

    class MockReturn:
        status_code = None

        def __init__(self, json_in, status_code_in):
            self.json_string = json_in
            self.status_code = status_code_in

        def json(self):
            return self.json_string

    #   Get
    @mock.patch("congregate.migration.gitlab.groups.api.generate_get_request")
    def test_get_current_group_notifications_returns_none_on_api_none(self, mock_get_api):
        mock_get_api.return_value = None
        gc = GroupsClient()
        return_value = gc.get_current_group_notifications(1111)
        assert return_value is None

    @mock.patch("congregate.migration.gitlab.groups.api.generate_get_request")
    def test_get_current_group_notifications_returns_none_on_api_not_200(self, mock_get_api):
        mock_get_api.return_value = {"status_code": 999}
        gc = GroupsClient()
        return_value = gc.get_current_group_notifications(1111)
        assert return_value is None

    @mock.patch("congregate.migration.gitlab.groups.api.generate_get_request")
    def test_get_current_group_notifications_returns_none_on_api_no_level(self, mock_get_api):
        mock_get_api.return_value = {"status_code": 200}
        gc = GroupsClient()
        return_value = gc.get_current_group_notifications(1111)
        assert return_value is None

    @mock.patch("congregate.migration.gitlab.groups.api.generate_get_request")
    def test_get_current_group_notifications_happy(self, mock_get_api):
        mock_get_api.return_value = self.MockReturn({"status_code": 200, "level": "disabled"}, 200)
        gc = GroupsClient()
        return_value = gc.get_current_group_notifications(1111)
        assert return_value == "disabled"

    #   Update
    @mock.patch("congregate.migration.gitlab.groups.api.generate_put_request")
    def test_disable_group_notifications_returns_none_on_api_none(self, mock_put_api):
        mock_put_api.return_value = None
        gc = GroupsClient()
        return_value = gc.update_group_notifications(1111)
        assert return_value is None

    @mock.patch("congregate.migration.gitlab.groups.api.generate_put_request")
    def test_disable_group_notifications_returns_none_on_api_not_200(self, mock_put_api):
        mock_put_api.return_value = {"status_code": 999}
        gc = GroupsClient()
        return_value = gc.update_group_notifications(1111)
        assert return_value is None

    @mock.patch("congregate.migration.gitlab.groups.api.generate_put_request")
    def test_disable_group_notifications_happy(self, mock_put_api):
        mock_put_api.return_value = self.MockReturn({"some": "json"}, 200)
        gc = GroupsClient()
        return_value = gc.update_group_notifications(1111)
        assert return_value.json() == {"some": "json"}

    #   Reset
    @mock.patch("congregate.migration.gitlab.groups.api.generate_put_request")
    def test_enable_group_notifications_returns_none_on_api_none(self, mock_put_api):
        mock_put_api.return_value = None
        gc = GroupsClient()
        return_value = gc.reset_group_notifications(1111, "level")
        assert return_value is None

    @mock.patch("congregate.migration.gitlab.groups.api.generate_put_request")
    def test_enable_group_notifications_returns_none_on_api_not_200(self, mock_put_api):
        mock_put_api.return_value = {"status_code": 999}
        gc = GroupsClient()
        return_value = gc.reset_group_notifications(1111, "level")
        assert return_value is None

    @mock.patch("congregate.migration.gitlab.groups.api.generate_put_request")
    def test_enable_group_notifications_happy(self, mock_put_api):
        mock_put_api.return_value = self.MockReturn({"some": "json"}, 200)
        gc = GroupsClient()
        return_value = gc.reset_group_notifications(1111, "level")
        assert return_value.json() == {"some": "json"}
