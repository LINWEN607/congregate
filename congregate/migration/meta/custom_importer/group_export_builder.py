import os
import tempfile
import tarfile
from shutil import rmtree
from json import dumps
from dataclasses import fields
from git import Repo, GitCommandError
from congregate.helpers.base_class import BaseClass
from congregate.migration.gitlab.api.instance import InstanceApi
from congregate.migration.meta.custom_importer.data_models.group_export import GroupExport
from congregate.migration.meta.custom_importer.data_models.group import Group
from congregate.helpers.migrate_utils import get_export_filename_from_namespace_and_name


class GroupExportBuilder(BaseClass):
    '''
        Utility class for building a custom group export

        This class handles the final construction of the group export with functions to:

        - Create the group export structure
        - Convert all tree dataclasses into ndjson files
        - Build the packaged tar.gz file
    '''

    def __init__(self, group, git_env=None):
        super().__init__()
        self.export_dir = tempfile.TemporaryDirectory()
        self.tree_path = os.path.join(self.export_dir.name, 'tree')
        os.makedirs(self.tree_path, exist_ok=True)
        self.group_path = os.path.join(self.export_dir.name, 'tree', 'groups', '1')
        os.makedirs(self.group_path, exist_ok=True)
        self.group = group

    def build_export(self, tree_export: GroupExport, group_metadata: Group):
        """
        Build a custom group export.

        This method creates a directory structure for the group export, including
        the group bundle, tree directory, snippets directory, and uploads directory.
        It also creates various NDJSON files containing the exported group data.

        :param tree_export: ProjectExport object containing the exported group data
        :param group_metadata: Project object containing the group metadata
        :param host: The GitLab host URL
        :param token: The access token for authentication
        """

        # Initialize ta counter for exported groups
        counter = 1

        # Create GITLAB_VERSION and GITLAB_REVISION files
        self.write_to_file('GITLAB_VERSION', self.get_gitlab_version(self.config.destination_host, self.config.destination_token))
        self.write_to_file('GITLAB_REVISION', self.get_gitlab_revision(self.config.destination_host, self.config.destination_token))

        # Create VERSION file
        self.write_to_file('VERSION', '0.2.4')

        # Create _all.ndjson with a single line containing '1'        
        self.write_to_file('_all.ndjson', str(counter), os.path.join(self.export_dir.name, 'tree', 'groups'))

        # Create <counter>.json
        self.write_to_file(f'{counter}.json', dumps(group_metadata.to_dict()), os.path.join(self.export_dir.name, 'tree', 'groups'))
        
        # Increment the counter for future use
        counter += 1

        # Create the tree directory
        self.create_tree_files(tree_export)

    def create_export_tar_gz(self):
        filename = get_export_filename_from_namespace_and_name(
                self.group['path'])
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

    def create_tree_files(self, export: GroupExport):
        """
        Create tree files for the group export.

        This method creates various NDJSON files containing the exported group data.
        Each file corresponds to a specific aspect of the group, such as approval rules,
        CI/CD settings, issues, merge requests, etc.

        :param export: ProjectExport object containing the exported group data
        """
        export_path = self.group_path
        for field in fields(export):
            # Create NDJSON files for each component of the export
            self.create_tree_ndjson(getattr(export, field.name), f"{export_path}/{field.name}.ndjson")

    def create_tree_ndjson(self, data, output_path):
        """
        Write tree data to an ndjson file
        """
        with open(output_path, "w") as f:
            if isinstance(data, dict):
                f.write(f"{dumps(data)}\n")
            elif isinstance(data, list):
                for item in data:
                    f.write(f"{dumps(item.to_dict())}\n")
            else:
                f.write('null')

    def write_to_file(self, file_path, data, root=None):
        base_path = self.export_dir.name if not root else root
        with open(base_path + "/" + file_path, "w") as f:
            f.write(data)

    