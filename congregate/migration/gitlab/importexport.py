import json

from re import sub
from urllib import quote
from time import sleep
from os import remove
from glob import glob
from requests.exceptions import RequestException
from requests_toolbelt.multipart.encoder import MultipartEncoder
from congregate.helpers.base_class import BaseClass
from congregate.helpers import api
from congregate.helpers.misc_utils import download_file, migration_dry_run, get_dry_log, \
    is_error_message_present, check_is_project_or_group_for_logging, json_pretty, validate_name, is_dot_com
from congregate.aws import AwsClient
from congregate.migration.gitlab.projects import ProjectsClient
from congregate.migration.gitlab.groups import GroupsClient
from congregate.migration.gitlab.api.users import UsersApi
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.api.namespaces import NamespacesApi
from congregate.helpers.migrate_utils import get_project_namespace, is_user_project, get_user_project_namespace, \
    get_export_filename_from_namespace_and_name, get_dst_path_with_namespace, get_full_path_with_parent_namespace


class ImportExportClient(BaseClass):
    # Import rate limit, 30 within 5 minutes
    RATE_LIMIT_MSG = "This endpoint has been requested too many times"

    # Import responses for a project re-import while it's still being deleted
    DEL_ERR_MSGS = [
        "The project is still being deleted",
        "Name has already been taken",
        "Path has already been taken"
    ]
    # Import rate limit cool-off
    COOL_OFF_MINUTES = 5 * 1.1  # Padding

    def __init__(self):
        super(ImportExportClient, self).__init__()
        self.aws = self.get_AwsClient()
        self.projects = ProjectsClient()
        self.groups = GroupsClient()
        self.projects_api = ProjectsApi()
        self.groups_api = GroupsApi()
        self.users_api = UsersApi()
        self.namespaces_api = NamespacesApi()
        self.keys_map = self.get_keys()

    def get_AwsClient(self):
        if self.config.location == "aws":
            return AwsClient()
        return None

    def get_keys(self):
        if self.config.location == "filesystem-aws":
            return self.aws.get_s3_keys(self.config.bucket_name)
        return {}

    def get_export_status(self, src_id, is_project=True):
        if is_project:
            return self.projects_api.get_project_export_status(src_id, self.config.source_host, self.config.source_token)
        return self.get_group_export_status(src_id)

    def get_group_export_status(self, src_id):
        return api.generate_get_request(self.config.source_host, self.config.source_token, "groups/%d/export" % src_id)

    def wait_for_export_to_finish(self, source_id, name, is_project=True):
        exported = False
        total_time = 0
        wait_time = self.config.importexport_wait
        export_type = check_is_project_or_group_for_logging(is_project)
        while not exported:
            response = self.get_export_status(source_id, is_project)
            if response.status_code == 200:
                response = response.json()
                name = response["name"]
                status = response.get("export_status", None)
                if status == "finished":
                    self.log.info(
                        "{0} {1} has finished exporting".format(export_type, name))
                    exported = True
                elif status == "failed" or status =="none":
                    self.log.error(
                        "{0} {1} export failed".format(export_type, name))
                    break
                elif total_time < self.config.max_export_wait_time:
                    self.log.info("Checking {0} {1} export status in {2} seconds".format(
                        export_type.lower(), name, wait_time))
                    total_time += wait_time
                    sleep(wait_time)
                else:
                    self.log.error("{0} {1} export time limit exceeded, download status:\n{2}".format(
                        export_type, name, response))
                    break
            else:
                self.log.error("SKIP: Export, source {0} {1} doesn't exist:\n{2}".format(
                    export_type.lower(), name, response))
                break
        return exported

    def wait_for_group_download(self, gid):
        exported = False
        timer = 0
        wait_time = self.config.importexport_wait
        while True:
            response = self.groups_api.get_group_download_status(
                self.config.source_host, self.config.source_token, gid)
            if response.status_code == 200:
                exported = True
                break
            self.log.info(
                "Waiting {0} seconds for group {1} to export".format(wait_time, gid))
            sleep(wait_time)
            timer += wait_time
            if timer > self.config.max_export_wait_time:
                self.log.error(
                    "Time limit exceeded for exporting group {0}, due to:\n{1}".format(gid, response))
                break
        return exported

    def wait_for_group_import(self, path):
        group = False
        timer = 0
        wait_time = self.config.importexport_wait
        while True:
            gid = self.groups.find_group_by_path(
                self.config.destination_host, self.config.destination_token, path)
            if gid:
                group = self.groups_api.get_group(
                    gid, self.config.destination_host, self.config.destination_token).json()
                self.log.info(
                    "Group {0} imported successfully with ID {1}".format(path, gid))
                break
            self.log.info(
                "Waiting {0} seconds for group {1} to import".format(wait_time, path))
            sleep(wait_time)
            timer += wait_time
            if timer > self.config.max_export_wait_time:
                self.log.error(
                    "Time limit exceeded for importing group {}".format(path))
                break
        return group

    def get_export_response(self, source_id, data, headers, is_project):
        """
        Gets the export response for both project and group exports
        """
        response = None
        if is_project:
            response = self.projects_api.export_project(
                self.config.source_host,
                self.config.source_token,
                source_id,
                data=data,
                headers=headers)
        else:
            response = self.groups_api.export_group(
                self.config.source_host,
                self.config.source_token,
                source_id,
                data=data,
                headers=headers)
        return response

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
        data = "&".join(upload)
        try:
            response = self.get_export_response(
                source_id,
                data,
                headers,
                is_project
            )
            return response
        except RequestException, e:
            self.log.error("Failed to trigger {0} (ID: {1}) export as {2} with response {3}".format(
                check_is_project_or_group_for_logging(is_project).lower(), source_id, filename, response))
            return None

    def import_project(self, project, dry_run=True):
        """
            Imports project to destination GitLab instance.
            Formats users, groups, migration info (aws, filesystem) during import process.
        """
        if isinstance(project, str):
            project = json.loads(project)

        name = project["name"]
        path = project["path"]
        namespace = project["namespace"]
        members = project["members"]
        override_params = self.get_override_params(project)
        filename = get_export_filename_from_namespace_and_name(namespace, name)
        import_id = None

        if is_user_project(project):
            self.log.info("{0}{1} is a USER project ({2}). Attempting to import into their namespace".format(
                get_dry_log(dry_run), name, namespace))
            dst_namespace = get_user_project_namespace(project)
        else:
            self.log.info("{0}{1} is NOT a USER project. Attempting to import into a group namespace".format(
                get_dry_log(dry_run), name))
            dst_namespace = get_project_namespace(project)

        if not dry_run:
            import_response = self.attempt_import(
                filename, name, path, dst_namespace, override_params, members)
            # Use until group import status endpoint is available
            if "404 Namespace Not Found" in str(import_response):
                timeout = 0
                wait_time = self.config.importexport_wait
                while self.namespaces_api.get_namespace_by_full_path(dst_namespace, self.config.destination_host, self.config.destination_token).status_code != 200:
                    self.log.info("Waiting {0} seconds to create {1} for project {2}".format(
                        self.config.importexport_wait, dst_namespace, name))
                    timeout += wait_time
                    sleep(wait_time)
                    if timeout > self.COOL_OFF_MINUTES * 60:
                        self.log.error("Time limit exceeded waiting for project {0} to import to {1}, with response:\n{2}".format(
                            name, dst_namespace, import_response))
                        return None
                import_response = self.attempt_import(
                    filename, name, path, dst_namespace, override_params, members)
            elif not import_response or is_error_message_present(import_response):
                self.log.error("Project {0} failed to import to {1}, due to:\n{2}".format(
                    name, dst_namespace, import_response))
                return None
            import_id = self.get_import_id_from_response(
                import_response, filename, name, path, dst_namespace, override_params, members)
        else:
            self.log.info(
                "DRY-RUN: Outputing project {0} (file: {1}) migration data to dry_run_project_migration.json".format(name, filename))
            migration_dry_run("project", {
                "filename": filename,
                "name": name,
                "namespace": dst_namespace,
                "override_params": override_params,
                "project": project})
        return import_id

    def attempt_import(self, filename, name, path, namespace, override_params, members):
        import_response = None
        if self.config.location == "aws":
            presigned_get_url = self.aws.generate_presigned_url(
                filename, "GET")
            self.log.info(
                "Importing {} from AWS presigned_url (aws mode)".format(filename))
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
                formatted_name = name.lower()
                download = "%s_%s.tar.gz" % (
                    namespace, formatted_name)
                downloaded_filename = self.keys_map.get(
                    download.lower(), None)
                if downloaded_filename is None:
                    self.log.info("Continuing to search for filename")
                    placeholder = len(formatted_name)
                    for i in range(placeholder, 0, -1):
                        split_name = "%s_%s.tar.gz" % (
                            namespace, formatted_name[:(i * (1))])
                        downloaded_filename = self.keys_map.get(
                            split_name.lower(), None)
                        if downloaded_filename is not None:
                            break
                if downloaded_filename is not None:
                    import_response = self.aws.copy_from_s3_and_import(
                        name, namespace, downloaded_filename)
        elif self.config.location == "filesystem":
            resp = None
            self.log.info(
                "Importing project {0} from filesystem to {1}".format(name, namespace))
            try:
                # Handle large files
                with open("%s/downloads/%s" % (self.config.filesystem_path, filename), "rb") as f:
                    m = MultipartEncoder(fields={
                        "file": (filename, f),
                        "path": path,
                        "namespace": namespace,
                        "name": validate_name(name)
                    })
                    headers = {
                        "Private-Token": self.config.destination_token,
                        "Content-Type": m.content_type
                    }
                    message = "Importing project %s with the following payload %s and following members %s" % (
                        name, m, members)
                    resp = self.projects_api.import_project(
                        self.config.destination_host, self.config.destination_token, data=m, headers=headers, message=message)
                    import_response = resp.text
            except AttributeError as ae:
                self.log.error(
                    "Large file upload failed for {0}. Using standard file upload, due to:\n{1}".format(
                        filename, ae))
                with open("%s/downloads/%s" % (self.config.filesystem_path, filename), "rb") as f:
                    data = {
                        "path": path,
                        "namespace": namespace,
                        "name": validate_name(name)
                    }
                    files = {
                        "file": (filename, f)
                    }
                    headers = {
                        "Private-Token": self.config.destination_token
                    }
                    message = "Importing project %s with the following payload %s and following members %s" % (
                        name, data, members)
                    resp = self.projects_api.import_project(
                        self.config.destination_host, self.config.destination_token, data=data, files=files, headers=headers, message=message)
                    import_response = resp.text
        return import_response

    def import_group(self, group, full_path, filename, dry_run=True):
        """
            Imports groups to destination GitLab instance.
        """
        if group is None:
            self.log.error(
                "SKIP: Import, the following group is NONE: {}".format(group))
            return None

        if isinstance(group, str):
            group = json.loads(group)

        name = group["name"]
        path = group["path"]
        members = group["members"]
        if not dry_run:
            import_response = self.attempt_group_import(
                filename, name, path, members)
            try:
                import_response_text = import_response.text
            except AttributeError as e:
                import_response_text = ""
            if import_response and import_response.status_code in [200, 202]:
                self.log.info(
                    "Group {0} (file: {1}) successfully imported".format(full_path, filename))
            else:
                self.log.error("Group {0} (file: {1}) import failed, with status:\n{2}".format(
                    full_path, filename, import_response_text))
        else:
            self.log.info("DRY-RUN: Outputing group {0} (file: {1}) migration data to dry_run_group_migration.json"
                          .format(full_path, filename))
            migration_dry_run("group", {
                "filename": filename,
                "name": name,
                "path": path,
                "full_path": full_path,
                "group": group})

    def attempt_group_import(self, filename, name, path, members):
        resp = None
        self.log.info("Importing group {} from filesystem".format(name))
        # NOTE: Group export does not yet support (AWS/S3) user attributes
        if self.config.location == "aws":
            pass
        elif self.config.location == "filesystem-aws":
            pass
        elif self.config.location == "filesystem":
            with open("%s/downloads/%s" % (self.config.filesystem_path, filename), "rb") as f:
                data = {
                    "path": path,
                    "name": validate_name(name),
                    "parent_id": self.config.parent_id if self.config.parent_id else ""
                }
                files = {
                    "file": (filename, f)
                }
                headers = {
                    "Private-Token": self.config.destination_token
                }
                message = "Importing group %s with payload %s and members %s" % (
                    path, data, members)
                resp = self.groups_api.import_group(
                    self.config.destination_host, self.config.destination_token, data=data, files=files, headers=headers, message=message)
        return resp

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

    def get_import_id_from_response(self, import_response, filename, name, path, dst_namespace, override_params, members):
        timeout = 0
        retry = True
        import_id = None
        wait_time = self.config.importexport_wait
        import_response = json.loads(import_response)
        while True:
            total = 0
            # Wait until rate limit is resolved or project deleted
            while self.RATE_LIMIT_MSG in str(import_response) or any(del_err_msg in str(import_response) for del_err_msg in self.DEL_ERR_MSGS):
                if self.RATE_LIMIT_MSG in str(import_response):
                    self.log.warning("Re-importing project {0} to {1}, waiting {2} minutes due to:\n{3}".format(
                        name, dst_namespace, self.COOL_OFF_MINUTES, import_response))
                    sleep(self.COOL_OFF_MINUTES * 60)
                # Assuming Default deletion adjourned period (Admin -> Settings -> General -> Visibility and access controls) is 0
                elif any(del_err_msg in str(import_response) for del_err_msg in self.DEL_ERR_MSGS) and not is_dot_com(self.config.destination_host):
                    if total > self.config.max_export_wait_time:
                        self.log.error("Time limit exceeded waiting for project {0} to delete from {1}, with response:\n{2}".format(
                            name, dst_namespace, import_response))
                        return None
                    self.log.info(
                        "Waiting {0} seconds for project {1} to delete from {2} before re-importing".format(wait_time, name, dst_namespace))
                    total += wait_time
                    sleep(wait_time)
                import_response = self.attempt_import(
                    filename, name, path, dst_namespace, override_params, members)
                import_response = json.loads(import_response)
                timeout = 0
            import_id = import_response.get("id", None)
            if import_id:
                status = self.projects_api.get_project_import_status(
                    self.config.destination_host, self.config.destination_token, import_id)
                if status.status_code == 200:
                    status_json = status.json()
                    if status_json.get("import_status", None) == "finished":
                        self.log.info(
                            "Project {0} successfully imported to {1}, with import status:\n{2}".format(name, dst_namespace, json_pretty(status_json)))
                        break
                    elif status_json.get("import_status", None) == "failed":
                        self.log.error("Project {0} import to {1} failed, with import status{2}:\n{3}".format(
                            name, dst_namespace, " (re-importing)" if retry else "", json_pretty(status_json)))
                        # Delete and re-import once if the project import status failed, otherwise just delete
                        # Assuming Default deletion adjourned period (Admin -> Settings -> General -> Visibility and access controls) is 0
                        if retry and not is_dot_com(self.config.destination_host):
                            self.log.info("Deleting project {0} from {1} after import status failed (re-importing)".format(
                                name, dst_namespace))
                            self.projects_api.delete_project(
                                self.config.destination_host, self.config.destination_token, import_id)
                            import_response = self.attempt_import(
                                filename, name, path, dst_namespace, override_params, members)
                            import_response = json.loads(import_response)
                            retry = False
                            timeout = 0
                        else:
                            self.log.info("Deleting project {0} from {1} after re-import status failed".format(
                                name, dst_namespace))
                            self.projects_api.delete_project(
                                self.config.destination_host, self.config.destination_token, import_id)
                            return None
                    # For any other import status (started, scheduled, etc.) wait for it to update
                    elif timeout < self.config.max_export_wait_time:
                        self.log.info(
                            "Checking project {0} ({1}) import status in {2} seconds".format(name, dst_namespace, wait_time))
                        timeout += wait_time
                        sleep(wait_time)
                    # In case of timeout delete
                    else:
                        self.log.error("Time limit exceeded waiting for project {0} ({1}) import status (deleting):\n{2}".format(
                            name, dst_namespace, json_pretty(status_json)))
                        self.projects_api.delete_project(
                            self.config.destination_host, self.config.destination_token, import_id)
                        return None
                else:
                    self.log.error(
                        "Project {0} ({1}) import attempt failed, with status:\n{2}".format(name, dst_namespace, status))
                    return None
            else:
                self.log.error("Project {0} ({1}) failed to import, with response:\n{2}".format(
                    name, dst_namespace, import_response))
                return None
        return import_id

    def export_project_thru_filesystem(self, project):
        exported = False
        name = project["name"]
        namespace = project["namespace"]
        pid = project["id"]
        dst_path_with_namespace = get_dst_path_with_namespace(project)
        self.log.info("Searching on destination for project {}".format(
            dst_path_with_namespace))
        dst_pid = self.projects.find_project_by_path(
            self.config.destination_host, self.config.destination_token, dst_path_with_namespace)
        if dst_pid:
            self.log.info("SKIP: Project {0} (ID: {1}) found on destination".format(
                dst_path_with_namespace, dst_pid))
        else:
            self.log.info("Project {} NOT found on destination. Exporting from source...".format(
                dst_path_with_namespace))
            response = self.projects_api.export_project(
                self.config.source_host, self.config.source_token, pid)
            if response is None or response.status_code not in (200, 202):
                self.log.error("Failed to trigger project {0} (ID: {1}) export, with response {2}"
                               .format(pid, name, response))
            else:
                exported = self.wait_for_export_to_finish(pid, name)
                if exported:
                    url = "{0}/api/v4/projects/{1}/export/download".format(
                        self.config.source_host, pid)
                    download_file(
                        url,
                        self.config.filesystem_path,
                        filename=get_export_filename_from_namespace_and_name(
                            namespace, name),
                        headers={"PRIVATE-TOKEN": self.config.source_token})
                else:
                    self.log.error(
                        "Failed to export project {0} (ID: {1})".format(name, pid))
        return exported

    def export_group_thru_filesystem(self, src_gid, full_path, filename):
        exported = False
        full_path_with_parent_namespace = get_full_path_with_parent_namespace(
            full_path)
        self.log.info("Searching on destination for group {}".format(
            full_path_with_parent_namespace))
        dst_gid = self.groups.find_group_by_path(
            self.config.destination_host,
            self.config.destination_token,
            full_path_with_parent_namespace)
        if dst_gid:
            self.log.info("SKIP: Group {0} with source ID {1} and destination ID {2} found on destination".format(
                full_path_with_parent_namespace, src_gid, dst_gid))
        else:
            self.log.info("Group {0} (Source ID: {1}) NOT found on destination.".format(
                full_path_with_parent_namespace, src_gid))
            response = self.groups_api.export_group(
                self.config.source_host, self.config.source_token, src_gid)
            if response is None or response.status_code not in [200, 202]:
                self.log.error("Failed to trigger group {0} (ID: {1}) export, with response '{2}'"
                               .format(full_path, src_gid, response))
            else:
                # NOTE: Export status API endpoint not yet available
                # exported = self.wait_for_export_to_finish(
                #     src_gid, full_path, is_project=False) or True
                exported = self.wait_for_group_download(src_gid)
                url = "{0}/api/v4/groups/{1}/export/download".format(
                    self.config.source_host, src_gid)
                self.log.info("Downloading group {0} (source ID: {1}) as {2}".format(
                    full_path, src_gid, filename))
                download_file(url, self.config.filesystem_path, filename=filename, headers={
                              "PRIVATE-TOKEN": self.config.source_token})
        return exported

    def export_thru_fs_aws(self, pid, name, namespace):
        path_with_namespace = "%s_%s.tar.gz" % (namespace, name)
        if self.keys_map.get(path_with_namespace.lower(), None) is None:
            self.log.info("Unarchiving %s" % name)
            self.projects.projects_api.unarchive_project(
                self.config.source_host, self.config.source_token, pid)
            self.log.info("Exporting %s to %s" %
                          (name, self.config.filesystem_path))
            self.projects_api.export_project(
                self.config.source_host, self.config.source_token, pid)
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
            self.log.info("SKIP: Project {} export found".format(
                path_with_namespace))

        return success

    def export_group_thru_aws(self, gid, full_path, filename):
        """
        Called from migrate to kick-off an export process. Calls export_to_aws.

        :param name: Entity name. This is the name of the group itself
        :param namespace: Namespace where the entity lives. It's direct parent.
        :param full_parent_namespace: Complete path of the parent namespace from source. So, if this group is group3
                                        in the structure `group1/group2/group3`, full_parent_namespace is `group1/group2`
        """
        exported = False

        full_path_with_parent_namespace = get_full_path_with_parent_namespace(
            full_path)
        self.log.info("Searching on destination for group {}".format(
            full_path_with_parent_namespace))
        dst_gid = self.groups.find_group_by_path(
            self.config.destination_host,
            self.config.destination_token,
            full_path_with_parent_namespace)
        if dst_gid:
            self.log.info("SKIP: Group {0} with source ID {1} and destination group ID {2} found on destination".format(
                full_path_with_parent_namespace, gid, dst_gid))
        else:
            # Generating the presigned URL later down the line does the quote_plus work, and the AWS functions to generate
            # expect an *un*quote_plus string (even through S3 itself returns a quote_plus style string)
            # Also, the CLI commands expect no + and no encoding (for is_export_on_aws). So, leave the filename as the full path
            # Do that export thing
            self.log.info("Group {0} (Source ID: {1}) NOT found on destination.".format(
                full_path_with_parent_namespace, gid))
            # Passing full_path_with_parent_namespace with no +, no encoding, not a quoted string
            # NOTE: upload parameter not yet available for export
            response = self.export_to_aws(gid, filename, False)
            if response is not None and response.status_code == 202:
                # TODO: We're going to need to see what the status looks like
                # NOTE: Export status API endpoint not available yet
                export_status = self.wait_for_export_to_finish(
                    gid, full_path, is_project=False)

                # If export status is unknown lookup the file on AWS
                # Could be misleading, since it assumes the file is complete
                exported = export_status or self.aws.is_export_on_aws(filename)
        return exported

    def export_project_thru_aws(self, project):
        """
        Called from migrate to kick-off an export process. This is project specific at this time. Calls export_to_aws.

        :param name: Project JSON
        """
        exported = False
        name = project["name"]
        namespace = project["namespace"]
        pid = project["id"]
        dst_path_with_namespace = get_dst_path_with_namespace(project)
        filename = get_export_filename_from_namespace_and_name(
            namespace, name)
        self.log.info("Searching on destination for project {0}".format(
            dst_path_with_namespace))
        dst_pid = self.projects.find_project_by_path(
            self.config.destination_host, self.config.destination_token, dst_path_with_namespace)
        if not dst_pid:
            self.log.info("Project {0} NOT found on destination. Exporting from source...".format(
                dst_path_with_namespace))
            response = self.export_to_aws(pid, filename, True)
            if response is not None and response.status_code == 202:
                export_status = self.wait_for_export_to_finish(pid, name)
                # If export status is unknown lookup the file on AWS
                # Could be misleading, since it assumes the file is complete
                exported = export_status or self.aws.is_export_on_aws(filename)
            else:
                self.log.error("Failed to export project {0} (ID: {1}), with response {2}".format(
                    name, pid, response))
        else:
            self.log.info("SKIP: Project {0} (ID: {1}) found on destination".format(
                dst_path_with_namespace, dst_pid))
        return exported
