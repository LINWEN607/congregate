import os
import tempfile
import shutil
import subprocess
import requests
from pathlib import Path
from traceback import print_exc
from requests.exceptions import RequestException
from congregate.helpers.base_class import BaseClass
from congregate.migration.gitlab.api.users import UsersApi
from congregate.migration.gitlab.api.packages import PackagesApi
from congregate.migration.gitlab.api.pypi import PyPiPackagesApi
from congregate.migration.gitlab.api.maven import MavenPackagesApi
from congregate.migration.gitlab.api.npm import NpmPackagesApi
from congregate.migration.gitlab.api.helm import HelmPackagesApi
from congregate.helpers.utils import ProjectIdPrefixedLogger, download_file_with_encoding_fallback, temp_directory, is_dot_com, upload_file_with_encoding_fallback
from congregate.helpers.package_utils import generate_pypi_package_payload, generate_npm_package_payload, extract_pypi_package_metadata, extract_npm_package_metadata, get_pkg_data, generate_npm_json_data, generate_custom_npm_tarball_url, extract_pypi_wheel_metadata, compare_packages
from congregate.migration.meta.api_models.pypi_package import PyPiPackage
from congregate.migration.meta.api_models.npm_package import NpmPackage
from congregate.migration.meta.api_models.maven_package import MavenPackage


