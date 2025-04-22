from congregate.migration.bitbucket_cloud.api.base import BitBucketCloudApi


class ProjectsApi():
    def __init__(self):
        self.api = BitBucketCloudApi()

    def get_project(self, workspace_slug, project_key):
        """
        Retrieve the project matching the supplied project key within a specific workspace.

        Core REST API: https://developer.atlassian.com/cloud/bitbucket/rest/api-group-projects/#api-workspaces-workspace-projects-project-key-get
        """
        return self.api.generate_get_request(f"workspaces/{workspace_slug}/projects/{project_key}")

    def get_all_projects(self, workspace_slug):
        """
        Retrieve all projects within the specified workspace.

        Core REST API: https://developer.atlassian.com/cloud/bitbucket/rest/api-group-projects/#api-workspaces-workspace-projects-get
        """
        return self.api.list_all(f"workspaces/{workspace_slug}/projects")

    def get_all_project_repos(self, workspace_slug, project_key):
        """
        Retrieve all repositories from the project corresponding to the supplied projectKey.

        Core REST API: https://developer.atlassian.com/cloud/bitbucket/rest/api-group-repositories/#api-repositories-workspace-get
        """
        return self.api.list_all(f"repositories/{workspace_slug}?q=project.key%3D%22{project_key}%22")

    def get_all_project_users(self, workspace_slug, project_key):
        """
        Returns a paginated list of explicit user permissions for the given project. This endpoint does not support BBQL features.
        May return an empty array

        Core REST API: https://developer.atlassian.com/cloud/bitbucket/rest/api-group-projects/#api-workspaces-workspace-projects-project-key-permissions-config-users-get
        """
        return self.api.list_all(f"workspaces/{workspace_slug}/projects/{project_key}/permissions-config/users")

    def get_all_project_groups(self, workspace_slug, project_key):
        """
        Returns a paginated list of explicit group permissions for the given project. This endpoint does not support BBQL features.

        Core REST API: https://developer.atlassian.com/cloud/bitbucket/rest/api-group-projects/#api-workspaces-workspace-projects-project-key-permissions-config-groups-get
        """
        return self.api.list_all(f"workspaces/{workspace_slug}/projects/{project_key}/permissions-config/groups")
