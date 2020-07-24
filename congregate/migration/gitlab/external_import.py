from base64 import b64encode
from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import migration_dry_run, deobfuscate, is_error_message_present
from congregate.migration.gitlab.api.external_import import ImportApi


class ImportClient(BaseClass):
    def __init__(self):
        super(ImportClient, self).__init__()
        self.ext_import = ImportApi()

    def trigger_import_from_bb_server(self, project, dry_run=True):
        project_path = project["path_with_namespace"]
        project_key, repo = self.get_project_repo_from_full_path(project_path)
        data = {
            "bitbucket_server_url": self.config.source_host,
            "bitbucket_server_username": self.config.source_username,
            "personal_access_token": deobfuscate(self.config.source_token),
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
                return self.get_failed_result(project, None)
        else:
            data["personal_access_token"] = b64encode(
                data["personal_access_token"])
            migration_dry_run("project", data)
            return self.get_failed_result(project, data)
            
    
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
    
    def get_failed_result(self, project, data):
        return {
            project["path_with_namespace"]: False,
            "data": data
        }
