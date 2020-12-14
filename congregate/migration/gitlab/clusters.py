from requests.exceptions import RequestException

from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import is_error_message_present, safe_json_response, is_dot_com
from congregate.helpers.migrate_utils import get_dst_path_with_namespace
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.api.instance import InstanceApi
from congregate.migration.gitlab.projects import ProjectsClient


class ClustersClient(BaseClass):
    def __init__(self):
        self.projects_api = ProjectsApi()
        self.projects = ProjectsClient()
        self.groups_api = GroupsApi()
        self.instance_api = InstanceApi()
        super(ClustersClient, self).__init__()

    def migrate_instance_clusters(self, dry_run=True):
        if not is_dot_com(self.config.source_host):
            try:
                resp = self.instance_api.get_all_instance_clusters(
                    self.config.source_host, self.config.source_token)
                clusters = iter(resp)
                for c in clusters:
                    if is_error_message_present(c) or not c:
                        self.log.error(
                            f"Failed to fetch source instance clusters ({c['name']})")
                        break
                    if not dry_run:
                        if is_dot_com(self.config.destination_host):
                            # Only if migrating to the parent group on gitlab.com
                            if self.config.dstn_parent_id and "/" not in self.config.dstn_parent_group_path:
                                resp = self.groups_api.add_group_cluster(
                                    self.config.dstn_parent_id, self.config.destination_host, self.config.destination_token, self.create_data(c, {}, "Instance "))
                        else:
                            resp = self.instance_api.add_instance_cluster(
                                self.config.destination_host, self.config.destination_token, self.create_data(c, {}, "Instance "))
                        if resp.status_code != 201:
                            self.log.error(
                                f"Failed to create instance cluster {c['name']}, with error:\n{resp} - {resp.text}")
            except TypeError as te:
                self.log.error(f"Instance clusters {resp} {te}")
            except RequestException as re:
                self.log.error(
                    f"Failed to migrate instance clusters, with error:\n{re}")

    def migrate_group_clusters(self, old_id, new_id, full_path):
        try:
            resp = self.groups_api.get_all_group_clusters(
                old_id, self.config.source_host, self.config.source_token)
            clusters = iter(resp)
            self.log.info(
                f"Migrating group {full_path} (ID: {old_id}) clusters")
            for c in clusters:
                if is_error_message_present(c) or not c:
                    self.log.error(
                        f"Failed to fetch clusters ({c['name']}) for group {full_path} (ID: {old_id})")
                    return False
                resp = self.groups_api.add_group_cluster(
                    new_id, self.config.destination_host, self.config.destination_token, data=self.create_data(c, {}, "Group ", path=full_path))
                if resp.status_code != 201:
                    self.log.error(
                        f"Failed to create group {full_path} cluster {c['name']}, with error:\n{resp} - {resp.text}")
            return True
        except TypeError as te:
            self.log.error(
                f"Group {full_path} (ID: {old_id}) clusters {resp} {te}")
            return False
        except RequestException as re:
            self.log.error(
                f"Failed to migrate group {full_path} (ID: {old_id}) clusters, with error:\n{re}")
            return False

    def migrate_project_clusters(self, old_id, new_id, path, enabled):
        try:
            if enabled:
                resp = self.projects_api.get_all_project_clusters(
                    old_id, self.config.source_host, self.config.source_token)
                clusters = iter(resp)
                self.log.info(
                    f"Migrating project {path} (ID: {old_id}) clusters")
                for c in clusters:
                    if is_error_message_present(c) or not c:
                        self.log.error(
                            f"Failed to fetch project {path} (ID: {old_id}) cluster ({c['name']})")
                        return False
                    resp = self.projects_api.add_project_cluster(
                        new_id, self.config.destination_host, self.config.destination_token, data=self.create_data(c, {}, "Project ", path=path))
                    if resp.status_code != 201:
                        self.log.error(
                            f"Failed to create project {path} (ID: {new_id}) cluster ({c['name']}), with error:\n{resp} - {resp.text}")
                return True
            else:
                self.log.info(
                    f"Clusters are disabled ({enabled}) for project {path}")
                return None
        except TypeError as te:
            self.log.error(
                f"Project {path} (ID: {old_id}) clusters {resp} {te}")
            return False
        except RequestException as re:
            self.log.error(
                f"Failed to migrate project {path} (ID: {old_id}) clusters, with error:\n{re}")
            return False

    def create_data(self, c, data, c_type, path=""):
        data["name"] = c["name"]
        data["domain"] = c["domain"]
        data["enabled"] = c.get("enabled", "true")
        data["managed"] = c.get("managed", "true")
        if c["management_project"]:
            # Find and retrieve management project ID on destination
            sp = safe_json_response(self.projects_api.get_project(
                c["management_project"]["id"], self.config.source_host, self.config.source_token))
            if sp and not is_error_message_present(sp):
                path = get_dst_path_with_namespace(sp)
                mp_id = self.projects.find_project_by_path(
                    self.config.destination_host, self.config.destination_token, path)
                if mp_id and not is_error_message_present(mp_id):
                    data["management_project_id"] = mp_id
                else:
                    self.log.warning(
                        f"{c_type}{path} cluster {c['name']} management project {path} NOT found on destination")
        data["environment_scope"] = c["environment_scope"]
        data["platform_kubernetes_attributes"] = {}
        data["platform_kubernetes_attributes"]["api_url"] = c["platform_kubernetes"]["api_url"]
        # Any value, cannot be empty
        data["platform_kubernetes_attributes"]["token"] = c["id"]
        data["platform_kubernetes_attributes"]["ca_cert"] = c["platform_kubernetes"]["ca_cert"]
        data["platform_kubernetes_attributes"]["namespace"] = c["platform_kubernetes"]["namespace"]
        data["platform_kubernetes_attributes"]["authorization_type"] = c["platform_kubernetes"]["authorization_type"]
        return data
