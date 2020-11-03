from requests.exceptions import RequestException

from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import get_dry_log, is_error_message_present, is_dot_com
from congregate.migration.gitlab.api.instance import InstanceApi
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.api.groups import GroupsApi


class HooksClient(BaseClass):
    def __init__(self):
        self.instance_api = InstanceApi()
        self.projects_api = ProjectsApi()
        self.groups_api = GroupsApi()
        super(HooksClient, self).__init__()

    def migrate_instance_hooks(self, dry_run=True):
        if not is_dot_com(self.config.source_host):
            try:
                resp = self.instance_api.get_all_instance_hooks(
                    self.config.source_host, self.config.source_token)
                s_hooks_src = iter(resp)
                # Used to check if hook already exists
                if is_dot_com(self.config.destination_host) and self.config.dstn_parent_id:
                    s_hooks_dstn = list(self.groups_api.get_all_group_hooks(
                        self.config.dstn_parent_id, self.config.destination_host, self.config.destination_token))
                else:
                    s_hooks_dstn = list(self.instance_api.get_all_instance_hooks(
                        self.config.destination_host, self.config.destination_token))
                for shd in s_hooks_dstn:
                    shd.pop("id", None)
                    shd.pop("created_at", None)
                for shc in s_hooks_src:
                    if is_error_message_present(shc) or not shc:
                        self.log.error(
                            f"Failed to fetch source instance hooks ({shc})")
                        break
                    self.log.info(
                        f"{get_dry_log(dry_run)}Migrating instance hook {shc['url']} (ID: {shc['id']})")
                    shc.pop("id", None)
                    shc.pop("created_at", None)
                    if not dry_run and not shc in s_hooks_dstn:
                        # hook does not include secret token
                        if is_dot_com(self.config.destination_host) and self.config.dstn_parent_id:
                            self.groups_api.add_group_hook(
                                self.config.destination_host, self.config.destination_token, self.config.dstn_parent_id, shc)
                        else:
                            self.instance_api.add_instance_hook(
                                self.config.destination_host, self.config.destination_token, shc)
            except TypeError as te:
                self.log.error(f"Instance hooks {resp} {te}")
            except RequestException as re:
                self.log.error(
                    f"Failed to migrate instance hooks, with error:\n{re}")

    def migrate_project_hooks(self, old_id, new_id, name):
        try:
            resp = self.projects_api.get_all_project_hooks(
                old_id, self.config.source_host, self.config.source_token)
            hooks = iter(resp)
            self.log.info(
                "Migrating project {0} (ID: {1}) hooks".format(name, old_id))
            for h in hooks:
                if is_error_message_present(h) or not h:
                    self.log.error(
                        "Failed to fetch hooks ({0}) for project {1} (ID: {2})".format(h, name, old_id))
                    return False
                h.pop("id", None)
                h.pop("created_at", None)
                h.pop("project_id", None)
                # hook does not include secret token
                self.projects_api.add_project_hook(
                    self.config.destination_host, self.config.destination_token, new_id, h)
            return True
        except TypeError as te:
            self.log.error("Project {0} (ID: {1}) hooks {2} {3}".format(
                name, old_id, resp, te))
            return False
        except RequestException as re:
            self.log.error(
                "Failed to migrate project {0} (ID: {1}) hooks, with error:\n{2}".format(name, old_id, re))
            return False

    def migrate_group_hooks(self, old_id, new_id, full_path):
        try:
            resp = self.groups_api.get_all_group_hooks(
                old_id, self.config.source_host, self.config.source_token)
            hooks = iter(resp)
            self.log.info(
                "Migrating group {0} (ID: {1}) hooks".format(full_path, old_id))
            for h in hooks:
                if is_error_message_present(h) or not h:
                    self.log.error(
                        "Failed to fetch hooks ({0}) for group {1} (ID: {2})".format(h, full_path, old_id))
                    return False
                h.pop("id", None)
                h.pop("created_at", None)
                h.pop("group_id", None)
                # hook does not include secret token
                self.groups_api.add_group_hook(
                    self.config.destination_host, self.config.destination_token, new_id, h)
            return True
        except TypeError as te:
            self.log.error("Group {0} (ID: {1}) hooks {2} {3}".format(
                full_path, old_id, resp, te))
            return False
        except RequestException as re:
            self.log.error(
                "Failed to migrate group {0} (ID: {1}) hooks, with error:\n{2}".format(full_path, old_id, re))
            return False
