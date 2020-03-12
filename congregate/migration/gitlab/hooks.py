from requests.exceptions import RequestException

from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import get_dry_log
from congregate.migration.gitlab.api.system import SystemApi
from congregate.migration.gitlab.api.projects import ProjectsApi


class HooksClient(BaseClass):
    def __init__(self):
        self.system_api = SystemApi()
        self.projects_api = ProjectsApi()
        super(HooksClient, self).__init__()

    def migrate_system_hooks(self, dry_run=True):
        try:
            response = self.system_api.get_all_system_hooks(
                self.config.source_host, self.config.source_token)
            s_hooks_src = iter(response)
            # used to check if hook already exists
            s_hooks_dstn = list(self.system_api.get_all_system_hooks(
                self.config.destination_host, self.config.destination_token))
            for h in s_hooks_dstn:
                h.pop("id", None)
                h.pop("created_at", None)
            for hook in s_hooks_src:
                self.log.info("{0}Migrating system hook {1} (ID: {2})".format(
                    get_dry_log(dry_run), hook["url"], hook["id"]))
                hook.pop("id", None)
                hook.pop("created_at", None)
                if not dry_run and not hook in s_hooks_dstn:
                    # hook does not include secret token
                    self.system_api.create_system_hook(
                        self.config.destination_host, self.config.destination_token, hook)
        except TypeError as te:
            self.log.error("System hooks {0} {1}".format(response, te))
        except RequestException as re:
            self.log.error(
                "Failed to migrate system hooks, with error:\n{}".format(re))

    def migrate_project_hooks(self, old_id, new_id, name):
        try:
            response = self.projects_api.get_all_project_hooks(
                self.config.source_host, self.config.source_token, old_id)
            p_hooks = iter(response)
            for h in p_hooks:
                self.log.info("Migrating project {0} (ID: {1}) hook {2} (ID: {3})".format(
                    name, old_id, h["url"], h["id"]))
                h.pop("created_at", None)
                h["project_id"] = new_id
                # hook does not include secret token
                self.projects_api.add_project_hook(
                    self.config.destination_host, self.config.destination_token, new_id, h)
        except TypeError as te:
            self.log.error("Project {0} (ID: {1}) hooks {2} {3}".format(
                name, old_id, response, te))
            return False
        except RequestException as re:
            self.log.error(
                "Failed to migrate project {0} (ID: {1}) hooks, with error:\n{2}".format(name, old_id, re))
            return False
        else:
            return True
