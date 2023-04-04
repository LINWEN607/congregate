from requests.exceptions import RequestException

from congregate.helpers.base_class import BaseClass
from gitlab_ps_utils.misc_utils import get_dry_log, is_error_message_present
from gitlab_ps_utils.dict_utils import pop_multiple_keys
from congregate.helpers.utils import is_dot_com
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
        if not is_dot_com(self.config.source_host) and not self.config.airgap:
            try:
                resp = self.instance_api.get_all_instance_hooks(
                    self.config.source_host, self.config.source_token)
                s_hooks_src = iter(resp)
                # Used to check if hook already exists
                if is_dot_com(
                        self.config.destination_host) and self.config.dstn_parent_id:
                    s_hooks_dstn = list(self.groups_api.get_all_group_hooks(
                        self.config.dstn_parent_id, self.config.destination_host, self.config.destination_token))
                else:
                    s_hooks_dstn = list(self.instance_api.get_all_instance_hooks(
                        self.config.destination_host, self.config.destination_token))
                for shd in s_hooks_dstn:
                    shd = pop_multiple_keys(shd, ["id", "created_at"])
                for shc in s_hooks_src:
                    error, shc = is_error_message_present(shc)
                    if error or not shc:
                        self.log.error(
                            f"Failed to fetch source instance hooks ({shc})")
                        break
                    self.log.info(
                        f"{get_dry_log(dry_run)}Migrating instance hook {shc['url']} (ID: {shc['id']})")
                    shc = pop_multiple_keys(shc, ["id", "created_at"])
                    # hook does not include secret token
                    if not dry_run and not shc in s_hooks_dstn:
                        add_resp = None
                        if is_dot_com(self.config.destination_host):
                            # Only if migrating to the parent group on
                            # gitlab.com
                            if self.config.dstn_parent_id and "/" not in self.config.dstn_parent_group_path:
                                add_resp = self.groups_api.add_group_hook(
                                    self.config.destination_host, self.config.destination_token, self.config.dstn_parent_id, shc)
                        else:
                            add_resp = self.instance_api.add_instance_hook(
                                self.config.destination_host, self.config.destination_token, shc)
                        if add_resp and add_resp.status_code != 201:
                            self.log.error(
                                f"Failed to create instance hook {shc}, with error:\n{add_resp} - {add_resp.text}")
            except TypeError as te:
                self.log.error(f"Instance hooks {resp} {te}")
            except RequestException as re:
                self.log.error(
                    f"Failed to migrate instance hooks, with error:\n{re}")

    def migrate_project_hooks(self, old_id, new_id, path):
        try:
            resp = self.projects_api.get_all_project_hooks(
                old_id, self.config.source_host, self.config.source_token)
            hooks = iter(resp)
            self.log.info(f"Migrating project {path} (ID: {old_id}) hooks")
            for h in hooks:
                error, h = is_error_message_present(h)
                if error or not h:
                    self.log.error(
                        f"Failed to fetch project {path} (ID: {old_id}) hook ({h})")
                    return False
                h = pop_multiple_keys(h, ["id", "created_at", "project_id"])
                # hook does not include secret token
                add_resp = self.projects_api.add_project_hook(
                    self.config.destination_host, self.config.destination_token, new_id, h)
                if add_resp.status_code != 201:
                    self.log.error(
                        f"Failed to create project {path} (ID: {new_id}) hook ({h}), with error:\n{add_resp} - {add_resp.text}")
            return True
        except TypeError as te:
            self.log.error(f"Project {path} (ID: {old_id}) hooks {resp} {te}")
            return False
        except RequestException as re:
            self.log.error(
                f"Failed to migrate project {path} (ID: {old_id}) hooks, with error:\n{re}")
            return False

    def migrate_group_hooks(self, old_id, new_id, full_path):
        try:
            resp = self.groups_api.get_all_group_hooks(
                old_id, self.config.source_host, self.config.source_token)
            hooks = iter(resp)
            self.log.info(f"Migrating group {full_path} (ID: {old_id}) hooks")
            for h in hooks:
                error, h = is_error_message_present(h)
                if error or not h:
                    self.log.error(
                        f"Failed to fetch hooks ({h}) for group {full_path} (ID: {old_id})")
                    return False
                h = pop_multiple_keys(h, ["id", "created_at", "group_id"])
                # hook does not include secret token
                add_resp = self.groups_api.add_group_hook(
                    self.config.destination_host, self.config.destination_token, new_id, h)
                if add_resp.status_code != 201:
                    self.log.error(
                        f"Failed to create group {full_path} hook {h}, with error:\n{add_resp} - {add_resp.text}")
            return True
        except TypeError as te:
            self.log.error(
                f"Group {full_path} (ID: {old_id}) hooks {resp} {te}")
            return False
        except RequestException as re:
            self.log.error(
                f"Failed to migrate group {full_path} (ID: {old_id}) hooks, with error:\n{re}")
            return False
