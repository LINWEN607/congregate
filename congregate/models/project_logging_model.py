from congregate.models.base_logging_model import BaseLoggingModel


class ProjectLoggingModel(BaseLoggingModel):
    def __init__(self):
        super(ProjectLoggingModel, self).__init__()
        self.FIELDS = ["id", "name", "name_with_namespace"]
