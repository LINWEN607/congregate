from helpers.base_class import BaseClass
from helpers import api
import json


class VersionClient(BaseClass):
    def get_version(self, host, token):
        return api.generate_get_request(host, token, "/version").json()

    def is_older_than(self, old_version, new_version):
        old_version = self.cat_version_string(old_version)
        new_version = self.cat_version_string(new_version)
        return old_version <= new_version

    def cat_version_string(self, version):
        return sum(int(n) for n in (version.split("-")[0]).split("."))