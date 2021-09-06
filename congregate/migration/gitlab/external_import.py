from time import sleep
from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import is_error_message_present, safe_json_response
from congregate.helpers.dict_utils import dig
from congregate.helpers.migrate_utils import migration_dry_run
from congregate.helpers.utils import is_dot_com, is_github_dot_com
from congregate.migration.gitlab.api.external_import import ImportApi
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.api.instance import InstanceApi


class ImportClient(BaseClass):
    def __init__(self):
        super().__init__()
        self.ext_import = ImportApi()
        self.projects = ProjectsApi()
        self.instance = InstanceApi()

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
        tn = f"{self.config.dstn_parent_group_path or ''}/{project_key}".strip(
            "/")
        data["target_namespace"] = tn

        if self.config.lower_case_project_path:
            data["new_name"] = repo.lower()

        if not dry_run:
            try:
                resp = self.ext_import.import_from_bitbucket_server(
                    self.config.destination_host, self.config.destination_token, data)
                error, resp = is_error_message_present(resp)
                if error:
                    error = resp.get("error")
                    self.log.error(
                        f"Project {project_path} import to {tn} failed with response {resp} and error {error}")
                    return self.get_failed_result(tn, error)
                return self.get_result_data(tn, resp)
            except ValueError as ve:
                self.log.error(
                    f"Failed to import project {project_path} to {tn} due to {ve}")
                return self.get_failed_result(tn)
        else:
            data.pop("personal_access_token", None)
            migration_dry_run("project", data)
            return self.get_failed_result(tn, data)

    def trigger_import_from_ghe(
            self, pid, path_with_namespace, tn, host, token, dry_run=True):
        '''
        Use the GitLab built in importers to start a GitHub Enterprise import.

            :param project: (dict)? This should be a dictionary representing a project
            :param host: (str)
            :param token: (str)
            :return: (dict) Project and its response code

        '''
        data = {
            "personal_access_token": token,
            "repo_id": pid,
            "target_namespace": tn
        }

        # TODO: This condition needs to be moved to the __init__ function of this class
        # and properly handle non standard GitLab versions like RCs
        if not is_github_dot_com(host):
            data["github_hostname"] = f"{host.rstrip('/')}/api/v3" if is_dot_com(
                self.config.destination_host) else host
        if not dry_run:
            try:
                resp = self.ext_import.import_from_github(
                    self.config.destination_host, self.config.destination_token, data)
                error, resp = is_error_message_present(resp)
                if error:
                    errors = resp.get("errors")
                    self.log.error(
                        f"Project {path_with_namespace} import to {tn} failed with response {resp} and error {errors}")
                    return self.get_failed_result(path_with_namespace, errors)
                return self.get_result_data(path_with_namespace, resp)
            except ValueError as ve:
                self.log.error(
                    f"Failed to import project {path_with_namespace} to {tn} due to {ve}")
                return self.get_failed_result(path_with_namespace)
        else:
            data.pop("personal_access_token", None)
            migration_dry_run("project", data)
            return self.get_failed_result(path_with_namespace, data)

    def wait_for_project_to_import(self, full_path):
        total_time = 0
        wait_time = self.config.export_import_status_check_time
        timeout = self.config.export_import_timeout
        success = False
        while True:
            project_statistics = safe_json_response(
                self.projects.get_project_statistics(
                    full_path,
                    self.config.destination_host,
                    self.config.destination_token
                )
            )
            if project_statistics and project_statistics.get(
                    "data", None) is not None:
                if project_statistics["data"].get("project", None) is not None:
                    if dig(project_statistics, 'data', 'project',
                           'importStatus', default="") == "finished":
                        self.log.info(
                            f"Import Status is marked as finished for {full_path}. Import is complete")
                        success = True
                        break
                    stats = dig(project_statistics, 'data',
                                'project', 'statistics')
                    if stats["commitCount"] > 0:
                        self.log.info(
                            f"Git commits have been found for {full_path}. Import is complete")
                        success = True
                        break
                    if (stats["storageSize"] > 0) or (
                            stats['repositorySize'] > 0):
                        self.log.info(
                            f"Project storage is greater than 0 for {full_path}. Import is complete")
                        success = True
                        break
            if total_time >= timeout:
                self.log.error(
                    f"Max import time exceeded for {full_path}. Skipping post-migration phase")
                break
            self.log.info(f"Waiting for project {full_path} to import")
            total_time += wait_time
            self.log.info(
                f"Total time: {total_time}. Max time: {timeout}")
            sleep(wait_time)
        return success

    def get_project_repo_from_full_path(self, full_path):
        split = full_path.split("/")
        project = split[0]
        if self.config.lower_case_group_path:
            project = project.lower()
        repo = split[1]
        return project, repo

    def get_result_data(self, path_with_namespace, response):
        return {
            path_with_namespace: {
                "repository": response.get("id", None) is not None,
                "response": response
            }
        }

    def get_failed_result(self, path_with_namespace, data=None):
        return {
            path_with_namespace: {
                "repository": bool(data) if not data.get("error") else False,
                "response": data
            }
        }
