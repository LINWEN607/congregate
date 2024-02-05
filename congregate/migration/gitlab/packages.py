from pathlib import Path
from requests.exceptions import RequestException
from congregate.helpers.base_class import BaseClass
from congregate.migration.gitlab.api.packages import PackagesApi
from congregate.migration.gitlab.api.pypi import PyPiPackagesApi
from congregate.migration.maven.maven_client import get_package, deploy_package
from congregate.migration.meta.api_models.pypi_package_data import PyPiPackageData
from congregate.helpers.grpc_utils import is_rpc_service_running


class PackagesClient(BaseClass):
    def __init__(self):
        self.packages = PackagesApi()
        self.pypi_packages = PyPiPackagesApi()
        super(PackagesClient, self).__init__()

    def migrate_project_packages(self, src_id, dest_id, project_name):
        grpc_service_running = is_rpc_service_running(f"{self.config.grpc_host}:{self.config.maven_port}")
        if not grpc_service_running:
            self.log.warning(f"Maven gRPC service is not running, skipping Maven packages")

        results = []
        try:
            for package in self.packages.get_project_packages(self.config.source_host, self.config.source_token, src_id):
                package_type = package.get('package_type')
                if package_type == 'generic':
                    self.migrate_generic_packages(src_id, dest_id, package, results)
                elif package_type == 'maven':
                    if grpc_service_running:
                        self.migrate_maven_packages(src_id, dest_id, package, project_name, results)
                elif package_type == 'pypi':
                    self.migrate_pypi_packages(src_id, dest_id, package, results)
                else:
                    self.log.warning(f"Skipping {package.get('name')}, type {package.get('package_type')} not supported")
                    results.append({'Migrated': False, 'Package': package.get('name')})
        except RequestException as re:
            self.log.error(
                f"Failed to get all packages for project {project_name} (ID:{src_id}) due to a request exception")
            self.log.debug(re)
        except Exception as e:
            self.log.error(
                f"Failed to get all packages for project {project_name} (ID:{src_id}) due to an exception")
            self.log.debug(e)
        return results

    def format_groupid(self, name):
        return '.'.join(name.split('/')[:-1])

    def format_artifactid(self, name):
        return name.split('/')[-1]

    def format_artifact(self, name, version):
        return f"{self.format_groupid(name)}:{self.format_artifactid(name)}:{version}"

    def get_maven_files_data(self, src_id, package):
        executable = None
        pom_file = None
        packaging = None
        try:
            for package_file in self.packages.get_package_files(self.config.source_host, self.config.source_token, src_id, package.get('id')):
                if Path(package_file.get('file_name')).suffix.lower() == '.pom':
                    pom_file = package_file['file_name']
                if Path(package_file.get('file_name')).suffix.lower() in ['.jar', '.war', '.ear']:
                    packaging = (Path(package_file.get('file_name')).suffix).strip(
                        '.').upper()
                    executable = package_file['file_name']
        except RequestException as re:
            self.log.error(
                f"Failed to retrieve package files for {package.get('name')} {package.get('version')} ")
            self.log.error(re)
        return executable, pom_file, packaging

    def migrate_generic_packages(self, src_id, dest_id, package, results):
        artifact = self.format_artifact(package['name'], package['version'])
        self.log.info(f"Attempting to download package: {artifact}")
        migration_status = True

        for package_file in self.packages.get_package_files(self.config.source_host, self.config.source_token, src_id, package.get('id')):
            response = self.packages.get_generic_package_file_contents(
                self.config.source_host, self.config.source_token, src_id, package['name'], package['version'], package_file['file_name'])
            file = response.content

            response = self.packages.upload_generic_package_file(
                self.config.destination_host, self.config.destination_token, dest_id, package['name'],
                package['version'], package_file['file_name'], data=file)

            if response.status_code != 201:
                self.log.info(f"Failed to migrate file {package_file['file_name']} in package {package['name']}")
                migration_status = False
            else:
                self.log.info(f"Successfully migrated file {package_file['file_name']} in package {package['name']}")

        results.append({'Migrated': migration_status, 'Package': artifact})

    def migrate_maven_packages(self, src_id, dest_id, package, project_name, results):
        executable, pom_file, packaging = self.get_maven_files_data(
            src_id, package)
        if executable and pom_file:
            artifact = self.format_artifact(
                package['name'], package['version'])
            self.log.info(
                f"Attempting to download package: ({artifact}) from project: ({project_name})")
            get_package_result = get_package(
                projectName=project_name,
                artifact=artifact,
                remoteRepositories=f"gitlab-src::::{self.config.source_host}/api/v4/projects/{src_id}/packages/maven"
            )
            if get_package_result[0] == 0:
                self.log.info(
                    f"Package ({artifact}) was successfully downloaded. Moving on to deploying package")
                deploy_package_result = deploy_package(
                    projectName=project_name,
                    groupId=self.format_groupid(package['name']),
                    artifactId=self.format_artifactid(package['name']),
                    version=package['version'],
                    packaging=packaging,
                    file=f"/opt/project_repositories/{project_name}/{package['name']}/{package['version']}/{executable.lower()}",
                    pomFile=f"/opt/project_repositories/{project_name}/{package['name']}/{package['version']}/{pom_file}",
                    repositoryId="gitlab-dest",
                    url=f"{self.config.destination_host}/api/v4/projects/{dest_id}/packages/maven"
                )
                if deploy_package_result[0] == 0:
                    self.log.info(
                        f"Package ({artifact}) was successfully deployed")
                    results.append({'Migrated': True, 'Package': artifact})

                else:
                    self.log.error(
                        f"Package ({artifact}) was not successfully deployed")
                    results.append({'Migrated': False, 'Package': artifact})
                    self.log.error(deploy_package_result[1])
            else:
                self.log.error(
                    f"Package ({artifact}) wasn't downloaded. Here is the stack trace \n {get_package_result[1]}")
                results.append({'Migrated': False, 'Package': artifact})
        else:
            self.log.info(
                f"Unable to find usable data (executable or pom file is missing) \n {package}")

    def migrate_pypi_packages(self, src_id, dest_id, package, results):
        version = package['version']
        package_name = package['name']
        artifact = self.format_artifact(package_name, version)
        
        self.log.info(f"Attempting to download package: {artifact}")
        migration_status = True

        for package_file in self.packages.get_package_files(self.config.source_host, self.config.source_token, src_id, package.get('id')):
            sha = package_file['file_sha256']
            file_name = package_file['file_name']
            response = self.pypi_packages.download_pypi_project_package(
                self.config.source_host, self.config.source_token, src_id, sha, file_name)
            file_content = response.content

            response = self.pypi_packages.upload_pypi_package(
                self.config.destination_host, self.config.destination_token, dest_id, PyPiPackageData(
                    filename=file_name,
                    file=file_content,
                    package_name=package_name,
                    version=version
                ))

            if response.status_code != 201:
                self.log.info(f"Failed to migrate file {package_file['file_name']} in package {package['name']}")
                migration_status = False
            else:
                self.log.info(f"Successfully migrated file {package_file['file_name']} in package {package['name']}")

        results.append({'Migrated': migration_status, 'Package': artifact})