class PackagesClient(BaseClass):
    def __init__(self):
        self.packages = PackagesApi()
        self.pypi_packages = PyPiPackagesApi()
        self.maven_packages = MavenPackagesApi()
        self.npm_packages = NpmPackagesApi()
        self.helm_packages = HelmPackagesApi()
        self.users = UsersApi()
        super().__init__()

    def migrate_project_packages(self, src_id, dest_id, project_name):
        results = []

        try:
            # Fetch all packages once at the beginning
            all_source_packages = list(self.packages.get_project_packages(
                self.config.source_host, self.config.source_token, src_id
            ))
            self.log.info(f"Found {len(all_source_packages)} packages in source project {src_id}")
            
            all_dest_packages = list(self.packages.get_project_packages(
                self.config.destination_host, self.config.destination_token, dest_id
            ))
            self.log.info(f"Found {len(all_dest_packages)} packages in destination project {dest_id}")
            
            for package in all_source_packages:
                package_type = package.get('package_type')
                try:
                    if package_type == 'generic':
                        self.migrate_generic_packages(
                            src_id, dest_id, package, results,
                            all_source_packages=all_source_packages,
                            all_dest_packages=all_dest_packages
                        )
                    elif package_type == 'maven':
                        self.migrate_maven_packages(
                            src_id, dest_id, package, project_name, results
                        )
                    elif package_type == 'pypi':
                        self.migrate_pypi_packages(
                            src_id, dest_id, package, results
                        )
                    elif package_type == 'npm':
                        self.migrate_npm_packages(
                            src_id, dest_id, package, results
                        )
                    elif package_type == 'helm':
                        self.migrate_helm_packages(
                            src_id, dest_id, package, results
                        )
                    else:
                        self.log.warning(
                            f"Skipping {package.get('name')}, type {package.get('package_type')} not supported")
                        results.append(
                            {'Migrated': False, 'Package': package.get('name')})
                except Exception:
                    self.log.error(print_exc())
        except RequestException as re:
            self.log.error(
                f"Failed to get all project '{project_name}' (ID:{src_id}) packages, due to a request exception:\n{re}")
        except Exception as e:
            self.log.error(
                f"Failed to get all project '{project_name}' (ID:{src_id}) packages, due to an exception:\n{e}")
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

    def migrate_generic_packages(self, src_id, dest_id, package, results, all_source_packages=None, all_dest_packages=None):
        """
        Migrates generic packages with robust handling of file transfers.
        """
        # Size threshold for using curl instead of direct API
        LARGE_FILE_THRESHOLD = 90 * 1024 * 1024  # 90MB
        
        # Check if destination is GitLab.com (which has Cloudflare)
        is_gitlab_com = is_dot_com(self.config.destination_host)
        
        artifact = self.format_artifact(package['name'], package['version'])
        self.log.info(f"[Project SRC:{src_id} → DST:{dest_id}] Attempting to migrate package: {artifact}")
        
        # First, check if package already exists with matching files
        comparison = compare_packages(
            src_id=src_id,
            dest_id=dest_id,
            package_name=package['name'],
            package_version=package['version'],
            src_host=self.config.source_host,
            dest_host=self.config.destination_host,
            src_token=self.config.source_token,
            dest_token=self.config.destination_token,
            packages_api=self.packages,  # Changed parameter name here to match function definition
            logger=self.log,
            all_source_packages=all_source_packages,
            all_dest_packages=all_dest_packages
        )
        if comparison["match"]:
            self.log.info(f"[Project SRC:{src_id} → DST:{dest_id}] Package {package['name']} v{package['version']} already exists with matching files. Skipping.")
            results.append({'Migrated': True, 'Package': artifact})
            return True
        elif comparison["reason"] != "dest_not_found":
            self.log.info(f"[Project SRC:{src_id} → DST:{dest_id}] Package exists but doesn't match: {comparison['reason']} - {comparison['details']}")
        
        # Use context manager for temporary directory
        with temp_directory(prefix="gitlab_package_") as temp_dir:
            migration_status = True
            
            # Get all package files
            package_files = list(self.packages.get_package_files(
                self.config.source_host, 
                self.config.source_token, 
                src_id, 
                package.get('id')
            ))
            
            self.log.info(f"[Project SRC:{src_id} → DST:{dest_id}] Found {len(package_files)} files to migrate for package: {artifact}")
            
            # Process each file
            for package_file in package_files:
                file_name = package_file['file_name']
                file_size = package_file.get('size', 0)
                
                self.log.info(f"[Project SRC:{src_id} → DST:{dest_id}] Processing file: {file_name} (Size: {round(file_size/1024/1024, 2)} MB)")
                
                # Skip oversized files (GitLab.com has a 5GB limit)
                if is_gitlab_com and file_size > 5 * 1024 * 1024 * 1024:  # 5GB
                    self.log.error(f"[Project SRC:{src_id} → DST:{dest_id}] File '{file_name}' exceeds GitLab.com's 5GB size limit. Skipping.")
                    migration_status = False
                    continue
                
                # Set up the temp file path
                temp_file_path = os.path.join(temp_dir, file_name)
                
                # Build download URL base
                download_base_url = f"{self.config.source_host}/api/v4/projects/{src_id}/packages/generic/{package['name']}/{package['version']}"
                
                # Create a wrapped logger that includes project IDs
                project_logger = ProjectIdPrefixedLogger(self.log, src_id, dest_id)
                
                # Download the file using utility function
                download_success, actual_size, successful_encoding_type = download_file_with_encoding_fallback(
                    download_base_url, 
                    file_name, 
                    temp_file_path, 
                    self.config.source_token, 
                    logger=project_logger
                )
                
                if not download_success:
                    self.log.error(f"[Project SRC:{src_id} → DST:{dest_id}] All download encoding attempts failed for file: {file_name}")
                    migration_status = False
                    continue
                    
                # Verify the downloaded file size
                if actual_size != file_size and file_size > 0:
                    self.log.warning(f"[Project SRC:{src_id} → DST:{dest_id}] Downloaded file size ({actual_size}) differs from expected size ({file_size})")
                
                # Build upload URL base
                upload_base_url = f"{self.config.destination_host}/api/v4/projects/{dest_id}/packages/generic/{package['name']}/{package['version']}"
                
                # Determine if we should use curl (large files to GitLab.com)
                use_curl = is_gitlab_com and actual_size > LARGE_FILE_THRESHOLD
                
                # Upload the file using utility function
                upload_success = upload_file_with_encoding_fallback(
                    upload_base_url, 
                    file_name, 
                    temp_file_path, 
                    self.config.destination_token, 
                    actual_size, 
                    use_curl=use_curl, 
                    logger=project_logger
                )
                
                # Clean up the temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                
                if not upload_success:
                    self.log.error(f"[Project SRC:{src_id} → DST:{dest_id}] All upload attempts failed for file: {file_name}")
                    migration_status = False
        
        # All operations complete, report result
        results.append({'Migrated': migration_status, 'Package': artifact})
        return migration_status

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

        self.log.info(f"[Project SRC:{src_id} → DST:{dest_id}] Attempting to download package: {artifact}")
        migration_status = True

        # Check if package already exists in destination
        dest_packages = list(self.packages.get_project_packages(
            self.config.destination_host,
            self.config.destination_token,
            dest_id
        ))
        
        dest_package = next((p for p in dest_packages 
                            if p.get('name') == package_name 
                            and p.get('version') == version), None)
                            
        if dest_package:
            self.log.info(f"[Project SRC:{src_id} → DST:{dest_id}] Package {package_name} v{version} already exists in destination, will check files")
            
            # Get file lists to check
            dest_files = list(self.packages.get_package_files(
                self.config.destination_host,
                self.config.destination_token,
                dest_id,
                dest_package.get('id')
            ))
        else:
            dest_files = []

        metadata = {}
        files = []
        for package_file in self.packages.get_package_files(self.config.source_host, self.config.source_token, src_id, package.get('id')):
            sha = package_file['file_sha256']
            file_name = package_file['file_name']
            
            # Check if file already exists in destination
            if dest_files and any(df['file_name'] == file_name for df in dest_files):
                self.log.info(f"[Project SRC:{src_id} → DST:{dest_id}] File '{file_name}' already exists in destination. Skipping.")
                continue

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
            elif file_name.endswith('.whl'):
                metadata = extract_pypi_wheel_metadata(file_content)

        for package in files:
            package_data = generate_pypi_package_payload(package, metadata)

            response = self.pypi_packages.upload_pypi_package(
                self.config.destination_host, self.config.destination_token, dest_id, package_data)

            if response.status_code != 201:
                self.log.error(
                    f"[Project SRC:{src_id} → DST:{dest_id}] Failed to migrate package '{package.file_name}':\n{response} - {response.text}")
                migration_status = False
            else:
                self.log.info(
                    f"[Project SRC:{src_id} → DST:{dest_id}] Successfully migrated package '{package.file_name}'")

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
            
            if response.status_code != 200 or not response.content:  # Checking if there's an empty response
                self.log.warning(f"Unable to get package {package_name} file {file_name} from source instance. Skipping")
                continue
            
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
                package_metadata_bytes, package_data, file_name, file_content, version, custom_tarball_url)

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

    def migrate_helm_packages(self, src_id, dest_id, package, results):
        """
        Migrates a Helm package from source project to destination project.

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
        channel = 'stable'

        self.log.info(f"Attempting to download Helm package: {artifact}")
        migration_status = True
        src_user = self.users.get_current_user(self.config.source_host, self.config.source_token)
        dst_user = self.users.get_current_user(self.config.destination_host, self.config.destination_token)
        metadata = {}
        for package_file in self.packages.get_package_files(self.config.source_host, self.config.source_token, src_id, package.get('id')):
            file_name = package_file['file_name']
            response = self.helm_packages.transfer_helm_package(self.config.source_host, self.config.destination_host, 
                                                                self.config.source_token, self.config.destination_token, 
                                                                src_id, dest_id, 
                                                                src_user, dst_user, file_name)
            # Handling response code
            if response.status_code == 403:
                self.log.info(
                    f"Package '{file_name}' already exists in the destination instance. Skipping")
            elif response.status_code != 201:
                self.log.error(
                    f"Failed to migrate package '{file_name}':\n{response} - {response.text} - {response.url}")
                migration_status = False
            else:
                self.log.info(
                    f"Successfully migrated package '{file_name}'")

        results.append({'Migrated': migration_status, 'Package': artifact})