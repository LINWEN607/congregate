from requests.exceptions import RequestException

from congregate.helpers.base_class import BaseClass
from congregate.migration.gitlab.api.hooks import HooksApi
from congregate.helpers.misc_utils import get_dry_log


class HooksClient(BaseClass):
    def __init__(self):
        self.hooks = HooksApi()
        super(HooksClient, self).__init__()

    def migrate_system_hooks(self, dry_run=True):
        try:
            response = self.hooks.get_all_system_hooks(
                self.config.source_host, self.config.source_token)
            s_hooks = list(response)
            if s_hooks:
                for s in s_hooks:
                    self.log.info(
                        "{0}Migrating system hook {1} (ID: {2})".format(get_dry_log(dry_run), s["url"], s["id"]))
                    if not dry_run:
                        self.hooks.create_system_hook(
                            self.config.destination_host, self.config.destination_token, s)
            else:
                self.log.info("SKIP: Source instance has no system hooks")
        except RequestException, re:
            self.log.error(
                "Failed to migrate system hooks, with error:\n{}".format(re))
