from congregate.helpers.base_class import BaseClass
from congregate.migration.gitlab.api.external_import import ImportApi

class ImportClient(BaseClass):
    def __init__(self):
        super(ImportClient, self).__init__()
        self.ext_import = ImportApi()

    def trigger_import_from_bb_server(self, project, repo):
        data = {
            "bitbucket_server_url": self.config.external_source_url,
            "bitbucket_server_username": self.config.external_user_name,
            "personal_access_token": self.config.external_user_token,
            "bitbucket_server_project": project,
            "bitbucket_server_repo": repo
        }
        if self.config.dstn_parent_group_path:
            data["targer_namespace"] = self.config.dstn_parent_group_path
        
        return self.ext_import.import_from_bitbucket_server(self.config.destination_host, self.config.destination_token, data)