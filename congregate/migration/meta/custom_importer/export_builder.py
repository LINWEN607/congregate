'''
Utility class for building a custom project export
'''

import os
import tempfile
import tarfile
from json import dumps
from dataclasses import fields
from git import Repo, GitCommandError
from congregate.helpers.base_class import BaseClass
from congregate.migration.gitlab.api.instance import InstanceApi
from congregate.migration.meta.custom_importer.data_models.project_export import ProjectExport, ApprovalRules, \
    AutoDevops, CiCdSettings, CiPipelines, CommitNotes, ContainerExpirationPolicy, Issues, Labels, MergeRequests, \
    ProjectFeatures, ProjectMembers, ProtectedBranches, ProtectedTags, PushRule, Releases, SecuritySetting, UserContributions
from congregate.migration.meta.custom_importer.data_models.project import Project


class ExportBuilder(BaseClass):
    def __init__(self, project_name, clone_url, git_env=None):
        super().__init__()
        self.export_dir = tempfile.TemporaryDirectory()
        self.tree_path = os.path.join(self.export_dir.name, 'tree')
        os.makedirs(self.tree_path, exist_ok=True)
        self.project_path = os.path.join(self.export_dir.name, 'tree', 'project')
        os.makedirs(self.project_path, exist_ok=True)
        self.clone_url = clone_url
        self.project_name = project_name
        self.git_env = git_env

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
        git_bundle_path = self.create_git_bundle(self.project_name, self.export_dir.name, self.clone_url)
        if git_bundle_path:
            print(f"Created Git bundle at {git_bundle_path}")
        else:
            print(f"Failed to create Git bundle for {self.project_name}")
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

    def create_export_tar_gz(self, output_path, project_name):
        with tarfile.open(f"{output_path}/{project_name}.tar.gz", mode="w:gz") as tar:
            for f in os.listdir(self.export_dir.name):
                print(f)
                tar.add(os.path.join(self.export_dir.name, f), arcname=f)
            # tar.add(self.export_dir.name,arcname=os.path.basename(self.export_dir.name))

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

    def create_git_bundle(self, project_path, output_path, clone_url):
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
            # Create a temporary directory for cloning
            with tempfile.TemporaryDirectory() as temp_dir:
                # Clone the repository
                repo = Repo.clone_from(clone_url, temp_dir, env=self.git_env)

                # Create the bundle
                bundle_path = f"{output_path}/project.bundle"
                repo.git.bundle('create', bundle_path, '--all')

            return bundle_path

        except GitCommandError as e:
            print(
                f"Git command error while creating bundle for {project_path}: {str(e)}")
            return False
        except Exception as e:
            print(f"Error creating Git bundle for {project_path}: {str(e)}")
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
        print(data)
        with open(base_path + "/" + file_path, "w") as f:
            f.write(data)
    