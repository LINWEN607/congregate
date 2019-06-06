from helpers.base_class import BaseClass
from helpers import api
import json


class VersionClient(BaseClass):
    def get_version(self, host, token):
        return api.generate_get_request(host, token, "/version").json()