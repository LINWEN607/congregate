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
                            f"Failed to fetch source instance clusters ({c})")
                        break
                    if not dry_run:
                        if is_dot_com(self.config.destination_host) and self.config.dstn_parent_id:
                            self.groups_api.add_group_cluster(
                                self.config.dstn_parent_id, self.config.destination_host, self.config.destination_token, self.create_data(c, {}))
                        else:
                            self.instance_api.add_instance_cluster(
                                self.config.destination_host, self.config.destination_token, self.create_data(c, {}))
            except TypeError as te:
                self.log.error("Instance clusters {0} {1}".format(resp, te))
            except RequestException as re:
                self.log.error(
                    "Failed to migrate instance clusters, with error:\n{}".format(re))

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
                        f"Failed to fetch clusters ({c}) for group {full_path} (ID: {old_id})")
                    return False
                self.groups_api.add_group_cluster(
                    new_id, self.config.destination_host, self.config.destination_token, data=self.create_data(c, {}))
            return True
        except TypeError as te:
            self.log.error(
                f"Group {full_path} (ID: {old_id}) clusters {resp} {te}")
            return False
        except RequestException as re:
            self.log.error(
                f"Failed to migrate group {full_path} (ID: {old_id}) clusters, with error:\n{re}")
            return False

    def migrate_project_clusters(self, old_id, new_id, project, enabled):
        try:
            name = project["name"]
            if enabled:
                resp = self.projects_api.get_all_project_clusters(
                    old_id, self.config.source_host, self.config.source_token)
                clusters = iter(resp)
                self.log.info(
                    f"Migrating project {name} (ID: {old_id}) clusters")
                for c in clusters:
                    if is_error_message_present(c) or not c:
                        self.log.error(
                            f"Failed to fetch clusters ({c}) for project {name} (ID: {old_id})")
                        return False
                    self.projects_api.add_project_cluster(
                        new_id, self.config.destination_host, self.config.destination_token, data=self.create_data(c, {}))
                return True
            else:
                self.log.info(
                    f"Clusters are disabled ({enabled}) for project {name}")
                return None
        except TypeError as te:
            self.log.error(
                f"Project {name} (ID: {old_id}) clusters {resp} {te}")
            return False
        except RequestException as re:
            self.log.error(
                f"Failed to migrate project {name} (ID: {old_id}) clusters, with error:\n{re}")
            return False

    def create_data(self, c, data):
        data["name"] = c["name"]
        data["domain"] = c["domain"]
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
                        f"Cluster {c['name']} management project {path} NOT found on destination")
        data["environment_scope"] = c["environment_scope"]
        data["platform_kubernetes_attributes"] = {}
        data["platform_kubernetes_attributes"]["api_url"] = c["platform_kubernetes"]["api_url"]
        # Any value, cannot be empty
        data["platform_kubernetes_attributes"]["token"] = c["id"]
        data["platform_kubernetes_attributes"]["ca_cert"] = c["platform_kubernetes"]["ca_cert"]
        data["platform_kubernetes_attributes"]["namespace"] = c["platform_kubernetes"]["namespace"]
        data["platform_kubernetes_attributes"]["authorization_type"] = c["platform_kubernetes"]["authorization_type"]
        return data
