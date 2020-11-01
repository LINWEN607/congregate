from requests.exceptions import RequestException

from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import is_error_message_present, safe_json_response
from congregate.helpers.migrate_utils import get_dst_path_with_namespace
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.projects import ProjectsClient


class ClustersClient(BaseClass):
    def __init__(self):
        self.projects_api = ProjectsApi()
        self.projects = ProjectsClient()
        super(ClustersClient, self).__init__()

    def migrate_instance_clusters(self, dry_run=True):
        pass

    def migrate_group_clusters(self, old_id, new_id, full_path):
        pass

    def migrate_project_clusters(self, old_id, new_id, project):
        try:
            name = project["name"]
            resp = self.projects_api.get_all_project_clusters(
                old_id, self.config.source_host, self.config.source_token)
            clusters = iter(resp)
            self.log.info(
                f"Migrating project {name} (ID: {old_id}) clusters".format(name, old_id))
            for c in clusters:
                if is_error_message_present(c) or not c:
                    self.log.error(
                        f"Failed to fetch clusters ({c}) for project {name} (ID: {old_id})")
                    return False
                data = {}
                data["name"] = c["name"]
                data["domain"] = c["domain"]
                if c["management_project"]:
                    # Find and retrieve management project ID on destination
                    sp = safe_json_response(self.projects_api.get_project(
                        c["management_project"]["id"], self.config.source_host, self.config.source_token))
                    if sp and not is_error_message_present(sp):
                        mp_id = self.projects.find_project_by_path(
                            self.config.destination_host, self.config.destination_token, get_dst_path_with_namespace(sp))
                        if mp_id and not is_error_message_present(mp_id):
                            data["management_project_id"] = mp_id
                data["environment_scope"] = c["environment_scope"]
                data["platform_kubernetes_attributes"] = {}
                data["platform_kubernetes_attributes"]["api_url"] = c["platform_kubernetes"]["api_url"]
                # Any value, cannot be empty
                data["platform_kubernetes_attributes"]["token"] = c["id"]
                data["platform_kubernetes_attributes"]["ca_cert"] = c["platform_kubernetes"]["ca_cert"]
                data["platform_kubernetes_attributes"]["namespace"] = c["platform_kubernetes"]["namespace"]
                data["platform_kubernetes_attributes"]["authorization_type"] = c["platform_kubernetes"]["authorization_type"]
                self.projects_api.add_project_cluster(
                    new_id, self.config.destination_host, self.config.destination_token, data)
            return True
        except TypeError as te:
            self.log.error(
                f"Project {name} (ID: {old_id}) clusters {resp} {te}")
            return False
        except RequestException as re:
            self.log.error(
                f"Failed to migrate project {name} (ID: {old_id}) clusters, with error:\n{re}")
            return False
