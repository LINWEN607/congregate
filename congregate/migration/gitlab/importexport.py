from congregate.helpers.base_class import base_class
from congregate.helpers import api, misc_utils
from congregate.aws import aws_client
from congregate.migration.gitlab.projects import gl_projects_client
from requests.exceptions import RequestException
from re import sub
from urllib import quote
from time import sleep
from os import remove, chdir, getcwd
from glob import glob
import json

class gl_importexport_client(base_class):
    def __init__(self):
        self.aws = self.get_aws_client()
        self.projects = gl_projects_client()
        self.keys_map = self.get_keys()
        
    def get_aws_client(self):
        if "aws" in self.config.location:
            return aws_client()
        return None
    
    def get_keys(self):
        if self.config.location == "filesystem-aws":
            return self.aws.get_s3_keys(self.config.bucket_name)
        return {}
    
    def export_project(self, project):
        if isinstance(project, str):
            project = json.loads(project)
        name = "%s_%s.tar.gz" % (project["namespace"], project["name"])
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
            api.generate_post_request(self.config.child_host, self.config.child_token, "projects/%d/export" % project["id"], "&".join(upload), headers=headers)
        except RequestException:
            pass

    def import_project(self, project):
        """
            Imports project to parent GitLab instance. Formats users, groups, migration info(aws, filesystem) during import process
        """
        if isinstance(project, str):
            project = json.loads(project)
        name = project["name"]
        filename = "%s_%s.tar.gz" % (project["namespace"], project["name"])
        user_project = False
        if isinstance(project["members"], list):
            for member in project["members"]:
                if project["namespace"] == member["username"]:
                    user_project = True
                    #namespace = project["namespace"]
                    new_user = api.generate_get_request(self.config.parent_host, self.config.parent_token, "users/%d" % member["id"]).json()
                    namespace = new_user["username"]
                    self.l.logger.info("%s is a user project belonging to %s. Attempting to import into their namespace" % (project["name"], new_user))
                    break
            if not user_project:
                self.l.logger.info("%s is not a user project. Attempting to import into a group namespace" % (project["name"]))
                if self.config.parent_id is not None:
                    response = api.generate_get_request(self.config.parent_host, self.config.parent_token, "groups/%d" % self.config.parent_id).json()
                    namespace = "%s/%s" % (response["full_path"], project["namespace"])
                else:
                    namespace = project["namespace"]
                    url = project["http_url_to_repo"]
                    strip = sub(r"http(s|)://.+(\.net|\.com|\.org)/", "", url)
                    another_strip = strip.split("/")
                    for ind, val in enumerate(another_strip):
                        if ".git" in val:
                            another_strip.pop(ind)
                    full_path = "/".join(another_strip)
                    self.l.logger.info("Searching for %s" % full_path)
                    for group in api.list_all(self.config.parent_host, self.config.parent_token, "groups?search=%s" % project["namespace"]):
                        if group["full_parent_namespace"].lower() == full_path.lower():
                            self.l.logger.info("Found %s" % group["full_path"])
                            namespace = group["id"]
                            break
                    
            exported = False
            import_response = None
            timeout = 0
            if self.config.location == "aws":
                presigned_get_url = self.aws.generate_presigned_url(filename, "GET")
                import_response = self.aws.import_from_s3(name, namespace, presigned_get_url, filename)
            elif self.config.location == "filesystem-aws":
                if self.config.allow_presigned_url is not None and self.config.allow_presigned_url is True:
                    self.l.logger.info("Importing %s presigned_url" % filename)
                    presigned_get_url = self.aws.generate_presigned_url(filename, "GET")
                    import_response = self.aws.import_from_s3(name, namespace, presigned_get_url, filename)
                else:
                    self.l.logger.info("Copying %s to local machine" % filename)
                    formatted_name = project["name"].lower()
                    download = "%s_%s.tar.gz" % (project["namespace"], formatted_name)
                    downloaded_filename = self.keys_map.get(download.lower(), None)
                    if downloaded_filename is None:
                        self.l.logger.info("Continuing to search for filename")
                        placeholder = len(formatted_name)
                        for i in range(placeholder, 0, -1):
                            split_name = "%s_%s.tar.gz" % (
                                project["namespace"], formatted_name[:(i * (1))])
                            downloaded_filename = self.keys_map.get(split_name.lower(), None)
                            if downloaded_filename is not None:
                                break
                    if downloaded_filename is not None:
                        import_response = self.aws.copy_from_s3_and_import(
                            name, namespace, downloaded_filename)

            self.l.logger.info(import_response)
            import_id = None
            if import_response is not None and len(import_response) > 0:
                # self.l.logger.info(import_response)
                import_response = json.loads(import_response)
                while not exported:
                    if import_response.get("id", None) is not None:
                        import_id = import_response["id"]
                    elif import_response.get("message", None) is not None:
                        if "Name has already been taken" in import_response.get("message"):
                            self.l.logger.debug("Searching for %s" % project["name"])
                            search_response = api.search(self.config.parent_host, self.config.parent_token, 'projects', project['name'])
                            if len(search_response) > 0:
                                for proj in search_response:
                                    if proj["name"] == project["name"] and project["namespace"] in proj["namespace"]["path"]:
                                        self.l.logger.info("Found project")
                                        import_id = proj["id"]
                                        break
                            self.l.logger.info("Project may already exist but it cannot be found. Ignoring %s" % project["name"])
                            return None
                        elif "404 Namespace Not Found" in import_response.get("message"):
                            self.l.logger.info("Skipping %s. Will need to migrate later." % name)
                            import_id = None
                            break
                        elif "The project is still being deleted" in import_response.get("message"):
                            self.l.logger.info("Previous project export has been targeted for deletion. Skipping %s" % project["name"])
                            import_id = None
                            break
                    if import_id is not None:
                        status = api.generate_get_request(self.config.parent_host, self.config.parent_token, "projects/%d/import" % import_id).json()
                        # self.l.logger.info(status)
                        if status["import_status"] == "finished":
                            self.l.logger.info("%s has been exported and import is occurring" % name)
                            exported = True
                            # TODO: Fix or remove soft-cutover option
                            # if self.config.mirror_username is not None:
                            #     mirror_repo(project, import_id)
                        elif status["import_status"] == "failed":
                            self.l.logger.info("%s failed to import" % name)
                            exported = True
                    else:
                        if timeout < 3600:
                            self.l.logger.info("Waiting on %s to upload" % name)
                            timeout += 1
                            sleep(1)
                        else:
                            self.l.logger.info("Moving on to the next project. Time limit exceeded")
                            break
        else:
            self.l.logger.error("Project doesn't exist. Skipping %s" % name)
            return None
        return import_id


    def export_import_thru_filesystem(self, id, name, namespace):
        working_dir = getcwd()
        self.l.logger.info("Exporting %s to %s" % (name, self.config.filesystem_path))
        api.generate_post_request(self.config.child_host, self.config.child_token, "projects/%d/export" % id, "")
        if working_dir != self.config.filesystem_path:
            chdir(self.config.filesystem_path)
        url = "%s/api/v4/projects/%d/export/download" % (self.config.child_host, id)
        filename = misc_utils.download_file(url, self.config.filesystem_path, headers={"PRIVATE-TOKEN": self.config.child_token})

        data = {
            "path": name,
            "file": "%s/downloads/%s" % (self.config.filesystem_path, filename),
            "namespace": namespace
        }

        return api.generate_post_request(self.config.parent_host, self.config.parent_token, "projects/import", data=data)

    def export_import_thru_fs_aws(self, id, name, namespace):
        testkey = "%s_%s.tar.gz" % (namespace, name)
        if self.keys_map.get(testkey.lower(), None) is None:
            self.l.logger.info("Exporting %s to %s" % (name, self.config.filesystem_path))
            self.l.logger.info("Unarchiving %s" % name)
            self.projects.unarchive_project(self.config.child_host, self.config.child_token, id)
            api.generate_post_request(
                self.config.child_host, self.config.child_token, "projects/%d/export" % id, {})
            url = "%s/api/v4/projects/%d/export/download" % (
                self.config.child_host, id)
            exported = False
            total_time = 0
            while not exported:
                response = api.generate_get_request(
                    self.config.child_host, self.config.child_token, "projects/%d/export" % id)
                if response.status_code == 200:
                    response = response.json()
                    if response["export_status"] == "finished":
                        self.l.logger.info("%s has finished exporting" % name)
                        exported = True
                    elif response["export_status"] == "failed":
                        self.l.logger.error("Export failed for %s" % name)
                        break
                    else:
                        self.l.logger.info("Waiting on %s to export" % name)
                        if total_time < 3600:
                            total_time += 1
                            sleep(1)
                        else:
                            self.l.logger.info(
                                "Time limit exceeded. Going to attempt to download anyway")
                            exported = True
                else:
                    self.l.logger.info("Project doesn't exist. Skipping %s export" % name)
                    exported = False
                    break
            if exported:
                self.l.logger.info("Downloading export")
                path_with_namespace = "%s_%s.tar.gz" % (
                    namespace, name)
                try:
                    filename = misc_utils.download_file(url, self.config.filesystem_path, path_with_namespace, headers={"PRIVATE-TOKEN": self.config.child_token})
                    self.l.logger.info("Copying %s to s3" % filename)
                    success = self.aws.copy_file_to_s3(filename)
                    if success:
                        self.l.logger.info("Removing %s from downloads" % filename)
                        filepattern = sub(
                            r'\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{3}_', '', filename)
                        for f in glob("%s/downloads/*%s" %
                                        (self.config.filesystem_path, filepattern)):
                            remove(f)
                        # self.l.logger.info("Archiving %s" % name)
                        # api.generate_post_request(
                        #     self.config.child_host, self.config.child_token, "projects/%d/archive" % id, {})
                except Exception as e:
                    self.l.logger.error("Download or copy to S3 failed")
                    self.l.logger.error(e)
        else:
            self.l.logger.info("Export found. Skipping %s" % testkey)

            