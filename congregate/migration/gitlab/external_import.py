import json

from time import sleep
from gitlab_ps_utils.misc_utils import is_error_message_present, safe_json_response
from gitlab_ps_utils.dict_utils import dig
from gitlab_ps_utils.json_utils import json_pretty

from congregate.helpers.base_class import BaseClass
from congregate.helpers.migrate_utils import migration_dry_run
from congregate.helpers.utils import is_dot_com, is_github_dot_com
from congregate.migration.gitlab.api.external_import import ImportApi
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.api.instance import InstanceApi
from congregate.migration.github.api.users import UsersApi as GitHubUsersApi


class ImportClient(BaseClass):
    def __init__(self):
        super().__init__()
        self.ext_import = ImportApi()
        self.projects = ProjectsApi()
        self.instance = InstanceApi()

    def trigger_import_from_bb_server(self, pwn, dst_pwn, tn, dry_run=True):
        """
        Use the built-in GitLab importer to start a BitBucket Server import.

            :param pwn: (str) Source path with namespace
            :param dst_pwn: (str) Destination path with namespace
            :param tn: (str) Full destination target namespace
            :return: (dict) Successful or failed result data
        """
        bbs_project_key, bbs_repo = self.get_project_repo_from_full_path(pwn)
        data = {
            "bitbucket_server_url": self.config.source_host,
            "bitbucket_server_username": self.config.source_username,
            "personal_access_token": self.config.source_token,
            "bitbucket_server_project": bbs_project_key,
            "bitbucket_server_repo": bbs_repo,
            "target_namespace": tn
        }

        if self.config.lower_case_project_path:
            data["new_name"] = bbs_repo.lower()

        if not dry_run:
            try:
                resp = self.ext_import.import_from_bitbucket_server(
                    self.config.destination_host, self.config.destination_token, data)
                error, resp = is_error_message_present(resp)
                if error or not resp:
                    error = resp.get("message")
                    self.log.error(
                        f"Repo {bbs_repo} import to {tn} failed with response {resp} and error {error}")
                    return self.get_failed_result(dst_pwn, error)
                return self.get_result_data(dst_pwn, resp)
            except ValueError as ve:
                self.log.error(
                    f"Failed to import repo {bbs_repo} to {tn} due to {ve}")
                return self.get_failed_result(dst_pwn)
        else:
            data.pop("personal_access_token", None)
            migration_dry_run("project", data)
            return self.get_failed_result(dst_pwn, data)

    def trigger_import_from_ghe(self, project, dst_pwn, tn, host, token, dry_run=True):
        """
        Use the built-in GitLab importer to start a GitHub Enterprise import.

            :param project: (dict) GitHub repository metadata
            :param dst_pwn: (str) Destination path with namespace
            :param tn: (str) Full destination target namespace
            :param host: (str) GitHub hostname
            :param token: (str) GitHub personal access token
            :return: (dict) Successful or failed result data
        """
        data = {
            "personal_access_token": token,
            "repo_id": project.get("id"),
            "target_namespace": tn
        }

        _, gh_repo = self.get_project_repo_from_full_path(
            project.get("path_with_namespace"))
        if self.config.lower_case_project_path:
            data["new_name"] = gh_repo.lower()

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
                if error or not resp:
                    errors = resp.get("message")
                    self.log.error(
                        f"Repo {gh_repo} import to {tn} failed with response {resp} and error {errors}")
                    return self.get_failed_result(dst_pwn, errors)
                return self.get_result_data(dst_pwn, resp)
            except ValueError as ve:
                self.log.error(
                    f"Failed to import repo {gh_repo} to {tn} due to {ve}")
                return self.get_failed_result(dst_pwn)
        else:
            data.pop("personal_access_token", None)
            migration_dry_run("project", data)
            return self.get_failed_result(dst_pwn, data)

    def wait_for_project_to_import(self, full_path):
        total_time = 0
        wait_time = self.config.export_import_status_check_time
        timeout = self.config.export_import_timeout
        imported, success = False, False
        while True:
            project_statistics = safe_json_response(
                self.projects.get_project_statistics(
                    full_path,
                    self.config.destination_host,
                    self.config.destination_token
                )
            )
            if project_statistics and project_statistics.get("data") is not None:
                if project_statistics["data"].get("project") is not None:
                    # Main criterion
                    status = dig(project_statistics, 'data',
                                 'project', 'importStatus', default="")
                    if status == "finished":
                        self.log.info(
                            f"Import status is marked as {status} for {full_path}")
                        imported = True
                    elif status == "failed":
                        self.log.error(
                            f"Import status is marked as {status} for {full_path}")
                        success = False
                        break
                    # Sub criteria
                    stats = dig(project_statistics, 'data',
                                'project', 'statistics')
                    if imported and stats["commitCount"] > 0:
                        self.log.info(
                            f"Git commits have been found for {full_path}. Import is complete")
                        success = True
                        break
                    if imported and ((stats["storageSize"] > 0) or (stats['repositorySize'] > 0)):
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
        """
        Split GitHib and BitBucket Server repo full path by project and repo
        """
        split = full_path.rsplit("/", 1)
        project = split[0]
        if self.config.lower_case_group_path:
            project = project.lower()
        repo = split[1]
        return project, repo

    def get_external_repo_import_status(self, host, token, pid):
        error, import_status = is_error_message_present(
            self.projects.get_project_import_status(host, token, pid))
        if error or not import_status:
            self.log.error(
                f"Repo {pid} import failed with status: {import_status.get('message')}")
            return import_status
        # Save to file to avoid outputing long lists to log
        failed_relations = import_status.pop(
            "failed_relations") if import_status.get("failed_relations") else None
        # Added to GitHub repo import responses as of GitLab 14.6
        stats = import_status.pop(
            "stats") if import_status.get("stats") else None

        # Save import_error, user rate_limit status, import stats and failed relations
        import_error = import_status.get("import_error")
        key = import_status.get("path_with_namespace")
        value = {
            "import_error": import_error,
            "gh_rate_limit_status": safe_json_response(GitHubUsersApi(self.config.source_host, self.config.source_token).get_rate_limit_status())
            if import_error else None,
            "stats": stats,
            "failed_relations": failed_relations
        }
        output = {key: value}

        self.log_repo_import_failure_or_diff(key, value)

        with open(f"{self.app_path}/data/logs/import_failed_relations.json", "a") as f:
            json.dump(output, f, indent=4)
        return import_status

    def log_repo_import_failure_or_diff(self, repo, status):
        '''
        Capture BitBucket Server and GitHub repo import failures
        '''
        # Log only import failure and immediately return
        if status.get("import_error") or status.get("failed_relations"):
            status.pop("stats", None)
            self.log.error(
                f"Failed repo {repo} import:\n{json_pretty(status)}")
            return
        # Capture import stats only and log in case of diff
        stats = status.get("stats")
        if stats and stats.get("fetched") != stats.get("imported"):
            for k in ["import_error", "gh_rate_limit_status", "failed_relations"]:
                status.pop(k, None)
            self.log.warning(
                f"Diff in repo {repo} import 'stats':\n{json_pretty(status)}")

    def get_result_data(self, path_with_namespace, response):
        return {
            path_with_namespace: {
                "repository": response.get("id") is not None,
                "response": response
            }
        }

    def get_failed_result(self, path_with_namespace, data=None):
        return {
            path_with_namespace: {
                "repository": False,
                "response": data
            }
        }
