import os
import tempfile
import tarfile
from shutil import rmtree
from json import dumps
from dataclasses import fields
from git import Repo, GitCommandError
from congregate.helpers.base_class import BaseClass
from congregate.migration.gitlab.api.instance import InstanceApi
from congregate.migration.meta.custom_importer.data_models.project_export import ProjectExport
from congregate.migration.meta.custom_importer.data_models.project import Project
from congregate.helpers.migrate_utils import get_export_filename_from_namespace_and_name


class ExportBuilder(BaseClass):
    '''
        Utility class for building a custom project export

        This class handles the final construction of the project export with functions to:

        - Clone the git repo
        - Create a git repo bundle
        - Create the project export structure
        - Convert all tree dataclasses into ndjson files
        - Build the packaged tar.gz file
    '''

    def __init__(self, project, clone_url, git_env=None):
        super().__init__()
        self.export_dir = tempfile.TemporaryDirectory()
        self.tree_path = os.path.join(self.export_dir.name, 'tree')
        os.makedirs(self.tree_path, exist_ok=True)
        self.project_path = os.path.join(self.export_dir.name, 'tree', 'project')
        os.makedirs(self.project_path, exist_ok=True)
        self.clone_url = clone_url
        self.project = project
        self.git_env = git_env
        self.repo = None

    def build_export(self, tree_export: ProjectExport, project_metadata: Project):
        """
        Build a custom project export.

        This method creates a directory structure for the project export, including
        the project bundle, tree directory, snippets directory, and uploads directory.
        It also creates various NDJSON files containing the exported project data.

        :param tree_export: ProjectExport object containing the exported project data
        :param project_metadata: Project object containing the project metadata
        :param host: The GitLab host URL
        :param token: The access token for authentication
        """
        # Create git bundle
        if self.repo is None:
            self.repo = self.clone_repo(self.project_path, self.export_dir.name, self.clone_url)
        git_bundle_path = self.create_git_bundle(self.project, self.export_dir.name)
        if git_bundle_path:
            self.log.info(f"Created Git bundle at {git_bundle_path}")
        else:
            self.log.error(f"Failed to create Git bundle for {self.project['name']}")
            raise

        # Create snippets directory
        os.makedirs(os.path.join(self.export_dir.name, 'snippets'), exist_ok=True)

        # Create uploads directory
        os.makedirs(os.path.join(self.export_dir.name, 'uploads'), exist_ok=True)

        # Create GITLAB_VERSION and GITLAB_REVISION files
        self.write_to_file('GITLAB_VERSION', self.get_gitlab_version(self.config.destination_host, self.config.destination_token))
        self.write_to_file('GITLAB_REVISION', self.get_gitlab_revision(self.config.destination_host, self.config.destination_token))

        # Create VERSION file
        self.write_to_file('VERSION', '0.2.4')
        
        # Create project.json
        self.write_to_file('project.json', dumps(project_metadata.to_dict()), root=self.tree_path)
        
        # Create empty lfs objects json file. We can handle LFS objects after import
        self.write_to_file('lfs_objects.json', '{}')
        
        # Create the tree directory
        self.create_tree_files(tree_export)

    def create_export_tar_gz(self):
        filename = get_export_filename_from_namespace_and_name(
                self.project['namespace'], self.project['name'])
        with tarfile.open(f"{self.config.filesystem_path}/downloads/{filename}", mode="w:gz") as tar:
            for f in os.listdir(self.export_dir.name):
                tar.add(os.path.join(self.export_dir.name, f), arcname=f)
        return filename

    def get_gitlab_version(self, host, token):
        """
        Get the GitLab version from the specified host using the provided token.

        :param host: The GitLab host URL
        :param token: The access token for authentication
        :return: The GitLab version as a string, or None if the request fails
        """
        return InstanceApi().get_version(host, token).json()['version']

    def get_gitlab_revision(self, host, token):
        """
        Get the GitLab revision from the specified host using the provided token.

        :param host: The GitLab host URL
        :param token: The access token for authentication
        :return: The GitLab revision as a string, or None if the request fails
        """
        return InstanceApi().get_version(host, token).json()['revision']

    def create_git_bundle(self, project_path, output_path):
        """
        Create a Git bundle for a project repository.

        :param project_path: The full path of the project
        :param output_path: The path where the Git bundle will be saved
        :param host: The GitLab host URL
        :param token: The access token for authentication
        :return: True if the bundle was created successfully, False otherwise
        """
        # cwd = os.getcwd()
        if not self.git_env:
            self.git_env = {
                'GIT_SSL_NO_VERIFY': '1'
            }
        try:
            if self.repo:
                # Create the bundle
                bundle_path = f"{output_path}/project.bundle"
                self.repo.git.bundle('create', bundle_path, '--all')

                return bundle_path
            raise Exception("No repo cloned")

        except GitCommandError as e:
            self.log.error(
                f"Git command error while creating bundle for {project_path}: {str(e)}")
            return False
        except Exception as e:
            self.log.error(f"Error creating Git bundle for {project_path}: {str(e)}")
            return False
    
    def clone_repo(self, project_path, clone_url) -> Repo:
        if not self.git_env:
            self.git_env = {
                'GIT_SSL_NO_VERIFY': '1',
                'pull.rebase': 'false'
            }
        try:
            os.makedirs('repos', exist_ok=True)
            repos_dir = f'repos/{project_path}'
            # Clone the repository
            repo = Repo.clone_from(clone_url, repos_dir, env=self.git_env)
            repo.git.pull('--all')
            default_branch = repo.git.branch('--show-current')
            for branch in repo.git.branch('-a').split('\n'):
                name = branch.lstrip('*').lstrip().split('->')[0].rstrip().split('remotes/origin/')[-1]
                if name != 'HEAD':
                    repo.git.checkout(name, '-f')
                    repo.git.pull('origin', name)
            for tag in repo.tags:
                repo.git.checkout(tag.name, '-f')
                repo.git.pull('origin', tag.name)
            repo.git.checkout(default_branch)
            return repo

        except GitCommandError as e:
            self.log.error(
                f"Git command error while creating bundle for {project_path}: {str(e)}")
            return False
        except Exception as e:
            self.log.error(f"Error creating Git bundle for {project_path}: {str(e)}")
            return False
        
    def create_tree_files(self, export: ProjectExport):
        """
        Create tree files for the project export.

        This method creates various NDJSON files containing the exported project data.
        Each file corresponds to a specific aspect of the project, such as approval rules,
        CI/CD settings, issues, merge requests, etc.

        :param export: ProjectExport object containing the exported project data
        """
        export_path = self.project_path
        for field in fields(export):
            # Create NDJSON files for each component of the export
            self.create_tree_ndjson(getattr(export, field.name), f"{export_path}/{field.name}.ndjson")

    def create_tree_ndjson(self, data, output_path):
        """
        Write tree data to an ndjson file
        """
        with open(output_path, "w") as f:
            if isinstance(data, dict):
                f.write(f"{dumps(item.to_dict())}\n")
            elif isinstance(data, list):
                for item in data:
                    f.write(f"{dumps(item.to_dict())}\n")
            else:
                f.write('null')

    def write_to_file(self, file_path, data, root=None):
        base_path = self.export_dir.name if not root else root
        with open(base_path + "/" + file_path, "w") as f:
            f.write(data)

    def delete_cloned_repo(self):
        rmtree(f'repos/{self.project_path}')
    