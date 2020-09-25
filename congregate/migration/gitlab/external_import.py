from time import sleep
from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import migration_dry_run, is_error_message_present, safe_json_response
from congregate.helpers.migrate_utils import get_dst_path_with_namespace
from congregate.migration.gitlab.api.external_import import ImportApi
from congregate.migration.gitlab.api.projects import ProjectsApi


class ImportClient(BaseClass):
    def __init__(self):
        super(ImportClient, self).__init__()
        self.ext_import = ImportApi()
        self.projects = ProjectsApi()

    def trigger_import_from_bb_server(self, project, dry_run=True):
        project_path = project["path_with_namespace"]
        project_key, repo = self.get_project_repo_from_full_path(project_path)
        data = {
            "bitbucket_server_url": self.config.source_host,
            "bitbucket_server_username": self.config.source_username,
            "personal_access_token": self.config.source_token,
            "bitbucket_server_project": project_key,
            "bitbucket_server_repo": repo
        }
        if self.config.dstn_parent_group_path:
            data["target_namespace"] = "{0}/{1}".format(
                self.config.dstn_parent_group_path, project_key)
        else:
            data["target_namespace"] = project_key

        if not dry_run:
            try:
                resp = self.ext_import.import_from_bitbucket_server(
                    self.config.destination_host, self.config.destination_token, data)
                if is_error_message_present(resp):
                    message = resp.get("message")
                    self.log.error(message)
                    return self.get_failed_result(project, message)
                return self.get_result_data(project, resp)
            except ValueError as e:
                self.log.error(
                    "Failed to import from bitbucket server due to %s" % e)
                return self.get_failed_result(project)
        else:
            data.pop("personal_access_token", None)
            migration_dry_run("project", data)
            return self.get_failed_result(project, data)

    def trigger_import_from_ghe(self, project, dry_run=True):
        data = {
            "personal_access_token": self.config.source_token,
            "repo_id": project["id"],
            "target_namespace": get_dst_path_with_namespace(project).rsplit("/", 1)[0]
        }

        if not dry_run:
            try:
                resp = self.ext_import.import_from_github(
                    self.config.destination_host, self.config.destination_token, data)
                if is_error_message_present(resp):
                    message = resp.get("message")
                    self.log.error(message)
                    return self.get_failed_result(project, message)
                return self.get_result_data(project, resp)
            except ValueError as ve:
                self.log.error(f"Failed to import from GitHub due to {ve}")
                return self.get_failed_result(project)
        else:
            data.pop("personal_access_token", None)
            migration_dry_run("project", data)
            return self.get_failed_result(project, data)
    
    def wait_for_project_to_import(self, full_path):
        total_time = 0
        wait_time = self.config.importexport_wait
        max_wait_time = self.config.max_export_wait_time
        while True:
            project_statistics = safe_json_response(
                self.projects.get_project_statistics(full_path, self.config.destination_host, self.config.destination_token))
            if project_statistics:
                if project_statistics.get("data", None) is not None:
                    if project_statistics["data"].get("project", None) is not None:
                        stats = project_statistics["data"]["project"]["statistics"]
                        if stats["commitCount"] > 0:
                            self.log.info(f"Git commits have been found for {full_path}. Import is complete")
                            return True
                        if (stats["storageSize"] > 0) or (stats['repositorySize'] > 0):
                            self.log.info(f"Project storage is greater than 0 for {full_path}. Import is complete")
                            return True
            if total_time > max_wait_time:
                self.log.error(f"Max import time exceeded for {full_path}. Skipping post-migration phase")
                return False
            self.log.info(f"Waiting for project {full_path} to import")
            sleep(wait_time)
            total_time += wait_time


    def get_project_repo_from_full_path(self, full_path):
        split = full_path.split("/")
        project = split[0]
        repo = split[1]
        return project, repo

    def get_result_data(self, project, response):
        return {
            project["path_with_namespace"]: {
                "repository": True if response.get("id", None) is not None else False,
                "response": response
            }
        }

    def get_failed_result(self, project, data=None):
        return {
            project["path_with_namespace"]: False,
            "data": data
        }
