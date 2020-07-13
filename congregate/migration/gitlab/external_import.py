from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import migration_dry_run
from congregate.migration.gitlab.api.external_import import ImportApi

class ImportClient(BaseClass):
    def __init__(self):
        super(ImportClient, self).__init__()
        self.ext_import = ImportApi()

    def trigger_import_from_bb_server(self, project, dry_run=True):
        project_key, repo = self.get_project_repo_from_full_path(project["path_with_namespace"])
        data = {
            "bitbucket_server_url": self.config.external_source_url,
            "bitbucket_server_username": self.config.external_user_name,
            "personal_access_token": self.config.external_access_token,
            "bitbucket_server_project": project_key,
            "bitbucket_server_repo": repo
        }
        if self.config.dstn_parent_group_path:
            data["target_namespace"] = "#{self.config.dstn_parent_group_path}/#{project_key}"
        else:
            data["target_namespace"] = project_key
        
        if not dry_run:
            return self.ext_import.import_from_bitbucket_server(self.config.destination_host, self.config.destination_token, data)

        migration_dry_run("project", data)
        return {
            "id": None,
            "name": repo,
            "full_path": project["path_with_namespace"],
            "full_name": project["path_with_namespace"]
        }
    
    def get_project_repo_from_full_path(self, full_path):
        split = full_path.split("/")
        project = split[0]
        repo = split[1]
        return project, repo
