import json

from re import sub
from urllib import quote
from time import sleep
from os import remove, chdir, getcwd
from glob import glob
from requests.exceptions import RequestException
from congregate.helpers.base_class import BaseClass
from congregate.helpers import api, misc_utils
from congregate.aws import AwsClient
from congregate.migration.gitlab.projects import ProjectsClient
from congregate.migration.gitlab.api.users import UsersApi
from congregate.migration.gitlab.api.groups import GroupsApi


class ImportExportClient(BaseClass):
    def __init__(self):
        super(ImportExportClient, self).__init__()
        self.aws = self.get_AwsClient()
        self.projects = ProjectsClient()
        self.users = UsersApi()
        self.groups = GroupsApi()
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

    def wait_for_export_to_finish(self, host, token, id, name):
        exported = False
        total_time = 0
        skip = False
        wait_time = self.config.importexport_wait
        while not exported:
            response = self.get_export_status(
                self.config.source_host, self.config.source_token, id)
            if response.status_code == 200:
                response = response.json()
                name = response["name"]
                status = response.get("export_status", "")
                if status == "finished":
                    self.log.info("Project {} has finished exporting".format(name))
                    exported = True
                elif status == "failed":
                    self.log.error("Project {} export failed".format(name))
                    break
                elif status == "none":
                    self.log.info(
                        "No export status could be found for project {}".format(name))
                    if skip is False:
                        self.log.info("Waiting {0}s before skipping project {1} export".format(wait_time, name))
                        sleep(wait_time)
                        skip = True
                    else:
                        break
                else:
                    self.log.info("Waiting {0}s for project {1} to export".format(wait_time, name))
                    if total_time < 3600:
                        total_time += wait_time
                        sleep(wait_time)
                    else:
                        self.log.info(
                            "Time limit exceeded. Going to attempt to download anyway")
                        exported = True
            else:
                self.log.info(
                    "Source project {} doesn't exist. Skipping export".format(name))
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
            'Private-Token': self.config.source_token,
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        try:
            response = api.generate_post_request(
                self.config.source_host, self.config.source_token, "projects/%d/export" % id, "&".join(upload),
                headers=headers)
            return response
        except RequestException:
            return None

    def import_project(self, project):
        """
            Imports project to destination GitLab instance.
            Formats users, groups, migration info (aws, filesystem) during import process.
        """
        if isinstance(project, str):
            project = json.loads(project)
        name = project["name"]
        filename = "%s_%s.tar.gz" % (project["namespace"], project["name"])
        override_params = {
            # to override the dash ("-") in import/export file path
            "name": project["name"],
            "description": project["description"],
            "shared_runners_enabled": project["shared_runners_enabled"],
            "wiki_access_level": project["wiki_access_level"],
            "issues_access_level": project["issues_access_level"],
            "merge_requests_access_level": project["merge_requests_access_level"],
            "builds_access_level": project["builds_access_level"],
            "snippets_access_level": project["snippets_access_level"],
            "repository_access_level": project["repository_access_level"],
            "archived": project["archived"]
        }
        user_project = False
        if isinstance(project["members"], list):
            # Determine if the project should be under a single user or group
            for member in project["members"]:
                if project["namespace"] == member["username"]:
                    user_project = True
                    # namespace = project["namespace"]
                    new_user = self.users.get_user(
                        member["id"], self.config.destination_host, self.config.destination_token).json()
                    namespace = new_user["username"]
                    self.log.info("%s is a user project belonging to %s. Attempting to import into their namespace" % (
                        project["name"], new_user))
                    break
            if not user_project:
                self.log.info("%s is not a user project. Attempting to import into a group namespace" % (
                    project["name"]))
                if self.config.parent_id is not None:
                    response = self.groups.get_group(
                        self.config.parent_id, self.config.destination_host, self.config.destination_token).json()
                    namespace = "%s/%s" % (response["full_path"],
                                           project["namespace"])
                    filename = "%s/%s_%s.tar.gz" % (
                        response["path"], project["namespace"], project["name"])

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
                    for group in api.list_all(self.config.destination_host, self.config.destination_token,
                                              "groups?search=%s" % project["namespace"]):
                        if isinstance(group, dict):
                            if group["full_path"].lower() == full_path.lower():
                                self.log.info("Found %s" % group["full_path"])
                                namespace = group["id"]
                                break

            exported = False
            # import_response = None
            timeout = 0

            import_response = self.attempt_import(filename, name, namespace, override_params, project)
            self.log.info("Import response: {}".format(import_response))

            import_results = self.get_import_id_from_import_response(import_response, exported, project, name, timeout)
            self.log.info(import_results)

            import_id = import_results["import_id"]
            exported = import_results["exported"]
            duped = import_results["duped"]

            import_results = self.dupe_reimport_worker(
                duped,
                self.config.append_project_suffix_on_existing_found,
                exported,
                filename,
                name,
                namespace,
                override_params,
                project,
                timeout
            )
            self.log.info("Import response (duped): {}".format(import_response))

            # From here, should just flow through to the import_id return at the end
        else:
            self.log.error("Project doesn't exist. Skipping %s" % name)
            return None
        return import_id

    def dupe_reimport_worker(
            self,
            duped,
            append_suffix_on_dupe,
            exported,
            filename,
            name,
            namespace,
            override_params,
            project,
            timeout
    ):
        # Issue 151
        # The exported check *should not* be needed, as it should be impossible to be exported and duped
        # but crazier things have happened
        if duped and append_suffix_on_dupe and not exported:
            # One of the few times we will retry an import
            # Some next-level hackery. If the project already "exists", append and _1 to it and try, again
            # Note: we only do this retry one time
            project["name"] = self.create_override_name(project["name"])
            self.log.info("Project name is {0}".format(project["name"]))

            import_response = self.attempt_import(
                filename,
                name,
                namespace,
                override_params,
                project
            )
            self.log.info(import_response)

            import_results = self.get_import_id_from_import_response(
                import_response, False, project, name, timeout)
            self.log.info(import_results)

            return import_results
        return None

    @staticmethod
    def create_override_name(current_project_name):
        return "".join([current_project_name, "_1"])

    def get_import_id_from_import_response(self, import_response, exported, project, name, timeout):
        import_id = None
        duped = False
        wait_time = self.config.importexport_wait
        value_error_count = 0
        if import_response is not None and len(import_response) > 0:
            import_response = json.loads(import_response)
            while not exported:
                if import_response.get("id", None) is not None:
                    import_id = import_response["id"]
                elif import_response.get("message", None) is not None:
                    if "Name has already been taken" in import_response.get("message"):
                        # issue 151.
                        self.log.debug("Searching for %s" % project["name"])
                        search_response = api.search(
                            self.config.destination_host, self.config.destination_token, 'projects', project['name'])
                        # Search for the project by name
                        if len(search_response) > 0:
                            if isinstance(search_response, list):
                                for proj in search_response:
                                    self.log.info(proj)
                                    if proj["name"] == project["name"] \
                                            and project["namespace"] in proj["namespace"]["path"]:
                                        self.log.info("Found project")
                                        import_id = proj["id"]
                                        duped = True
                                        self.log.info("Existing project found at id: {0}. "
                                                      "Setting duped status and returning."
                                                      .format(import_id))
                                        # Found a match, so dump out of the for loop
                                        # import_id (project id) and duped flag are set
                                        break
                        # We can get here via a search match, or by exhausting the dict
                        # We already log the duped message info when we find the dupe
                        # Reuse the not found message
                        if not duped:
                            self.log.warn(
                                "Project may already exist but it cannot be found. Ignoring %s"
                                % project["name"])
                            import_id = None
                        # Break out of the while, as we don't care about exported
                        break
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
                        self.config.destination_host, self.config.destination_token, import_id)
                    try:
                        if status.status_code == 200:
                            status_json = status.json()
                            if status_json["import_status"] == "finished":
                                self.log.info(
                                    "Project {} has been successfully imported".format(name))
                                exported = True
                                # TODO: Fix or remove soft-cutover option
                                # if self.config.mirror_username is not None:
                                #     mirror_repo(project, import_id)
                            elif status_json["import_status"] == "failed":
                                self.log.error("Project {0} failed to import ({1})".format(name, status_json["import_error"]))
                                exported = True
                            elif status_json["import_status"] != "started":
                                # If it is started, we just ignore the status
                                self.log.warn("Could not get import status: {0}".format(status_json))
                        else:
                            self.log.error("Import status code was {0}".format(status.status_code))
                        timeout += wait_time
                        sleep(wait_time)
                    except ValueError as e:
                        self.log.error(e)
                        self.log.error("Status content was {0}".format(status.content))
                        if value_error_count > 2:
                            self.log.error("ValueError failed twice. Moving on for {0}".format(import_id))
                            break
                        value_error_count += 1
                else:
                    if timeout < 3600:
                        self.log.info("Waiting {0}s for project {1} to import".format(wait_time, name))
                        timeout += wait_time
                        sleep(wait_time)
                    else:
                        self.log.warn(
                            "Moving on to the next project. Time limit exceeded")
                        break
        return {"import_id": import_id, "exported": exported, "duped": duped}

    def attempt_import(self, filename, name, namespace, override_params, project):
        import_response = None
        if self.config.location == "aws":
            presigned_get_url = self.aws.generate_presigned_url(
                filename, "GET")
            self.log.info("Importing {} from AWS presigned_url (aws mode)".format(filename))
            import_response = self.aws.import_from_s3(
                name, namespace, presigned_get_url, filename, override_params=override_params)
        elif self.config.location == "filesystem-aws":
            if bool(self.config.allow_presigned_url):
                presigned_get_url = self.aws.generate_presigned_url(
                    filename, "GET")
                self.log.info(
                    "Importing {} from AWS presigned_url (filesystem-aws mode)".format(filename))
                import_response = self.aws.import_from_s3(
                    name, namespace, presigned_get_url, filename, override_params=override_params)
            else:
                self.log.info("Copying {} to local machine".format(filename))
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
        elif self.config.location == "filesystem":
            with open("%s/downloads/%s" % (self.config.filesystem_path, filename), "rb") as f:
                data = {
                    "path": name.replace(" ", "_"),
                    "namespace": namespace
                }

                files = {
                    "file": (filename, f)
                }

                headers = {
                    "Private-Token": self.config.destination_token
                }

                resp = api.generate_post_request(self.config.destination_host, self.config.destination_token, "projects/import", data, files=files, headers=headers)
                import_response = resp.text
        return import_response

    def export_thru_filesystem(self, id, name, namespace):
        working_dir = getcwd()
        filename = "{0}_{1}.tar.gz".format(namespace, name)
        self.log.info("Exporting %s to %s" %
                      (name, self.config.filesystem_path))
        api.generate_post_request(
            self.config.source_host, self.config.source_token, "projects/%d/export" % id, "")
        if working_dir != self.config.filesystem_path:
            chdir(self.config.filesystem_path)
        url = "%s/api/v4/projects/%d/export/download" % (
            self.config.source_host, id)
        misc_utils.download_file(url, self.config.filesystem_path, headers={
            "PRIVATE-TOKEN": self.config.source_token}, filename=filename)

        return filename

    def export_thru_fs_aws(self, id, name, namespace):
        path_with_namespace = "%s_%s.tar.gz" % (namespace, name)
        if self.keys_map.get(path_with_namespace.lower(), None) is None:
            self.log.info("Unarchiving %s" % name)
            self.projects.projects_api.unarchive_project(
                self.config.source_host, self.config.source_token, id)
            self.log.info("Exporting %s to %s" %
                          (name, self.config.filesystem_path))
            api.generate_post_request(
                self.config.source_host, self.config.source_token, "projects/%d/export" % id, {})
            url = "%s/api/v4/projects/%d/export/download" % (
                self.config.source_host, id)

            exported = self.wait_for_export_to_finish(
                self.config.source_host, self.config.source_token, id, name)

            if exported:
                self.log.info("Downloading export")
                try:
                    filename = misc_utils.download_file(url, self.config.filesystem_path, path_with_namespace, headers={
                        "PRIVATE-TOKEN": self.config.source_token})
                    self.log.info("Copying %s to s3" % filename)
                    success = self.aws.copy_file_to_s3(filename)
                    if success:
                        self.log.info("Removing %s from downloads" % filename)
                        filepattern = sub(
                            r'\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{3}_', '', filename)
                        for f in glob("%s/downloads/*%s" %
                                      (self.config.filesystem_path, filepattern)):
                            remove(f)
                except Exception as e:
                    self.log.error("Download or copy to S3 failed")
                    self.log.error(e)
        else:
            self.log.info("Export found. Skipping %s" % path_with_namespace)

        return success

    def export_thru_aws(self, id, name, namespace, full_parent_namespace):
        exported = False
        self.log.debug("Searching for existing project {}".format(name))
        if self.config.strip_namespace_prefix:
            namespace = self.strip_namespace(full_parent_namespace, namespace)
        project_exists, _ = self.projects.find_project_by_path(self.config.destination_host,
                                                               self.config.destination_token, full_parent_namespace,
                                                               namespace, name)
        if not project_exists:
            self.log.info(
                "Project {} not found on destination instance. Exporting from source instance.".format(name))
            self.export_project_to_aws(id, name, namespace)
            exported = self.wait_for_export_to_finish(
                self.config.source_host, self.config.source_token, id, name)

        return exported

    def strip_namespace(self, full_parent_namespace, namespace):
        if len(full_parent_namespace.split("/")) > 1:
            if full_parent_namespace.split("/")[-1] == namespace.split("/")[0]:
                namespace = namespace.replace(namespace.split("/")[0] + "/", "")
        return namespace
