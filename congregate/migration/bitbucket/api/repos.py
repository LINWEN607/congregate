from congregate.migration.bitbucket.api.base import BitBucketServerApi


class ReposApi():
    def __init__(self):
        self.api = BitBucketServerApi()

    def get_all_repos(self):
        return self.api.list_all("repos")

    def get_all_repo_users(self, project_key, repo_slug):
        return self.api.list_all(f"projects/{project_key}/repos/{repo_slug}/permissions/users")

    def get_all_repo_groups(self, project_key, repo_slug):
        return self.api.list_all(f"projects/{project_key}/repos/{repo_slug}/permissions/groups")

    def get_repo_default_branch(self, project_key, repo_slug):
        return self.api.generate_get_request(f"projects/{project_key}/repos/{repo_slug}/branches/default")

    def get_repo_branch_permissions(self, project_key, repo_slug):
        return self.api.list_all(f"projects/{project_key}/repos/{repo_slug}/restrictions", branch_permissions=True)
