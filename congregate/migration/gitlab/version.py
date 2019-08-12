from congregate.helpers.base_class import BaseClass
from congregate.helpers import api
# pylint: disable=import-error, no-name-in-module
from distutils.version import StrictVersion
# pylint: enable=import-error, no-name-in-module

class VersionClient(BaseClass):
    def get_version(self, host, token):
        return api.generate_get_request(host, token, "/version").json()

    def is_older_than(self, old_version, new_version):
        return StrictVersion(old_version) <= StrictVersion(new_version)
