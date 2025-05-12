import json

from time import sleep
from gitlab_ps_utils.misc_utils import is_error_message_present, safe_json_response
from gitlab_ps_utils.dict_utils import dig
from gitlab_ps_utils.json_utils import json_pretty
from gitlab_ps_utils.string_utils import deobfuscate

from congregate.helpers.base_class import BaseClass
from congregate.helpers.migrate_utils import migration_dry_run, sanitize_project_path
from congregate.helpers.utils import is_dot_com, is_github_dot_com
from congregate.migration.gitlab.api.external_import import ImportApi
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.api.instance import InstanceApi
from congregate.migration.github.api.users import UsersApi as GitHubUsersApi
from congregate.migration.gitlab.groups import GroupsClient

class ImportClient(BaseClass):
    def __init__(self):
        super().__init__()
        self.ext_import = ImportApi()
        self.projects = ProjectsApi()
        self.instance = InstanceApi()
        self.groups = GroupsClient()
        

    def trigger_import_from_repo(self, pn, dst_pwn, tn, project, dry_run=True):
        """
        Use the built-in GitLab importer to start a Azure Devops import.

            :param pwn: (str) Source path with namespace
            :param dst_pwn: (str) Destination path with namespace
            :param tn: (str) Full destination target namespace
            :return: (dict) Successful or failed result data
        """
        namespace_id = self.groups.find_group_id_by_path(self.config.destination_host, self.config.destination_token, pn)
        azure_repo = project.get("path")
        url = project.get("http_url_to_repo").rsplit("@")[1]
        token = deobfuscate(self.config.source_token)
        
        data = {
            "name": project.get("name"),
            "namespace_id": namespace_id,
            "import_url": "https://"+ self.config.source_username+token+"@"+ url,
            "initialize_with_readme": False
        }


        if not dry_run:
            try:
                resp = self.ext_import.import_from_azure(
                    self.config.destination_host, self.config.destination_token, data)
                error, resp = is_error_message_present(resp)
                if error or not resp:
                    error = resp.get("message")
                    self.log.error(
                        f"Repo {azure_repo} import to {tn} failed with response {resp} and error {error}")
                    return self.get_failed_result(dst_pwn, error)
                return self.get_result_data(dst_pwn, resp)
            except ValueError as ve:
                self.log.error(
                    f"Failed to import repo {azure_repo} to {tn} due to {ve}")
                return self.get_failed_result(dst_pwn)
        else:
            data.pop("personal_access_token", None)
            migration_dry_run("project", data)
            return self.get_failed_result(dst_pwn, data)

    
    def get_namespace_id(self, host, token, path):
        """
        Get namespace ID by path.
        
        :param host: GitLab host URL
        :param token: GitLab access token
        :param path: Namespace path
        :return: Namespace ID if found, None otherwise
        """
        return self.projects.get_namespace_id_by_full_path(host, token, path)
    
    def trigger_import_from_codecommit(self, repo_name, dst_pwn, tn, dry_run=True):
        """
        Use the built-in GitLab importer to start an AWS CodeCommit import.

        :param repo_name: (str) The name of the AWS CodeCommit repository.
        :param dst_pwn: (str) Destination path with namespace.
        :param tn: (str) Full destination target namespace.
        :param dry_run: (bool) If True, simulate the import without executing it.
        :return: (dict) Successful or failed result data.
        """
        src_aws_codecommit_username = self.config.src_aws_codecommit_username
        src_aws_codecommit_password = self.config.src_aws_codecommit_password
        src_aws_region = self.config.src_aws_region
        # Get the namespace info for the target namespace
        namespace_response = self.projects.get_namespace_id_by_full_path(
            self.config.destination_host,
            self.config.destination_token,
            tn
        )
        
        if not namespace_response:
            self.log.error(f"Could not find namespace for target namespace: {tn}")
            return self.get_failed_result(dst_pwn, "Invalid target namespace")

        namespace_id = namespace_response.get('id')
        if not namespace_id:
            self.log.error(f"Could not find namespace ID in response for target namespace: {tn}")
            return self.get_failed_result(dst_pwn, "Invalid target namespace")
      
    #   https://docs.gitlab.com/ee/administration/settings/import_and_export_settings.html#configure-allowed-import-sources
    
        data = {
            "name": repo_name,
            "path": repo_name.lower() if self.config.lower_case_project_path else repo_name,
            "namespace_id": namespace_id,
            "import_url": f'https://{src_aws_codecommit_username}:{src_aws_codecommit_password}@git-codecommit.{src_aws_region}.amazonaws.com/v1/repos/{repo_name}',
            "visibility": "private"
        }

        if not dry_run:
            try:
                resp = self.ext_import.import_from_codecommit(
                    self.config.destination_host, self.config.destination_token, data
                )
                error, resp = is_error_message_present(resp)
                if error or not resp:
                    error_message = resp.get("message", "Unknown error")
                    self.log.error(
                        f"Repo {repo_name} import to {tn} failed with response {resp} and error {error_message}"
                    )
                    return self.get_failed_result(dst_pwn, error_message)
                return self.get_result_data(dst_pwn, resp)
            except ValueError as ve:
                self.log.error(
                    f"Failed to import repo {repo_name} to {tn} due to {ve}"
                )
                return self.get_failed_result(dst_pwn)
        else:
            data.pop("import_url", None)  # Avoid logging sensitive data
            migration_dry_run("project", data)
            return self.get_failed_result(dst_pwn, data)
        
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
            "target_namespace": tn,
            "new_name": sanitize_project_path(bbs_repo, pwn)
        }

        if self.config.lower_case_project_path:
            data["new_name"] = data["new_name"].lower()

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
    
    def trigger_import_from_bitbucket_cloud(self, project, workspace, repo_slug, path_with_namespace, namespace, bb_username, bb_token, dry_run=True):
        """
        Trigger import from Bitbucket Cloud using GitLab's built-in importer
        """
        # Create import payload with correct parameter names
        import_data = {
            "bitbucket_username": bb_username,         # Changed from bitbucket_cloud_username
            "bitbucket_app_password": bb_token,        # Changed from bitbucket_cloud_app_password
            "repo_path": f"{workspace}/{repo_slug}",   # Added repo_path parameter
            "new_name": project.get('name', repo_slug),
            "target_namespace": namespace,
        }
        
        # Include optional parameters if available
        if project.get('description'):
            import_data["description"] = project.get('description')
        
        if project.get('visibility'):
            import_data["visibility"] = project.get('visibility')
        
        # Log the import attempt
        self.log.info(f"Triggering Bitbucket Cloud import for {workspace}/{repo_slug} to {namespace}")
        
        if dry_run:
            # Return a dry run result
            self.log.info(f"[DRY RUN] Would import Bitbucket Cloud repo {workspace}/{repo_slug} to {namespace}")
            return {path_with_namespace: {"response": "dry_run", "success": True}}
        
        # Make the API request to import the repository
        host = self.config.destination_host
        token = self.config.destination_token
        
        response = self.ext_import.import_from_bitbucket_cloud(
            host=host,
            token=token,
            data=import_data
        )
        
        # Process response
        if isinstance(response, dict) and response.get('id'):
            result = {path_with_namespace: {"response": response, "success": True}}
            self.log.info(f"Successfully initiated Bitbucket Cloud import for {workspace}/{repo_slug}")
        else:
            result = {path_with_namespace: {"response": response, "success": False}}
            self.log.error(f"Failed to import Bitbucket Cloud repo {workspace}/{repo_slug}: {response}")
        
        return result

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
        _, gh_repo = self.get_project_repo_from_full_path(
            project.get("path_with_namespace"))

        data = {
            "personal_access_token": token,
            "repo_id": project.get("id"),
            "target_namespace": tn,
            "new_name": sanitize_project_path(gh_repo, dst_pwn),
            # TODO: make configurable; use default values for now
            "optional_stages": {
                "single_endpoint_notes_import": False,
                "attachments_import": False,
                "collaborators_import": False
            },
            "timeout_strategy": "pessimistic"
        }

        if self.config.lower_case_project_path:
            data["new_name"] = data["new_name"].lower()

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
                    # Sub criteria - if repo statistics are populated
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
                        if stats["commitCount"] == 0:
                            self.log.warning(f"Git repo {full_path} is empty")
                        success = True
                        break
                    repository = dig(project_statistics, 'data',
                                     'project', 'repository')
                    if imported and repository.get("empty") is True:
                        self.log.info(
                            f"Repository is empty for {full_path}. Import is complete")
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

        # Save to file to avoid outputting long lists to log
        failed_relations = import_status.pop(
            "failed_relations") if import_status.get("failed_relations") else None
        key = import_status.get("path_with_namespace")
        stats = self.get_external_repo_import_stats(import_status, key)

        # Save import_error, user rate_limit status, import stats and failed relations
        import_error = import_status.get("import_error")
        import_status["stats"] = stats
        value = {
            "import_error": import_error,
            "gh_rate_limit_status": safe_json_response(GitHubUsersApi(self.config.source_host, self.config.source_token).get_rate_limit_status())
            if import_error and self.config.source_type.lower() == "github" else None,
            "stats": stats,
            "failed_relations": failed_relations
        }
        output = {key: value}

        self.log_repo_import_failure_or_diff(key, value)

        with open(f"{self.app_path}/data/logs/import_failed_relations.json", "a") as f:
            json.dump(output, f, indent=4)
        return import_status

    def get_external_repo_import_stats(self, import_status, full_path):
        if import_status.get("stats"):
            # Added to GitHub repo import responses as of GitLab 14.6
            stats = import_status.pop("stats")
        else:
            # Otherwise retrieve project statistics
            stats = safe_json_response(
                self.projects.get_project_statistics(
                    full_path,
                    self.config.destination_host,
                    self.config.destination_token
                )
            )
            stats = stats["data"]["project"]["statistics"] if stats and stats.get(
                "data") else None
        return stats

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
