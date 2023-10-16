from copy import deepcopy as copy
from json import dumps
from congregate.migration.gitlab.api.base_api import GitLabApiWrapper

class BulkImportApi(GitLabApiWrapper):
    

    def start_new_bulk_import(self, host, token, data, message=None):
        """
        Import your projects from GitHub to GitLab via the API

        GitLab API Doc: https://docs.gitlab.com/ee/api/bulk_imports.html#start-a-new-group-or-project-migration

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: data: (str) Relevant data for the import (see docs above)
            :return: Response object containing the response to POST /bulk_imports

        """
    
        if not message:
            audit_data = copy(data)
            audit_data.pop("personal_access_token", None)
            audit_data.get('configuration', {}).pop('access_token', None)
            message = f"Triggering new group or project bulk import with data {audit_data}"
        print(f"\n\nDATA: {data}")
        return self.api.generate_post_request(host, token, "bulk_imports", dumps(data), description=message)
    
    def get_bulk_import_entities(self, host, token, id):
        """
        Get a list of all entities related to a bulk import request

        GitLab API Doc: https://docs.gitlab.com/ee/api/bulk_imports.html#list-group-or-project-migration-entities

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: id: (str) ID of the bulk import request
        """
        return self.api.list_all(host, token, f"bulk_imports/{id}/entities")

    def get_bulk_imports(self, host, token, data, query_params=""):
        """
        Get a list of all group or project migrations via the API

        GitLab API Doc: https://docs.gitlab.com/ee/api/bulk_imports.html#list-all-group-or-project-migrations

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: data: (str) Relevant data for the import (see docs above)
            :return: Response object containing the response to GET /bulk_imports


        """
        return self.api.list_all(host, token, f"bulk_imports{query_params}")
    

    def get_bulk_imports_id(self, host, token, id):
        """
        Get a specific import request from a single group or project migration details via the API
    
        GitLab API Doc: https://docs.gitlab.com/ee/api/bulk_imports.html#get-group-or-project-migration-details

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: data: (str) Relevant data for the import (see docs above)
            :return: Response object containing the response to GET /bulk_imports/:id/entities

        """
        return self.api.generate_get_request(host, token, f"bulk_imports/{id}")
    
    def get_bulk_import_entity_details(self, host, token, iid, eid):
        """
        Get a specific entity from a single group or project migration details via the API
    
        GitLab API Doc: https://docs.gitlab.com/ee/api/bulk_imports.html#get-group-or-project-migration-details

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: iid: (int) import request id
            :param: eid: (int) import entity id
            :return: Response object containing the response to GET /bulk_imports/:id/entities

        """
        return self.api.generate_get_request(host, token, f"bulk_imports/{iid}/entities/{eid}")
    
