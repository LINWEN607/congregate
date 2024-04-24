from pathlib import Path
from requests.exceptions import RequestException
from congregate.helpers.base_class import BaseClass
from congregate.migration.gitlab.api.packages import PackagesApi
from congregate.migration.gitlab.api.pypi import PyPiPackagesApi
from congregate.migration.gitlab.api.maven import MavenPackagesApi
from congregate.migration.gitlab.api.npm import NpmPackagesApi
from congregate.helpers.package_utils import generate_pypi_package_payload, generate_npm_package_payload, extract_pypi_package_metadata, extract_npm_package_metadata, get_pkg_data, generate_npm_json_data, generate_custom_npm_tarball_url
from congregate.migration.meta.api_models.pypi_package import PyPiPackage
from congregate.migration.meta.api_models.npm_package import NpmPackage
from congregate.migration.meta.api_models.maven_package import MavenPackage


class PackagesClient(BaseClass):
    def __init__(self):
        self.packages = PackagesApi()
        self.pypi_packages = PyPiPackagesApi()
        self.maven_packages = MavenPackagesApi()
        self.npm_packages = NpmPackagesApi()
        super().__init__()

    def migrate_project_packages(self, src_id, dest_id, project_name):
        results = []
        try:
            for package in self.packages.get_project_packages(self.config.source_host, self.config.source_token, src_id):
                package_type = package.get('package_type')
                if package_type == 'generic':
                    self.migrate_generic_packages(
                        src_id, dest_id, package, results)
                elif package_type == 'maven':
                    self.migrate_maven_packages(
                        src_id, dest_id, package, project_name, results)
                elif package_type == 'pypi':
                    self.migrate_pypi_packages(
                        src_id, dest_id, package, results)
                elif package_type == 'npm':
                    self.migrate_npm_packages(
                        src_id, dest_id, package, results)
                else:
                    self.log.warning(
                        f"Skipping {package.get('name')}, type {package.get('package_type')} not supported")
                    results.append(
                        {'Migrated': False, 'Package': package.get('name')})
        except RequestException as re:
            self.log.error(
                f"Failed to get all project '{project_name}' (ID:{src_id}) packages, due to a request exception")
            self.log.debug(re)
        except Exception as e:
            self.log.error(
                f"Failed to get all project '{project_name}' (ID:{src_id}) packages, due to an exception")
            self.log.debug(e)
        return results

    def format_groupid(self, name):
        return '.'.join(name.split('/')[:-1])

    def format_artifactid(self, name):
        return name.split('/')[-1]

    def format_artifact(self, name, version):
        return f"{self.format_groupid(name)}:{self.format_artifactid(name)}:{version}"

    def get_maven_files_data(self, src_id, package, project_name, path):
        files = []
        found_executable = False
        found_pom = False

        try:
            for package_file in self.packages.get_package_files(self.config.source_host, self.config.source_token, src_id, package.get('id')):
                file_name = package_file.get('file_name')
                file_suffix = Path(file_name).suffix.lower()

                supported_extensions = ['.pom', '.jar', '.war', '.ear']

                if file_suffix in supported_extensions:
                    if file_suffix == '.pom':
                        found_pom = True
                    if file_suffix in ['.jar', '.war', '.ear']:
                        found_executable = True

                    self.log.info(
                        f"Attempting to download maven package: ({file_name}) from project: ({project_name})")

                    response = self.maven_packages.download_maven_project_package(
                        self.config.source_host, self.config.source_token, src_id, path, file_name)
                    file_content = response.content

                    files.append(MavenPackage(
                        content=file_content,
                        file_name=file_name
                    ))
        except RequestException as re:
            self.log.error(
                f"Failed to retrieve package files for '{package.get('name')}', version '{package.get('version')}'")
            self.log.error(re)
        return files, found_executable, found_pom

    def migrate_generic_packages(self, src_id, dest_id, package, results):
        artifact = self.format_artifact(package['name'], package['version'])
        self.log.info(f"Attempting to download package: {artifact}")
        migration_status = True

        for package_file in self.packages.get_package_files(self.config.source_host, self.config.source_token, src_id, package.get('id')):
            response = self.packages.get_generic_package_file_contents(
                self.config.source_host, self.config.source_token, src_id, package['name'], package['version'], package_file['file_name'])
            file = response.content

            response = self.packages.upload_generic_package_file(
                self.config.destination_host, self.config.destination_token, dest_id, package[
                    'name'],
                package['version'], package_file['file_name'], data=file)

            if response.status_code != 201:
                self.log.error(
                    f"Failed to migrate package '{package['name']}' file '{package_file['file_name']}':\n{response} - {response.text}")
                migration_status = False
            else:
                self.log.info(
                    f"Successfully migrated package '{package['name']}' file '{package_file['file_name']}'")

        results.append({'Migrated': migration_status, 'Package': artifact})

    def migrate_maven_packages(self, src_id, dest_id, package, project_name, results):
        """
        Migrates a maven package from source project to destination project.

        Parameters:
        - src_id: Identifier or path for the source project.
        - dest_id: Identifier or path for the destination project.
        - package: The package name to migrate.
        - results: A dictionary to store the results of the migration.
        """

        # Format properly the group, artifactId and version of the package to migrate
        groupId = self.format_groupid(package['name']).replace(
            "(", "").replace(")", "").replace("'", "").replace(",", "").replace(".", "/")
        artifactId = self.format_artifactid(package['name']).replace(
            "(", "").replace(")", "").replace("'", "").replace(",", "")
        version = package['version']
        path = f"{groupId}/{artifactId}/{version}"

        # Get the maven files included inside the package to migrate - This is the downloading process
        files, found_executable, found_pom = self.get_maven_files_data(
            src_id, package, project_name, path)
        migration_status = True

        # If we find both the pom and jar file, we can proceed to the migration
        if found_executable and found_pom:
            for file in files:
                # Check if the file doesn't exist in the destination instance yet as we don't want any duplicate
                response = self.maven_packages.download_maven_project_package(
                    self.config.destination_host, self.config.destination_token, dest_id, path, file.file_name)
                if response.status_code == 200:
                    self.log.info(
                        f"File '{file.file_name}' already exists in the destination instance. Skipping")
                else:
                    # Proceed to uploading the file, since it's not yet present in the destination instance for this specific package
                    response = self.maven_packages.upload_maven_package(
                        self.config.destination_host, self.config.destination_token, dest_id, path, file.content, file.file_name)
                    if response.status_code != 200:
                        self.log.error(
                            f"Failed to migrate package '{package['name']}' file '{file.file_name}':\n{response} - {response.text}")
                        migration_status = False
                    else:
                        self.log.info(
                            f"Successfully migrated package '{package['name']}' file '{file.file_name}'")

            results.append({'Migrated': migration_status,
                           'Package': package['name']})
        else:
            self.log.warning(
                f"Unable to find usable data (executable or pom file is missing) for package '{package}'")

    def migrate_pypi_packages(self, src_id, dest_id, package, results):
        version = package['version']
        package_name = package['name']
        artifact = self.format_artifact(package_name, version)

        self.log.info(f"Attempting to download package: {artifact}")
        migration_status = True

        metadata = {}
        files = []
        for package_file in self.packages.get_package_files(self.config.source_host, self.config.source_token, src_id, package.get('id')):
            sha = package_file['file_sha256']
            file_name = package_file['file_name']

            response = self.pypi_packages.download_pypi_project_package(
                self.config.source_host, self.config.source_token, src_id, sha, file_name)
            file_content = response.content

            files.append(PyPiPackage(
                content=file_content,
                file_name=file_name,
                sha256_digest=sha,
                md5_digest=package_file['file_md5']
            ))

            if file_name.endswith('.tar.gz'):
                metadata = extract_pypi_package_metadata(
                    get_pkg_data(file_content, 'PKG-INFO'))

        for package in files:
            package_data = generate_pypi_package_payload(package, metadata)

            response = self.pypi_packages.upload_pypi_package(
                self.config.destination_host, self.config.destination_token, dest_id, package_data)

            if response.status_code != 201:
                self.log.error(
                    f"Failed to migrate package '{package.file_name}' file '{package['file_name']}':\n{response} - {response.text}")
                migration_status = False
            else:
                self.log.info(
                    f"Successfully migrated package '{package.file_name}' file '{package['file_name']}'")

        results.append({'Migrated': migration_status, 'Package': artifact})

    def migrate_npm_packages(self, src_id, dest_id, package, results):
        """
        Migrates a npm package from source project to destination project.

        Parameters:
        - src_id: Identifier or path for the source project.
        - dest_id: Identifier or path for the destination project.
        - package: The package name to migrate.
        - results: A dictionary to store the results of the migration.

        This method updates the `package.json` of both projects and records the migration status.
        """
        version = package['version']
        package_name = package['name']
        artifact = self.format_artifact(package_name, version)

        self.log.info(f"Attempting to download npm package: {artifact}")
        migration_status = True

        metadata = {}
        for package_file in self.packages.get_package_files(self.config.source_host, self.config.source_token, src_id, package.get('id')):
            file_name = package_file['file_name']

            # Downloading the binary content file of the package
            response = self.npm_packages.download_npm_project_package(
                self.config.source_host, self.config.source_token, src_id, package_name, file_name)
            file_content = response.content

            # Download the package metadata (dists and versions)
            response = self.npm_packages.download_npm_package_metadata(
                self.config.source_host, self.config.source_token, src_id, package_name)
            package_metadata_bytes = response.content

            # Generate the tarball url for registry setup on the destination instance
            custom_tarball_url = generate_custom_npm_tarball_url(
                self.config.destination_host, dest_id, package_name, file_name)

            # Get the package dataclass
            package = NpmPackage(
                content=file_content,
                file_name=file_name,
                md5_digest=package_file['file_md5']
            )

            # If the package is a tarball, extract the metadata that will be later used to build the json data to upload on the destination instance
            if file_name.endswith('.tgz'):
                metadata = extract_npm_package_metadata(
                    get_pkg_data(file_content, 'package.json'))

            package_data = generate_npm_package_payload(package, metadata)

            # The json data that will be sent over the network and dropped in the package registry of the destination instance
            json_data = generate_npm_json_data(
                package_metadata_bytes, package_data, file_name, file_content, custom_tarball_url)

            # Uploading the data to the destination instance
            response = self.npm_packages.upload_npm_package(
                self.config.destination_host, self.config.destination_token, dest_id, json_data, package_data)

            # Handling response code
            if response.status_code == 403:
                self.log.info(
                    f"Package '{package.file_name}' already exists in the destination instance. Skipping")
            elif response.status_code != 200:
                self.log.error(
                    f"Failed to migrate package '{package.file_name}' file '{package_file['file_name']}':\n{response} - {response.text}")
                migration_status = False
            else:
                self.log.info(
                    f"Successfully migrated package '{package.file_name}' file '{package_file['file_name']}'")

        results.append({'Migrated': migration_status, 'Package': artifact})
