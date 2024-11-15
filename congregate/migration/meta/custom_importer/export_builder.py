'''
Utility functions for building a custom project export
'''

import os
import tempfile
from json import dumps
from git import Repo, GitCommandError
from congregate.migration.gitlab.api.instance import InstanceApi
from congregate.migration.meta.custom_importer.data_models.project_export import ProjectExport, ApprovalRules, \
    AutoDevops, CiCdSettings, CiPipelines, CommitNotes, ContainerExpirationPolicy, Issues, Labels, MergeRequests, \
    ProjectFeatures, ProjectMembers, ProtectedBranches, ProtectedTags, PushRule, Releases, SecuritySetting, UserContributions


class ExportBuilder():
    def __init__(self):
        self.export_dir = tempfile.TemporaryDirectory()

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
        cwd = os.getcwd()
        try:
            # Create a temporary directory for cloning
            with tempfile.TemporaryDirectory() as temp_dir:
                # Clone the repository
                repo = Repo.clone_from(clone_url, temp_dir, env={
                                       'GIT_SSL_NO_VERIFY': '1'})

                # Create the bundle
                bundle_path = f"{cwd}/{output_path}/project.bundle"
                repo.git.bundle('create', bundle_path, '--all')

            return bundle_path

        except GitCommandError as e:
            print(
                f"Git command error while creating bundle for {project_path}: {str(e)}")
            return False
        except Exception as e:
            print(f"Error creating Git bundle for {project_path}: {str(e)}")
            return False
    
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
