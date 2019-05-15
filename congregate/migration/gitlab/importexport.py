from helpers.base_class import BaseClass
from helpers import api, misc_utils
from aws import AwsClient
from migration.gitlab.projects import ProjectsClient
from migration.gitlab.users import UsersClient
from migration.gitlab.groups import GroupsClient
from requests.exceptions import RequestException
from re import sub
from urllib import quote
from time import sleep
from os import remove, chdir, getcwd
from glob import glob
import json


class ImportExportClient(BaseClass):
    def __init__(self):
        super(ImportExportClient, self).__init__()
        self.aws = self.get_AwsClient()
        self.projects = ProjectsClient()
        self.users = UsersClient()
        self.groups = GroupsClient()
        self.keys_map = self.get_keys()

    def get_AwsClient(self):
        if "aws" in self.config.location:
            return AwsClient()
        return None

    def get_keys(self):
        if self.config.location == "filesystem-aws":
            return self.aws.get_s3_keys(self.config.bucket_name)
        return {}

    def get_export_status(self, host, token, id):
        return api.generate_get_request(host, token, "projects/%d/export" % id)

    def get_import_status(self, host, token, id):
        return api.generate_get_request(host, token, "projects/%d/import" % id)

    def wait_for_export_to_finish(self, host, token, id):
        exported = False
        total_time = 0
        skip = False
        while not exported:
            response = self.get_export_status(
                self.config.child_host, self.config.child_token, id)
            if response.status_code == 200:
                response = response.json()
                name = response["name"]
                status = response.get("export_status", "")
                if status == "finished":
                    self.log.info("%s has finished exporting" % name)
                    exported = True
                elif status == "failed":
                    self.log.error("Export failed for %s" % name)
                    break
                elif status == "none":
                    self.log.info("No export status could be found for %s" % name)
                    if skip is False:
                        self.log.info("Waiting 3 seconds before skipping")
                        sleep(3)
                        skip = True
                    else:
                        break
                else:
                    self.log.info("Waiting on %s to export" % name)
                    if total_time < 3600:
                        total_time += 1
                        sleep(1)
                    else:
                        self.log.info(
                            "Time limit exceeded. Going to attempt to download anyway")
                        exported = True
            else:
                self.log.info(
                    "Project doesn't exist. Skipping %s export" % name)
                exported = False
                break

        return exported

    def export_project_to_aws(self, id, name, namespace):
        name = "%s_%s.tar.gz" % (namespace, name)
        presigned_put_url = self.aws.generate_presigned_url(name, "PUT")
        upload = [
            "upload[http_method]=PUT",
            "upload[url]=%s" % quote(presigned_put_url)
        ]

        headers = {
            'Private-Token': self.config.child_token,
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        try:
            response = api.generate_post_request(
                self.config.child_host, self.config.child_token, "projects/%d/export" % id, "&".join(upload), headers=headers)
            return response
        except RequestException:
            return None

    def import_project(self, project):
        """
            Imports project to parent GitLab instance. Formats users, groups, migration info(aws, filesystem) during import process
        """
        if isinstance(project, str):
            project = json.loads(project)
        name = project["name"]
        filename = "%s_%s.tar.gz" % (project["namespace"], project["name"])
        override_params = [
            "override_params[description]=%s" % project["description"],
            "override_params[default_branch]=%s" % project["default_branch"]
        ]
        user_project = False
        if isinstance(project["members"], list):
            for member in project["members"]:
                if project["namespace"] == member["username"]:
                    user_project = True
                    #namespace = project["namespace"]
                    new_user = self.users.get_user(
                        member["id"], self.config.parent_host, self.config.parent_token).json()
                    namespace = new_user["username"]
                    self.log.info("%s is a user project belonging to %s. Attempting to import into their namespace" % (
                        project["name"], new_user))
                    break
            if not user_project:
                self.log.info("%s is not a user project. Attempting to import into a group namespace" % (
                    project["name"]))
                if self.config.parent_id is not None:
                    response = self.groups.get_group(
                        self.config.parent_id, self.config.parent_host, self.config.parent_token).json()
                    namespace = "%s/%s" % (response["full_path"],
                                           project["namespace"])
                else:
                    namespace = project["namespace"]
                    url = project["http_url_to_repo"]
                    strip = sub(r"http(s|)://.+(\.net|\.com|\.org)/", "", url)
                    another_strip = strip.split("/")
                    for ind, val in enumerate(another_strip):
                        if ".git" in val:
                            another_strip.pop(ind)
                    full_path = "/".join(another_strip)
                    self.log.info("Searching for %s" % full_path)
                    for group in api.list_all(self.config.parent_host, self.config.parent_token, "groups?search=%s" % project["namespace"]):
                        if group["full_path"].lower() == full_path.lower():
                            self.log.info("Found %s" % group["full_path"])
                            namespace = group["id"]
                            break

            exported = False
            import_response = None
            timeout = 0
            if self.config.location == "aws":
                presigned_get_url = self.aws.generate_presigned_url(
                    filename, "GET")
                import_response = self.aws.import_from_s3(
                    name, namespace, presigned_get_url, filename, override_params=override_params)
            elif self.config.location == "filesystem-aws":
                if self.config.allow_presigned_url is not None and self.config.allow_presigned_url is True:
                    self.log.info("Importing %s presigned_url" % filename)
                    presigned_get_url = self.aws.generate_presigned_url(
                        filename, "GET")
                    import_response = self.aws.import_from_s3(
                        name, namespace, presigned_get_url, filename, override_params=override_params)
                else:
                    self.log.info("Copying %s to local machine" % filename)
                    formatted_name = project["name"].lower()
                    download = "%s_%s.tar.gz" % (
                        project["namespace"], formatted_name)
                    downloaded_filename = self.keys_map.get(
                        download.lower(), None)
                    if downloaded_filename is None:
                        self.log.info("Continuing to search for filename")
                        placeholder = len(formatted_name)
                        for i in range(placeholder, 0, -1):
                            split_name = "%s_%s.tar.gz" % (
                                project["namespace"], formatted_name[:(i * (1))])
                            downloaded_filename = self.keys_map.get(
                                split_name.lower(), None)
                            if downloaded_filename is not None:
                                break
                    if downloaded_filename is not None:
                        import_response = self.aws.copy_from_s3_and_import(
                            name, namespace, downloaded_filename)

            self.log.info(import_response)
            import_id = None
            if import_response is not None and len(import_response) > 0:
                # self.log.info(import_response)
                import_response = json.loads(import_response)
                while not exported:
                    if import_response.get("id", None) is not None:
                        import_id = import_response["id"]
                    elif import_response.get("message", None) is not None:
                        if "Name has already been taken" in import_response.get("message"):
                            self.log.debug("Searching for %s" %
                                           project["name"])
                            search_response = api.search(
                                self.config.parent_host, self.config.parent_token, 'projects', project['name'])
                            if len(search_response) > 0:
                                for proj in search_response:
                                    if proj["name"] == project["name"] and project["namespace"] in proj["namespace"]["path"]:
                                        self.log.info("Found project")
                                        import_id = proj["id"]
                                        break
                            self.log.info(
                                "Project may already exist but it cannot be found. Ignoring %s" % project["name"])
                            return None
                        elif "404 Namespace Not Found" in import_response.get("message"):
                            self.log.info(
                                "Skipping %s. Will need to migrate later." % name)
                            import_id = None
                            break
                        elif "The project is still being deleted" in import_response.get("message"):
                            self.log.info(
                                "Previous project export has been targeted for deletion. Skipping %s" % project["name"])
                            import_id = None
                            break
                    if import_id is not None:
                        status = self.get_import_status(
                            self.config.parent_host, self.config.parent_token, import_id).json()
                        # self.log.info(status)
                        if status["import_status"] == "finished":
                            self.log.info(
                                "%s has been exported and import is occurring" % name)
                            exported = True
                            # TODO: Fix or remove soft-cutover option
                            # if self.config.mirror_username is not None:
                            #     mirror_repo(project, import_id)
                        elif status["import_status"] == "failed":
                            self.log.info("%s failed to import" % name)
                            exported = True
                    else:
                        if timeout < 3600:
                            self.log.info("Waiting on %s to upload" % name)
                            timeout += 1
                            sleep(1)
                        else:
                            self.log.info(
                                "Moving on to the next project. Time limit exceeded")
                            break
        else:
            self.log.error("Project doesn't exist. Skipping %s" % name)
            return None
        return import_id

    def export_import_thru_filesystem(self, id, name, namespace):
        working_dir = getcwd()
        self.log.info("Exporting %s to %s" %
                      (name, self.config.filesystem_path))
        api.generate_post_request(
            self.config.child_host, self.config.child_token, "projects/%d/export" % id, "")
        if working_dir != self.config.filesystem_path:
            chdir(self.config.filesystem_path)
        url = "%s/api/v4/projects/%d/export/download" % (
            self.config.child_host, id)
        filename = misc_utils.download_file(url, self.config.filesystem_path, headers={
                                            "PRIVATE-TOKEN": self.config.child_token})

        data = {
            "path": name,
            "file": "%s/downloads/%s" % (self.config.filesystem_path, filename),
            "namespace": namespace
        }

        return api.generate_post_request(self.config.parent_host, self.config.parent_token, "projects/import", data=data)

    def export_import_thru_fs_aws(self, id, name, namespace):
        testkey = "%s_%s.tar.gz" % (namespace, name)
        if self.keys_map.get(testkey.lower(), None) is None:
            self.log.info("Exporting %s to %s" %
                          (name, self.config.filesystem_path))
            self.log.info("Unarchiving %s" % name)
            self.projects.unarchive_project(
                self.config.child_host, self.config.child_token, id)
            api.generate_post_request(
                self.config.child_host, self.config.child_token, "projects/%d/export" % id, {})
            url = "%s/api/v4/projects/%d/export/download" % (
                self.config.child_host, id)

            exported = self.wait_for_export_to_finish(
                self.config.child_host, self.config.child_token, id)

            if exported:
                self.log.info("Downloading export")
                path_with_namespace = "%s_%s.tar.gz" % (
                    namespace, name)
                try:
                    filename = misc_utils.download_file(url, self.config.filesystem_path, path_with_namespace, headers={
                                                        "PRIVATE-TOKEN": self.config.child_token})
                    self.log.info("Copying %s to s3" % filename)
                    success = self.aws.copy_file_to_s3(filename)
                    if success:
                        self.log.info("Removing %s from downloads" % filename)
                        filepattern = sub(
                            r'\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{3}_', '', filename)
                        for f in glob("%s/downloads/*%s" %
                                      (self.config.filesystem_path, filepattern)):
                            remove(f)
                        # self.log.info("Archiving %s" % name)
                        # api.generate_post_request(
                        #     self.config.child_host, self.config.child_token, "projects/%d/archive" % id, {})
                except Exception as e:
                    self.log.error("Download or copy to S3 failed")
                    self.log.error(e)
        else:
            self.log.info("Export found. Skipping %s" % testkey)

        return success

    def export_import_thru_aws(self, id, name, namespace):
        # if isinstance(project_json, str):
        #     project_json = json.loads(project_json)
        exported = False
        self.log.debug("Searching for existing %s" % name)
        project_exists = False
        for proj in self.projects.search_for_project(self.config.parent_host, self.config.parent_token, name):
            if proj["name"] == name and namespace in proj["namespace"]["path"]:
                self.log.info("Project already exists. Skipping %s" % name)
                project_exists = True
                break
        if not project_exists:
            self.log.info(
                "%s could not be found in parent instance. Exporting project on child instance." % name)
            self.export_project_to_aws(id, name, namespace)
            exported = self.wait_for_export_to_finish(
                self.config.child_host, self.config.child_token, id)

        return exported
