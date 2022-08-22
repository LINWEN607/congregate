from pathlib import Path
from congregate.helpers.base_class import BaseClass
from congregate.migration.gitlab.api.packages import PackagesApi
from congregate.migration.maven.maven_client import get_package, deploy_package

class PackagesClient(BaseClass):
    def __init__(self):
        self.packages = PackagesApi()
        super(PackagesClient, self).__init__()

    def migrate_project_packages(self, src_id, dest_id, project_name):
        self.log.info(f"Migrating project {project_name}(ID:{src_id}) packages")
        results = []
        for package in self.packages.get_project_packages(self.config.source_host, self.config.source_token, src_id):
            if package.get('package_type') == 'maven':
                self.migrate_maven_packages(src_id, dest_id, package, project_name, results)
            else:
                self.log.info(f"{package.get('name')} is not a maven package (Package Type:{package.get('package_type')}) and thus not supported at this time, skipping")
            
        return not False in results

    def format_groupid(self, name):
        return '.'.join(name.split('/')[:-1])

    def format_artifactid(self, name):
        return name.split('/')[-1]

    def format_artifact(self, name, version ):
        return f"{self.format_groupid(name)}:{self.format_artifactid(name)}:{version}"

    def get_maven_files_data(self, src_id, package):
        executable = None
        pom_file = None
        packaging = None
        for package_file in self.packages.get_package_files(self.config.source_host, self.config.source_token, src_id, package.get('id')):
            if Path(package_file.get('file_name')).suffix.lower() == '.pom':
                pom_file = package_file['file_name']
            if Path(package_file.get('file_name')).suffix.lower() in ['.jar', '.war', '.ear']:
                packaging = (Path(package_file.get('file_name')).suffix).strip('.').upper()
                executable = package_file['file_name']
        return executable, pom_file, packaging

    def migrate_maven_packages(self, src_id, dest_id, package, project_name, results):
        executable, pom_file, packaging = self.get_maven_files_data(src_id, package)
        if executable and pom_file:
            artifact = self.format_artifact(package['name'], package['version'])
            self.log.info(f"Attempting to download package: ({artifact}) from project: ({project_name})")
            get_package_result = get_package(
                projectName=project_name,
                artifact=artifact,
                remoteRepositories=f"gitlab-src::::{self.config.source_host}/api/v4/projects/{src_id}/packages/maven"
            )
            if get_package_result[0] == 0:
                self.log.info(f"Package ({artifact}) was successfully downloaded. Moving on to deploying package")
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
                    self.log.info(f"Package ({artifact}) was successfully deployed")
                    results.append(True)
                else:
                    self.log.error(f"Package ({artifact}) was not successfully deployed")
                    results.append(False)
                    self.log.error(deploy_package_result[1])
            else:
                self.log.error(f"Package ({artifact}) wasn't downloaded. Here is the stack trace \n {get_package_result[1]}")
        else:
            self.log.info(f"Unable to find usable data (executable or pom file is missing) \n {package}")