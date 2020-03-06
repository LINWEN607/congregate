from congregate.helpers.base_class import BaseClass
from congregate.helpers import api
# pylint: disable=import-error, no-name-in-module
from distutils.version import StrictVersion
# pylint: enable=import-error, no-name-in-module
from congregate.migration.gitlab.api.system import SystemApi

class VersionClient(BaseClass):
    def __init__(self):
        self.system_api = SystemApi()
        super(VersionClient, self).__init__()

    def get_version(self, host, token):
        return self.system_api.get_version(host, token).json()

    def is_older_than(self, old_version, new_version):
        old_version = old_version.split("-")[0]
        new_version = new_version.split("-")[0]
        return StrictVersion(old_version) <= StrictVersion(new_version)
