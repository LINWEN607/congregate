from congregate.models.base_logging_model import BaseLoggingModel


class UserLoggingModel(BaseLoggingModel):
    def __init__(self):
        super(UserLoggingModel, self).__init__()
        self.FIELDS = ["id", "username", "email"]
