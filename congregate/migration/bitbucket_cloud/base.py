from requests.exceptions import RequestException

from gitlab_ps_utils.misc_utils import remove_dupes_but_take_higher_access, strip_netloc, safe_json_response
from gitlab_ps_utils.dict_utils import dig
from congregate.helpers.base_class import BaseClass
from congregate.helpers.utils import is_dot_com
from congregate.migration.bitbucket_cloud.api.projects import ProjectsApi
from congregate.migration.bitbucket_cloud.api.repos import ReposApi
from congregate.migration.bitbucket_cloud.api.users import UsersApi


class BitBucketCloud(BaseClass):
    @classmethod
    def get_http_url_to_repo(cls, repo):
        repo_clone_links = dig(repo, 'links', 'clone', default=[{"href": ""}])
        if repo_clone_links[0]["name"] == "http":
            return repo_clone_links[0]["href"]
        return repo_clone_links[1]["href"]

    def __init__(self, subset=False):
        self.projects_api = ProjectsApi()
        self.repos_api = ReposApi()
        self.users_api = UsersApi()
        self.user_groups = {}
        self.repo_groups = {}
        self.project_groups = {}
        self.subset = subset
        self.skip_group_members = False
        self.skip_project_members = False
        super().__init__()

    def determine_visibility(self, is_public):
        # Only allow 'public' for migrations to GL self-managed
        return "public" if not is_dot_com(self.config.destination_host) and is_public else "private"
    
    def sync_processed_repos(self, uuid):
        """
        Synchronize processed repository IDs across processes
        """
        if hasattr(self, 'processed_repo_ids'):
            # If we track processed repos in this class, add this ID
            self.processed_repo_ids.add(uuid)

    def add_project_repos(self, repos, workspace_slug, project_key, mongo):
        """
        Add repositories for a given project
        """
        try:
            for repo in self.projects_api.get_all_project_repos(workspace_slug, project_key):
                # Clean the UUID for consistent format
                uuid = repo.get("uuid", "")
                if uuid and uuid.startswith("{") and uuid.endswith("}"):
                    uuid = uuid[1:-1]  # Remove the braces
                
                # Add the cleaned UUID to the repos list
                repos.append(uuid)
                
                # Insert the formatted repo into MongoDB
                mongo.insert_data(
                    f"projects-{strip_netloc(self.config.source_host)}",
                    self.format_repo(repo)
                )
                
            # Remove duplicate entries
            return list(set(repos))
        except RequestException as re:
            self.log.error(
                f"Failed to GET repos from project '{project_key}', with error:\n{re}")
            return None

        
    def format_project(self, project, mongo):
        # Clean the UUID by removing curly braces if present
        uuid = project.get("uuid", "")
        if uuid and uuid.startswith("{") and uuid.endswith("}"):
            uuid = uuid[1:-1]  # Remove the first and last characters (the braces)
        
        workspace_slug = dig(project, "workspace", "slug", default=self.config.src_parent_workspace)
        
        return {
            "name": project["name"],
            "id": uuid,
            "path": project.get("key", ""),
            "full_path": project.get("key", ""),
            "visibility": self.determine_visibility(project.get("public", False)),
            "description": project.get("description", ""),
            "groups": self.project_groups,
            "projects": [] if self.subset else self.add_project_repos([], workspace_slug, project.get("key", ""), mongo)
        }

    def format_repo(self, repo, project=False):
        """
        Format public and project repos.
        Leave project repo members empty ([]) as they are retrieved during staging.
        """
        repo_path = dig(repo, 'project', 'key') or self.config.src_parent_workspace
        namespace_id = dig(repo, 'project', 'uuid')[1:-1]
        self.repo_groups = {}
        
        # Clean the UUID by removing curly braces if present
        uuid = repo.get("uuid", "")
        if uuid and uuid.startswith("{") and uuid.endswith("}"):
            uuid = uuid[1:-1]  # Remove the first and last characters (the braces)
        
        # Get the repository URL
        http_url = dig(repo, "links", "html", "href", default="")
        
        # Clean the URL to remove any username in the format username@domain
        if http_url and '@' in http_url:
            # Split by protocol and the rest
            protocol_parts = http_url.split('://')
            if len(protocol_parts) == 2:
                protocol = protocol_parts[0]
                rest = protocol_parts[1]
                
                # Remove username part
                if '@' in rest:
                    rest = rest.split('@', 1)[1]
                
                # Reconstruct the URL
                http_url = f"{protocol}://{rest}"
        
        return {
            "id": uuid,
            "path": repo["slug"],
            "name": repo["name"],
            # "archived": repo.get("archived", False),
            "namespace": {
                "id": namespace_id,
                "path": repo_path,
                "name": repo_path,
                "kind": "group",
                "full_path": repo_path
            },
            "path_with_namespace": f"{repo_path}/{repo.get('slug')}",
            "visibility": "private" if repo.get("is_private") else "public",
            "description": repo.get("description", ""),
            # "members": [] if project else self.add_repo_users([], repo_path, repo.get("slug")),
            "groups": self.repo_groups,
            "default_branch": dig(repo, "mainbranch", "name", default="master"),
            "http_url_to_repo": http_url
        }