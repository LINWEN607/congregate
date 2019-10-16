import json
from congregate.helpers.base_class import BaseClass


class BaseLoggingModel(BaseClass):

    FIELDS = []

    def __init__(self):
        super(BaseLoggingModel, self).__init__()

    def get_logging_model(self, entity):
        __entity = {}
        if isinstance(entity, str):
            __entity = json.loads(entity)
        elif isinstance(entity, dict):
            __entity = entity
        else:
            raise Exception("Logging model takes string or dictionary")
        return {k: v for (k, v) in __entity.items() if str(k).lower() in self.FIELDS}
