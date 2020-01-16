import json

from re import sub
from urllib import quote
from time import sleep
from os import remove
from glob import glob
from requests.exceptions import RequestException
from congregate.helpers.base_class import BaseClass
from congregate.helpers import api
from congregate.helpers.misc_utils import download_file, migration_dry_run, get_dry_log
from congregate.aws import AwsClient
from congregate.migration.gitlab.projects import ProjectsClient
from congregate.migration.gitlab.groups import GroupsClient
from congregate.migration.gitlab.api.users import UsersApi
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.helpers.migrate_utils import get_project_filename, get_project_namespace, \
    is_user_project, get_member_id_for_user_project
from congregate.models.user_logging_model import UserLoggingModel


class ImportExportClient(BaseClass):
    def __init__(self):
        super(ImportExportClient, self).__init__()
        self.aws = self.get_AwsClient()
        self.projects = ProjectsClient()
        self.groups = GroupsClient()
        self.projects_api = ProjectsApi()
        self.groups_api = GroupsApi()
        self.users = UsersApi()
        self.groups = GroupsApi()
        self.keys_map = self.get_keys()

    def get_AwsClient(self):
        if self.config.location == "aws":
            return AwsClient()
        return None

    def get_keys(self):
        if self.config.location == "filesystem-aws":
            return self.aws.get_s3_keys(self.config.bucket_name)
        return {}

    def get_export_status(self, host, token, source_id, is_project=True):
        if is_project:
            return self.get_project_export_status(host, token, source_id)
        return self.get_group_export_status(host, token, source_id)

    def get_project_export_status(self, host, token, source_id):
        return api.generate_get_request(host, token, "projects/%d/export" % source_id)
    
    def get_group_export_status(self, host, token, source_id):
        return api.generate_get_request(host, token, "groups/%d/export" % source_id)
    
    def get_import_status(self, host, token, source_id):
        return api.generate_get_request(host, token, "projects/%d/import" % source_id)
    
    def wait_for_export_to_finish(self, source_id, name, is_project=True):
        exported = False
        total_time = 0
        skip = False
        wait_time = self.config.importexport_wait
        while not exported:            
            response = self.get_export_status(self.config.source_host, self.config.source_token, source_id, is_project)
            if response.status_code == 200:
                response = response.json()
                name = response["name"]
                status = response.get("export_status", "")
                if status == "finished":
                    self.log.info("%s %s has finished exporting", self.check_is_project_or_group_for_logging(is_project), name)
                    exported = True
                elif status == "failed":
                    self.log.error("%s %s export failed", self.check_is_project_or_group_for_logging(is_project), name)
                    break
                elif status == "none":
                    self.log.info(
                        "No export status could be found for %s %s", str(self.check_is_project_or_group_for_logging(is_project)).lower(), name)
                    if not skip:
                        self.log.info("Waiting %s seconds before skipping %s %s export", 
                                      str(wait_time), 
                                      str(self.check_is_project_or_group_for_logging(is_project)).lower(), 
                                      name)
                        sleep(wait_time)
                        skip = True
                    else:
                        break
                else:
                    self.log.info("Waiting %s seconds for %s %s to export", 
                                  str(wait_time), 
                                  str(self.check_is_project_or_group_for_logging(is_project)).lower(), 
                                  name)
                    if total_time < self.config.max_export_wait_time:
                        total_time += wait_time
                        sleep(wait_time)
                    else:
                        self.log.warning(
                            "Time limit exceeded. Going to attempt to download anyway")
                        exported = True
            else:
                self.log.info(
                    "SKIP: Export, source %s %s doesn't exist", 
                    str(self.check_is_project_or_group_for_logging(is_project)).lower(), 
                    name)
                exported = False
                break

        return exported

    def export_project_to_aws(self, pid, filename):
        presigned_put_url = self.aws.generate_presigned_url(filename, "PUT")
        upload = [
            "upload[http_method]=PUT",
            "upload[url]=%s" % quote(presigned_put_url)
        ]
        headers = {
            'Private-Token': self.config.source_token,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        try:
            response = self.projects_api.export_project(
                self.config.source_host,
                self.config.source_token,
                pid,
                data="&".join(upload),
                headers=headers)
            return response
        except RequestException, e:
            self.log.error("Failed to trigger project (ID: {0}) export as {1} with response {2}"
                .format(pid, filename, response))
            return None

    def export_to_aws(self, source_id, filename, is_project=True):
        presigned_put_url = self.aws.generate_presigned_url(filename, "PUT")
        upload = [
            "upload[http_method]=PUT",
            "upload[url]=%s" % quote(presigned_put_url)
        ]
        headers = {
            'Private-Token': self.config.source_token,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        try:
            if is_project:
                response = self.projects_api.export_project(
                    self.config.source_host,
                    self.config.source_token,
                    source_id,
                    data="&".join(upload),
                    headers=headers)
            else:
                response = self.groups_api.export_group(
                    self.config.source_host,
                    self.config.source_token,
                    source_id,
                    data="&".join(upload),
                    headers=headers)
            return response
        except RequestException, e:
            self.log.error("Failed to trigger %s (ID: %s) export as %s with response %s", 
                           str(self.check_is_project_or_group_for_logging(is_project)).lower(), 
                           str(source_id), 
                           filename, 
                           response)
            return None
        
    def import_project(self, project, dry_run=True):
        """
            Imports project to destination GitLab instance.
            Formats users, groups, migration info (aws, filesystem) during import process.
        """
        if project is None:
            self.log.error("SKIP: Import, the following project is NONE: {}".format(project))
            return None

        if isinstance(project, str):
            project = json.loads(project)

        name = project["name"]
        override_params = self.get_override_params(project)
        filename = get_project_filename(project)

        if is_user_project(project):
            member_id = get_member_id_for_user_project(project)
            # TODO: Needs to be some user remapping in this, as well
            #   as the username/namespace may exist on the source
            if member_id:
                new_user = self.users.get_user(
                    member_id,
                    self.config.destination_host,
                    self.config.destination_token).json()
                namespace = new_user["username"]
                self.log.info("{0}{1} is a USER project (owner: {2}). Attempting to import into their namespace"
                    .format(get_dry_log(dry_run), name, UserLoggingModel().get_logging_model(new_user)))
            else:
                self.log.error("USER project FOUND, but NO member ID returned for project {0}".format(name))
                return None
        else:
            namespace = get_project_namespace(project)
            self.log.info("%s%s is NOT a USER project. Attempting to import into a group namespace", get_dry_log(dry_run), name)
            if self.config.parent_id is None:
                # TODO: This section is for importing to top-level, non-user projects.
                #   Needs a going over. We know the parent_id case is solid
                #   but recent experience would suggest this part isn't as tight
                #   Certainly not the GitHost scenario
                full_path = self.get_full_path(project["http_url_to_repo"])
                self.log.info("Searching for namespace %s", full_path)
                for group in self.groups.search_for_group(
                        project["namespace"],
                        self.config.destination_host,
                        self.config.destination_token):
                    if isinstance(group, dict):
                        if group["full_path"].lower() == full_path.lower():
                            self.log.info("Found group {}".format(group["full_path"]))
                            namespace = group["id"]
                            break

        exported = False
        # import_response = None
        timeout = 0

        if not dry_run:
            import_response = self.attempt_import(filename, name, namespace, override_params, project)
            self.log.info("Project {0} (file: {1}) import response:\n{2}"
                .format(name, filename, import_response))

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
                timeout)
            self.log.info("Project {0} (file: {1}) import response (DUPED): {2}"
                .format(name, filename, import_response))
            return import_id
        else:
            self.log.info("DRY-RUN: Outputing project {0} (file: {1}) migration data to dry_run_project_migration.json"
                .format(name, filename))
            migration_dry_run("project", {
                "filename": filename,
                "name": name,
                "namespace": namespace,
                "override_params": override_params,
                "project": project})

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

    def get_override_params(self, project):
        return {
            "description": project["description"],
            "shared_runners_enabled": self.config.shared_runners_enabled,
            "wiki_access_level": project["wiki_access_level"],
            "issues_access_level": project["issues_access_level"],
            "merge_requests_access_level": project["merge_requests_access_level"],
            "builds_access_level": project["builds_access_level"],
            "snippets_access_level": project["snippets_access_level"],
            "repository_access_level": project["repository_access_level"],
            "archived": project["archived"]
        }

    def get_full_path(self, url):
        strip = sub(r"http(s|)://.+(\.net|\.com|\.org)/", "", url)
        another_strip = strip.split("/")
        for ind, val in enumerate(another_strip):
            if ".git" in val:
                another_strip.pop(ind)
        return "/".join(another_strip)

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
                    res = import_response.get("message")
                    if "Name has already been taken" in res:
                        # issue 151.
                        self.log.debug("Searching for %s" % project["name"])
                        search_response = api.search(
                            self.config.destination_host, self.config.destination_token, 'projects', project['name'])
                        # Search for the project by name
                        if len(search_response) > 0:
                            if isinstance(search_response, list):
                                for proj in search_response:
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
                            self.log.warning("IGNORE: Project {} may already exist but it cannot be found".format(project["name"]))
                            import_id = None
                        # Break out of the while, as we don't care about exported
                        break
                    elif "404 Namespace Not Found" in res:
                        self.log.info("SKIP: Project {0} will need to import later (response: {1})".format(name, res))
                        import_id = None
                        break
                    elif "The project is still being deleted" in res:
                        self.log.info("SKIP: Previous project {} export has been targeted for deletion".format(project["name"]))
                        import_id = None
                        break
                if import_id is not None:
                    status = self.get_import_status(
                        self.config.destination_host, self.config.destination_token, import_id)
                    try:
                        if status.status_code == 200:
                            status_json = status.json()
                            if status_json["import_status"] == "finished":
                                self.log.info("Project {} has been successfully imported".format(name))
                                exported = True
                                # TODO: Fix or remove soft-cutover option
                                # if self.config.mirror_username is not None:
                                #     mirror_repo(project, import_id)
                            elif status_json["import_status"] == "failed":
                                self.log.error(
                                    "Project {0} failed to import ({1})".format(name, status_json["import_error"]))
                                exported = True
                            elif status_json["import_status"] != "started":
                                # If it is started, we just ignore the status
                                self.log.warning("Could not get import status: {0}".format(status_json))
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
                        self.log.warning(
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
            if self.config.allow_presigned_url:
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
                    "path": name.replace(" ", "-"),
                    "namespace": namespace,
                    "name": name
                }

                files = {
                    "file": (filename, f)
                }

                headers = {
                    "Private-Token": self.config.destination_token
                }

                resp = api.generate_post_request(self.config.destination_host, self.config.destination_token,
                                                 "projects/import", data, files=files, headers=headers)
                import_response = resp.text
        return import_response

    def get_export_filename_from_namespace_and_name(self, namespace, name):
        return "{0}_{1}.tar.gz".format(namespace, name).lower()

    def export_thru_filesystem(self, pid, name, namespace):
        exported = False
        response = self.projects_api.export_project(self.config.source_host, self.config.source_token, pid)
        if response is None or response.status_code not in (200, 202):
            self.log.error("Failed to trigger project {0} (ID: {1}) export, with response '{2}'"
                .format(pid, name, response))
        else:
            exported = self.wait_for_export_to_finish(pid, name)

            if exported:
                url = "{0}/api/v4/projects/{1}/export/download".format(self.config.source_host, pid)
                download_file(
                    url,
                    self.config.filesystem_path,
                    filename=self.get_export_filename_from_namespace_and_name(namespace, name),
                    headers={"PRIVATE-TOKEN": self.config.source_token})
            else:
                self.log.error("Failed to export project {0} (ID: {1}), with export status '{2}'"
                    .format(name, pid, exported))
        return exported

    def export_thru_fs_aws(self, pid, name, namespace):
        path_with_namespace = "%s_%s.tar.gz" % (namespace, name)
        if self.keys_map.get(path_with_namespace.lower(), None) is None:
            self.log.info("Unarchiving %s" % name)
            self.projects.projects_api.unarchive_project(
                self.config.source_host, self.config.source_token, pid)
            self.log.info("Exporting %s to %s" %
                          (name, self.config.filesystem_path))
            self.projects_api.export_project(self.config.source_host, self.config.source_token, pid)
            url = "%s/api/v4/projects/%d/export/download" % (
                self.config.source_host, pid)

            exported = self.wait_for_export_to_finish(pid, name)

            if exported:
                self.log.info("Downloading export")
                try:
                    filename = download_file(url, self.config.filesystem_path, path_with_namespace, headers={
                        "PRIVATE-TOKEN": self.config.source_token})
                    self.log.info("Copying %s to s3", filename)
                    success = self.aws.copy_file_to_s3(filename)
                    if success:
                        self.log.info("Removing %s from downloads", filename)
                        filepattern = sub(
                            r'\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{3}_', '', filename)
                        for f in glob("%s/downloads/*%s" %
                                      (self.config.filesystem_path, filepattern)):
                            remove(f)
                except Exception as e:
                    self.log.error("Download or copy to S3 failed")
                    self.log.error(e)
        else:
            self.log.info("SKIP: Project {} export found".format(path_with_namespace))

        return success

    def export_group_thru_aws(self, group_id, group_name, full_parent_namespace):
        """
        Called from migrate to kick-off an export process. Calls export_to_aws.
        
        :param name: Entity name. This is the name of the group itself
        :param namespace: Namespace where the entity lives. It's direct parent.
        :param full_parent_namespace: Complete path of the parent namespace from source. So, if this group is group3
                                        in the structure `group1/group2/group3`, full_parent_namespace is `group1/group2`
        """
        exported = False
        
        # TODO: Should stripping parent matter in this scenario? Think we want to leave everything as is
        full_name_with_parent_namespace = "{0}/{1}".format(full_parent_namespace, group_name)
        self.log.info("Searching on destination for group %s (ID: %s)", full_name_with_parent_namespace, str(group_id))
        group_exists, dest_group_id = self.groups.find_group_by_path(
            self.config.destination_host,
            self.config.destination_token,
            full_name_with_parent_namespace
        )
        if group_exists:
            # Generating the presigned URL later down the line does the quote_plus work, and the AWS functions to generate
            # expect an *un*quote_plus string (even through S3 itself returns a quote_plus style string)
            # Also, the CLI commands expect no + and no encoding (for is_export_on_aws). So, leave the filename as the full path
            # Do that export thing
            self.log.info("Group %s (Source ID: %s) NOT found on destination.", full_name_with_parent_namespace, str(group_id))
            # Passing full_name_with_parent_namespace with no +, no encoding, not a quoted string
            response = self.export_to_aws(group_id, full_name_with_parent_namespace, False)
            if response is not None and response.status_code == 202:
                # TODO: We're going to need to see what the status looks like
                # TODO: Checking the export needs to know...?            
                export_status = self.wait_for_export_to_finish(group_id, group_name, is_project=False)

                # If export status is unknown lookup the file on AWS
                # Could be misleading, since it assumes the file is complete
                exported = export_status or self.aws.is_export_on_aws(full_name_with_parent_namespace)                
        else:
            self.log.info("SKIP: Group %s found on destination with source id %s and destination id %s", 
                          full_name_with_parent_namespace, str(group_id), str(dest_group_id))
        return exported
        
    def export_thru_aws(self, pid, name, namespace, full_parent_namespace):
        """
        Called from migrate to kick-off an export process. Calls export_to_aws.
        
        :param name: Entity name
        :param namespace: Namespace where the entity lives
        :param full_parent_namespace: Complete path of the parent namespace from source
        """
        exported = False
        if self.config.strip_namespace_prefix:
            namespace = self.strip_namespace(full_parent_namespace, namespace)
        filename = self.get_export_filename_from_namespace_and_name(namespace, name)
        full_name = "{0}/{1}".format(namespace, name)
        self.log.info("Searching on destination for project {0} (ID: {1})".format(full_name, pid))
        project_exists, dest_pid = self.projects.find_project_by_path(
            self.config.destination_host,
            self.config.destination_token,
            full_parent_namespace,
            namespace,
            name)
        if not project_exists:
            self.log.info("Project {0} (ID: {1}) NOT found on destination. Exporting from source..."
                .format(full_name, pid))
            response = self.export_to_aws(pid, filename, True)
            if response is not None and response.status_code == 202:
                export_status = self.wait_for_export_to_finish(pid, name)
                # If export status is unknown lookup the file on AWS
                # Could be misleading, since it assumes the file is complete
                exported = export_status or self.aws.is_export_on_aws(filename)
            else:
                self.log.error("Failed to export project {0} (ID: {1}), with response {2}".format(name, pid, response))
        else:
            self.log.info("SKIP: Project {0} (ID: {1}) found on destination".format(full_name, dest_pid))
        return exported

    def strip_namespace(self, full_parent_namespace, namespace):
        if len(full_parent_namespace.split("/")) > 1:
            if full_parent_namespace.split("/")[-1] == namespace.split("/")[0]:
                namespace = namespace.replace(namespace.split("/")[0] + "/", "")
        return namespace

    def check_is_project_or_group_for_logging(self, is_project):
        return "Project" if is_project else "Group"
        
