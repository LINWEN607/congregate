import json
from congregate.helpers.base_class import BaseClass


class UserLoggingModel(BaseClass):
    __FIELDS = ["id", "username", "email"]

    @staticmethod
    def get_logging_user(user):
        __user = {}
        if isinstance(user, str):
            __user = json.loads(user)
        elif isinstance(user, dict):
            __user = user
        else:
            raise Exception("UserLoggingModel takes string or dictionary")
        return {k: v for (k, v) in __user.items() if str(k).lower() in UserLoggingModel.__FIELDS}
