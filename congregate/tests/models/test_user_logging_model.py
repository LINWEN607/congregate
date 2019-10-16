import unittest
from congregate.models.user_logging_model import UserLoggingModel


class UserLoggingModelTests(unittest.TestCase):
    def setUp(self):
        self.user_model = UserLoggingModel()

    def test_proper_fields(self):
        user = {
            "id": 123,
            "username": "some username",
            "email": "some@email.com"
        }
        return_user_model = self.user_model.get_logging_model(user)
        self.assertDictEqual(user, return_user_model)
