import json
import os
import signal
from re import sub
from urllib.parse import quote, quote_plus
from time import sleep
from os import remove
from glob import glob
from gitlab_ps_utils.misc_utils import get_dry_log, safe_json_response
from gitlab_ps_utils.file_utils import download_file, is_gzip
from gitlab_ps_utils.json_utils import json_pretty

from requests.exceptions import RequestException
from requests_toolbelt.multipart.encoder import MultipartEncoder
from congregate.migration.gitlab.base_gitlab_client import BaseGitLabClient
from congregate.aws import AwsClient
from congregate.migration.gitlab.projects import ProjectsClient
from congregate.migration.gitlab.groups import GroupsClient
from congregate.migration.gitlab.api.users import UsersApi
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.api.namespaces import NamespacesApi
from congregate.helpers.migrate_utils import get_project_dest_namespace, is_user_project, get_user_project_namespace, \
    get_export_filename_from_namespace_and_name, get_full_path_with_parent_namespace, \
    is_loc_supported, check_is_project_or_group_for_logging, migration_dry_run, check_download_directory, default_response, \
    get_stage_wave_paths
from congregate.helpers.airgap_utils import extract_archive


class ImportExportClient(BaseGitLabClient):
    SAML_MSG = "Validation failed: User is not linked to a SAML account"

    # Import rate limit cool-off
    COOL_OFF_MINUTES = 1.2

    def __init__(self, src_host=None, src_token=None, dest_host=None, dest_token=None):
        super().__init__(src_host=src_host, src_token=src_token,
                         dest_host=dest_host, dest_token=dest_token)
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
            return self.projects_api.get_project_export_status(
                src_id, self.src_host, self.src_token)
        return self.get_group_export_status(src_id)

    def get_group_export_status(self, src_id):
        return self.projects_api.api.generate_get_request(
            self.src_host, self.src_token, "groups/%d/export" % src_id)

    def wait_for_export_to_finish(
            self, src_id, name, is_project=True, retry=True):
        exported = False
        total_time = 0
        wait_time = self.config.export_import_status_check_time
        timeout = self.config.export_import_timeout
        export_type = check_is_project_or_group_for_logging(is_project)
        response = self.trigger_export_and_get_response(src_id, is_project)
        while True:
            # Wait until rate limit is resolved
            while response.status_code == 429:
                self.log.info(
                    f"Re-exporting {export_type.lower()} {name} (ID: {src_id}), waiting {self.COOL_OFF_MINUTES} minutes due to:\n{response.text}")
                sleep(self.COOL_OFF_MINUTES * 60)
                response = self.trigger_export_and_get_response(
                    src_id, is_project)
            if response.status_code in [200, 201, 202]:
                status = self.get_export_status(src_id, is_project)
                if status.status_code in [200, 201, 202]:
                    status_json = safe_json_response(status)
                    state = status_json.get("export_status")
                    if state in ["finished", "regeneration_in_progress"]:
                        self.log.info(
                            f"{export_type} {name} has finished exporting, with response:\n{json_pretty(status_json)}")
                        exported = True
                        break
                    if state == "failed":
                        self.log.error(
                            f"{export_type} {name} export failed, with response:\n{json_pretty(status_json)}")
                        break
                    # We don't want to wait for queued exports
                    if state == "none" and total_time > timeout/4:
                        self.log.error(
                            f"SKIP: {export_type} {name} export with status '{state}' and response:\n{json_pretty(status_json)}")
                        break
                    if total_time < timeout:
                        self.log.info(
                            f"{export_type} {name} export status '{state}' after {total_time}/{timeout} seconds")
                        total_time += wait_time
                        sleep(wait_time)
                    else:
                        self.log.error(
                            f"{export_type} {name} time limit exceeded with export status:\n{json_pretty(status_json)}")
                        break
            elif retry:
                self.log.error(
                    f"{export_type} {name} export trigger failed{' (re-exporting)' if retry else ''}, with response:\n{response.text}")
                response = self.trigger_export_and_get_response(
                    src_id, is_project)
                retry = False
                total_time = 0
            else:
                self.log.error(
                    f"SKIP: Failed to trigger source {export_type.lower()} {name} export, due to:\n{response.text}")
                break
        return exported

    def wait_for_group_download(self, gid, retry=True):
        exported = False
        total_time = 0
        wait_time = self.config.export_import_status_check_time
        timeout = self.config.export_import_timeout/2
        response = self.trigger_export_and_get_response(gid, is_project=False)
        while True:
            # Wait until rate limit is resolved
            while response.status_code == 429:
                self.log.info(
                    f"Re-exporting group {gid}, waiting {self.COOL_OFF_MINUTES} minutes due to:\n{response.text}")
                sleep(self.COOL_OFF_MINUTES * 60)
                response = self.trigger_export_and_get_response(
                    gid, is_project=False)
            if response.status_code == 202:
                status = self.groups_api.get_group_download_status(
                    self.src_host, self.src_token, gid)
                # Assuming Max Group Export Download requests per minute per
                # user = 1
                if status.status_code == 200:
                    self.log.info(
                        f"Waiting {self.COOL_OFF_MINUTES} minutes to download group {gid}")
                    sleep(self.COOL_OFF_MINUTES * 60)
                    exported = True
                    break
                if total_time < timeout:
                    self.log.info(
                        f"Waited {total_time}/{timeout} seconds for group {gid} to export")
                    total_time += wait_time
                    sleep(wait_time)
                else:
                    self.log.error(
                        f"Time limit exceeded for exporting group {gid}, with status:\n{status}")
                    break
            elif retry:
                self.log.error(
                    f"Group {gid} export failed (re-exporting), with response:\n{response.text}")
                response = self.trigger_export_and_get_response(
                    gid, is_project=False)
                retry = False
                total_time = 0
            else:
                self.log.error(
                    f"SKIP: Failed to trigger source group {gid} export, due to:\n{response.text}")
                break
        return exported

    def wait_for_group_import(self, path):
        group = {}
        timer = 0
        wait_time = self.config.export_import_status_check_time
        # Lightweight and requires half the timeout at most
        timeout = self.config.export_import_timeout/2
        while True:
            group = self.groups.find_group_by_path(
                self.config.destination_host, self.config.destination_token, path)
            if group:
                self.log.info(
                    f"Group {path} imported successfully with ID {group.get('id')}")
                break
            self.log.info(
                f"Waited {timer}/{timeout} seconds for group {path} to import")
            sleep(wait_time)
            timer += wait_time
            if timer > timeout:
                self.log.error(
                    f"Time limit exceeded for importing group {path}")
                break
        return group

    def trigger_export_and_get_response(self, source_id, is_project, data=None, headers=None):
        """
        Gets the export response for both project and group exports
        """
        response = None

        if is_project:
            response = self.projects_api.export_project(
                self.src_host, self.src_token, source_id, data=data, headers=headers)
        else:
            response = self.groups_api.export_group(
                self.src_host, self.src_token, source_id, data=data, headers=headers)
        return response

    def export_to_aws(self, source_id, filename, is_project=True):
        presigned_put_url = self.aws.generate_presigned_url(filename, "PUT")
        upload = [
            "upload[http_method]=PUT",
            "upload[url]=%s" % quote(presigned_put_url)
        ]
        headers = {
            'Private-Token': self.src_token,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = "&".join(upload)
        try:
            response = self.trigger_export_and_get_response(
                source_id, is_project, data=data, headers=headers)
            return response
        except RequestException as e:
            self.log.error("Failed to trigger {0} (ID: {1}) export as {2} with response {3}".format(
                check_is_project_or_group_for_logging(is_project).lower(), source_id, filename, response))
            return None

    def import_project(self, project, dry_run=True, group_path=None):
        """
            Imports project to destination GitLab instance.
            Formats users, groups, migration info (aws, filesystem) during import process.
        """
        if isinstance(project, str):
            project = json.loads(project)

        name = project["name"]
        path = project["path"]
        namespace = project["namespace"]
        members = project.get("members", [])
        override_params = self.get_override_params(project)
        filename = get_export_filename_from_namespace_and_name(namespace, name=name, airgap=self.config.airgap)
        dry = get_dry_log(dry_run)
        import_id = None

        if is_user_project(project):
            dest_namespace = get_user_project_namespace(project)
            self.log.info(
                f"{dry}'{path}' is a USER project. Importing to USER namespace '{dest_namespace}'")
        else:
            dest_namespace = get_project_dest_namespace(
                project, group_path=group_path)
            self.log.info(
                f"{dry}'{path}' is a GROUP project. Importing to GROUP namespace '{dest_namespace}'")

        if not dry_run:
            import_response = self.attempt_import(
                filename, name, path, dest_namespace, override_params, members)
            # Use until group import status endpoint is available
            if import_response.status_code in [404, 403]:
                total_time = 0
                wait_time = self.config.export_import_status_check_time
                timeout = self.COOL_OFF_MINUTES * 60
                while (ns := self.namespaces_api.get_namespace_by_full_path(
                        dest_namespace, self.dest_host, self.dest_token)).status_code != 200:
                    self.log.info(
                        f"Waited {total_time}/{timeout} seconds to create '{dest_namespace}' for project '{name}'")
                    total_time += wait_time
                    sleep(wait_time)
                    if total_time > timeout:
                        self.log.error(
                            f"Time limit exceeded waiting for project '{name}' to import to '{dest_namespace}', with response:\n{import_response}")
                        return None
                ns_id = ns.json().get('id')
                import_response = self.attempt_import(
                    filename, name, path, ns_id, override_params, members)
            elif import_response.status_code == 422:
                self.log.error(
                    f"Project '{name}' failed to import to '{dest_namespace}', due to:\n{import_response.text}")
                return None
            elif import_response.status_code == 400:
                self.log.error(
                    f"Project '{name}' failed to import to '{dest_namespace}', due to:\n{import_response.text}\n\t"
                    "Double check your path. If your path seems correct, make sure you can manually create a project in the GL instance UI under the path")
                return None
            import_id = self.get_import_id_from_response(
                import_response, filename, name, path, dest_namespace, override_params, members)
        else:
            self.log.info(
                f"{dry}Outputing project '{name}' (file: {filename}) migration data to dry_run_project_migration.json")
            migration_dry_run("project", {
                "filename": filename,
                "name": name,
                "namespace": dest_namespace,
                "override_params": override_params,
                "project": project})
        return import_id

    def attempt_import(self, filename, name, path,
                       namespace, override_params, members):
        resp = default_response()
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
            # Check if the download directory exists before attempting to access it
            download_dir = f"{self.config.filesystem_path}/downloads"
            if not check_download_directory(download_dir):
                self.log.error(f"Error: The download directory '{download_dir}' does not exist. "
                               "Please create the directory and try again.")
                os.killpg(os.getpgid(os.getpid()), signal.SIGKILL)
            upload_path = f"{download_dir}/{filename}"
            self.log.info(f"Importing project '{name}' from filesystem ({upload_path}) to '{namespace}")
            try:
                if self.config.airgap:
                    # Extract project archive and load data into mongo
                    _, filename = extract_archive(upload_path)

                # Handle large files
                with open(f"{download_dir}/{filename}", "rb") as f:
                    m = MultipartEncoder(fields={
                        "file": (filename, f),
                        "path": path,
                        "namespace": str(namespace),
                        "name": name
                    })
                    headers = {
                        "Private-Token": self.dest_token,
                        "Content-Type": m.content_type
                    }
                    message = f"Importing project '{name}' with the following payload '{m}' and members '{members}'"
                    if import_resp := self.projects_api.import_project(
                        self.dest_host, self.dest_token, data=m, headers=headers, message=message):
                        resp = import_resp
            except AttributeError as ae:
                self.log.error(f"Large file upload failed for '{filename}'. Using standard file upload:\n{ae}")
                with open(f"{download_dir}/{filename}", "rb") as f:
                    data = {
                        "path": path,
                        "namespace": namespace,
                        "name": name
                    }
                    files = {
                        "file": (filename, f)
                    }
                    headers = {
                        "Private-Token": self.config.destination_token
                    }
                    message = f"Importing project '{name}' with the following payload '{data}' and members '{members}'" % (
                        name, data, members)
                    if import_resp := self.projects_api.import_project(
                        self.config.destination_host, self.config.destination_token, data=data, files=files, headers=headers, message=message):
                        resp = import_resp
        return resp if resp else default_response()

    def import_group(self, group, full_path, filename,
                     dry_run=True, subgroups_only=False):
        """
            Imports groups to destination GitLab instance.
        """
        if group is None:
            self.log.error(
                f"SKIP: Import, the following group is NONE: {group}")
            return None

        if isinstance(group, str):
            group = json.loads(group)

        name = group["name"]
        path = group["path"]
        members = group["members"]
        parent_id = None
        if subgroups_only:
            parent_path = full_path.rsplit("/", 1)[0]
            found = self.groups.find_group_id_by_path(
                self.config.destination_host, self.config.destination_token, parent_path)
            if found:
                parent_id = found
            else:
                self.log.warning(
                    f"Parent group '{parent_path}' NOT found on destination")
                return False
        if not dry_run:
            import_response = self.attempt_group_import(
                filename, name, path, members, parent_id=parent_id)
            wait_time = self.config.export_import_status_check_time
            try:
                text = import_response.text
            except AttributeError:
                text = ""
            while import_response.status_code in [500, 429]:
                if import_response.status_code == 429:
                    self.log.info(
                        f"Re-importing group '{full_path}', waiting {self.COOL_OFF_MINUTES} minutes due to:\n{import_response.text}")
                    sleep(self.COOL_OFF_MINUTES * 60)
                elif import_response.status_code == 500:
                    self.log.warning(
                        f"Re-importing group '{full_path}' in {wait_time} seconds due to:\n{import_response.text}")
                    sleep(wait_time)
                import_response = self.attempt_group_import(
                    filename, name, path, members, parent_id=parent_id)
            if import_response and import_response.status_code == 202:
                self.log.info(
                    f"Group '{full_path}' (file: {filename}) successfully imported")
                return True
            self.log.error(
                f"Group '{full_path}' (file: {filename}) import failed, with status:\n{text}")
            return False
        self.log.info(
            f"DRY-RUN: Outputting group '{full_path}' (file: {filename}) migration data to dry_run_group_migration.json")
        migration_dry_run("group", {
            "filename": filename,
            "name": name,
            "path": path,
            "full_path": full_path,
            "group": group})
        return False

    def attempt_group_import(self, filename, name,
                             path, members, parent_id=None):
        resp = None
        self.log.info(f"Importing group '{path}' from filesystem")
        if self.config.location in ["aws", "filesystem-aws"]:
            self.log.warning(
                "NOTICE: Group export does not yet support (AWS/S3) user attributes")
        elif self.config.location == "filesystem":
            # Check if the download directory exists before attempting to access it
            download_dir = f"{self.config.filesystem_path}/downloads"
            if not check_download_directory(download_dir):
                self.log.error(f"Error: The download directory '{download_dir}' does not exist. "
                               "Please create the directory and try again.")
                os.killpg(os.getpgid(os.getpid()), signal.SIGKILL)
            token = self.config.destination_token
            with open(f"{self.config.filesystem_path}/downloads/{filename}", "rb") as f:
                data = {
                    "path": path,
                    "name": name,
                    "parent_id": parent_id if parent_id else self.config.dstn_parent_id if self.config.dstn_parent_id else None
                }
                files = {
                    "file": (filename, f)
                }
                headers = {
                    "Private-Token": token
                }
                message = f"Importing group '{path}' with payload {data} and members {members}"
                resp = self.groups_api.import_group(
                    self.config.destination_host, token, data=data, files=files, headers=headers, message=message)
        return resp

    def get_override_params(self, project):
        return {
            "description": project.get("description", ''),
            "shared_runners_enabled": self.config.shared_runners_enabled,
            "archived": project.get("archived", False)
        }

    def get_full_path(self, url):
        strip = sub(r"http(s|)://.+(\.net|\.com|\.org)/", "", url)
        another_strip = strip.split("/")
        for ind, val in enumerate(another_strip):
            if ".git" in val:
                another_strip.pop(ind)
        return "/".join(another_strip)

    def get_import_id_from_response(
            self, import_response, filename, name, path, dst_namespace, override_params, members):
        total_time = 0
        retry = True
        import_id = None
        wait_time = self.config.export_import_status_check_time
        timeout = self.config.export_import_timeout
        host = self.dest_host
        token = self.dest_token
        while True:
            # Wait until rate limit is resolved or project deleted
            while import_response.status_code in [500, 429, 409, 400]:
                text = import_response.text
                if import_response.status_code == 429:
                    self.log.info(
                        f"Re-importing project '{name}' to '{dst_namespace}', waiting {self.COOL_OFF_MINUTES} minutes due to:\n{text}")
                    sleep(self.COOL_OFF_MINUTES * 60)
                # Assuming Default deletion adjourned period (Admin -> Settings
                # -> General -> Visibility and access controls) is 0
                elif import_response.status_code in [409, 400]:
                    if total_time > timeout:
                        self.log.error(
                            f"Time limit exceeded waiting for project '{name}' to delete from '{dst_namespace}', with response:\n{text}")
                        return None
                    self.log.info(
                        f"Waited {total_time}/{timeout} seconds for project '{name}' to delete from '{dst_namespace}' before re-importing:\n{text}")
                    total_time += wait_time
                    sleep(wait_time)
                elif import_response.status_code == 500:
                    if retry:
                        self.log.info(
                            f"Attempting to delete project '{name}' from '{dst_namespace}', before re-importing, due to:\n{text}")
                        # Using project path instead of ID
                        self.projects_api.delete_project(
                            host, token, quote_plus(dst_namespace + "/" + path))
                        sleep(wait_time)
                        retry = False
                    else:
                        self.log.error(
                            f"Skipping project '{name}' due to multiple 500 errors")
                        break
                import_response = self.attempt_import(
                    filename, name, path, dst_namespace, override_params, members)
            safe_resp = safe_json_response(import_response)
            import_id = safe_resp.get("id") if safe_resp else None
            if import_id:
                status = self.projects_api.get_project_import_status(
                    host, token, import_id)
                if status.status_code in [200, 201]:
                    status_json = safe_json_response(status)
                    state = status_json.get(
                        "import_status") if status_json else None
                    if state == "finished":
                        self.log.info(
                            f"Project '{name}' successfully imported to '{dst_namespace}', with import status:\n{json_pretty(status_json)}")
                        with open(f"{self.app_path}/data/logs/import_failed_relations.json", "a") as f:
                            json.dump({status_json.get("path_with_namespace"): status_json.get(
                                "failed_relations")}, f, indent=4)
                        break
                    if state == "failed":
                        if self.SAML_MSG in status_json.get("import_error"):
                            self.log.error(
                                f"Project {name} import to {dst_namespace} failed:\n{json_pretty(status_json)}")
                            return None
                        self.log.error(
                            f"Project {name} import to {dst_namespace} failed, with import status{' (re-importing)' if retry else ''}:\n{json_pretty(status_json)}")
                        # Delete and re-import once if the project import status failed, otherwise just delete
                        # Assuming Default deletion adjourned period (Admin ->
                        # Settings -> General -> Visibility and access
                        # controls) is 0
                        if retry:
                            self.log.info(
                                f"Deleting project {name} from {dst_namespace} after import status failed (re-importing)")
                            self.projects_api.delete_project(
                                host, token, import_id)
                            import_response = self.attempt_import(
                                filename, name, path, dst_namespace, override_params, members)
                            retry = False
                            total_time = 0
                        else:
                            return None
                    # For any other import status (started, scheduled, etc.)
                    # wait for it to update
                    elif total_time < timeout:
                        self.log.info(
                            f"Project {name} ({dst_namespace}) import status ({state}) after {total_time}/{timeout} seconds")
                        total_time += wait_time
                        sleep(wait_time)
                    else:
                        self.log.error(
                            f"Time limit exceeded waiting for project {name} ({dst_namespace}) import status:\n{json_pretty(status_json)}")
                        return None
                else:
                    self.log.error(
                        f"Project {name} ({dst_namespace}) import attempt failed, with status:\n{status}")
                    return None
            else:
                self.log.error(
                    f"Project '{name}' ({dst_namespace}) failed to import:\n{import_response} - {import_response.text}")
                return None
        return import_id

    def export_project(self, project, dry_run=True):
        loc = self.config.location
        is_loc_supported(loc)
        exported = False
        name = project["name"]
        namespace = project["namespace"]
        pid = project["id"]
        if not self.config.airgap:
            dst_path_with_namespace, _ = get_stage_wave_paths(project)
            dst_pid = self.projects.find_project_by_path(
                self.config.destination_host, self.config.destination_token, dst_path_with_namespace)
            if dst_pid:
                self.log.warning(
                    f"SKIP: Project '{dst_path_with_namespace}' (ID: {dst_pid}) found on destination")
                return False
        if not dry_run:
            filename = get_export_filename_from_namespace_and_name(
                namespace, name=name)
            if loc == "filesystem":
                exported = self.wait_for_export_to_finish(pid, name)
                if exported:
                    self.handle_gzip_download(name, pid, filename)
            # TODO: Refactor and sync with other scenarios (#119)
            elif loc == "filesystem-aws":
                self.log.warning(
                    "NOTICE: Filesystem-AWS exports are not currently supported")
                # exported = self.export_thru_fs_aws(pid, name, namespace) if not dry_run else True
            elif loc == "aws":
                response = self.export_to_aws(pid, filename)
                if response is None or response.status_code != 202:
                    self.log.error(
                        f"Failed to trigger project {name} (ID: {pid}) export, with response {response}")
                else:
                    export_status = self.wait_for_export_to_finish(pid, name)
                    # If export status is unknown lookup the file on AWS
                    # Could be misleading, since it assumes the file is
                    # complete
                    exported = export_status or self.aws.is_export_on_aws(
                        filename)
        else:
            return True
        return exported

    def handle_gzip_download(self, name, pid, filename):
        '''
            Attempt to download the export, if it's not a valid export, try again.
        '''
        url = f"{self.src_host}/api/v4/projects/{pid}/export/download"
        self.log.info(
            f"Downloading project '{name}' (ID: {pid}) as {filename}")
        total_time = 0
        timeout = self.config.export_import_timeout
        wait_time = self.COOL_OFF_MINUTES * 60
        while total_time < timeout:
            new_file = download_file(
                url,
                self.config.filesystem_path,
                filename,
                headers={"PRIVATE-TOKEN": self.src_token},
                verify=self.config.ssl_verify,
                wait=67)
            # If None i.e. exception, retry
            if not new_file:
                self.log.info(
                    f"Waiting {self.COOL_OFF_MINUTES} minutes to download project '{name}' (ID: {pid}) as {filename}")
                total_time += wait_time
                sleep(wait_time)
                continue
            break
        if not is_gzip(f"{self.config.filesystem_path}/downloads/{new_file}"):
            raise ValueError("Downloaded file is NOT a Gzip file.")
        self.log.info(
            f"Project '{name}' export file successfully downloaded. Verified {filename} is a gzip file.")

    def export_thru_fs_aws(self, pid, name, namespace):
        path_with_namespace = "%s_%s.tar.gz" % (namespace, name)
        if self.keys_map.get(path_with_namespace.lower(), None) is None:
            self.log.info("Unarchiving %s" % name)
            self.projects.projects_api.unarchive_project(
                self.src_host, self.src_token, pid)
            self.log.info("Exporting %s to %s" %
                          (name, self.config.filesystem_path))
            self.projects_api.export_project(
                self.src_host, self.src_token, pid)
            url = "%s/api/v4/projects/%d/export/download" % (
                self.src_host, pid)

            exported = self.wait_for_export_to_finish(pid, name)

            if exported:
                self.log.info("Downloading export")
                try:
                    filename = download_file(url, self.config.filesystem_path, path_with_namespace, headers={
                        "PRIVATE-TOKEN": self.src_token}, verify=self.config.ssl_verify, wait=67)
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

    def export_group(self, src_gid, full_path, filename, dry_run=True):
        loc = self.config.location
        is_loc_supported(loc)
        exported = False
        dst_gid = None
        # Destination group lookup might not be possible if source is air-gapped
        if not self.config.airgap:
            full_path_with_parent_namespace = get_full_path_with_parent_namespace(
                full_path)
            self.log.info(f"Searching on destination for group '{full_path_with_parent_namespace}'")
            dst_gid = self.groups.find_group_id_by_path(
                self.config.destination_host,
                self.config.destination_token,
                full_path_with_parent_namespace)
        if dst_gid:
            self.log.warning(f"SKIP: Group '{full_path_with_parent_namespace}' with source ID {src_gid} and destination ID {dst_gid} found on destination")
        elif not dry_run:
            if loc == "filesystem":
                # NOTE: Export status API endpoint not yet available
                # exported = self.wait_for_export_to_finish(
                #     src_gid, full_path, is_project=False) or True
                exported = self.wait_for_group_download(src_gid)
                if exported:
                    url = f"{self.src_host}/api/v4/groups/{src_gid}/export/download"
                    self.log.info(f"Downloading group '{full_path}' (ID: {src_gid}) as '{filename}'")
                    download_file(url, self.config.filesystem_path, filename=filename, headers={
                        "PRIVATE-TOKEN": self.src_token}, verify=self.config.ssl_verify, wait=67)
            # TODO: Refactor and sync with other scenarios (#119)
            elif loc == "filesystem-aws":
                self.log.error(
                    "NOTICE: Filesystem-AWS exports are not currently supported")
            # NOTE: Group export does not yet support AWS (S3) user attributes
            elif loc == "aws":
                self.log.error(
                    "NOTICE: AWS group exports are not currently supported")
                # response = self.export_to_aws(src_gid, filename, is_project=False)
                # if response is None or response.status_code not in [200, 202]:
                #     self.log.error("Failed to trigger group {0} (ID: {1}) export, with response '{2}'"
                #                    .format(full_path, src_gid, response))
                # else:
                #     # NOTE: Export status API endpoint not yet available
                #     export_status = self.wait_for_export_to_finish(
                #         src_gid, full_path, is_project=False)

                #     # If export status is unknown lookup the file on AWS
                #     # Could be misleading, since it assumes the file is complete
                #     exported = export_status or self.aws.is_export_on_aws(
                #         filename)
        else:
            return True
        return exported

    def wait_for_bulk_group_import(self, resp, iid):
        imported = False
        total_time = 0
        wait_time = self.config.export_import_status_check_time
        timeout = self.config.export_import_timeout
        while True:
            details = safe_json_response(resp)
            state = details.get("status") if details else None
            log_string = f"Bulk group import {state}, with status response:\n{json_pretty(details)}"
            if state == "finished":
                self.log.info(log_string)
                imported = True
                break
            if not state or state == "failed":
                self.log.error(log_string)
                break
            if total_time < timeout:
                self.log.info(
                    f"Bulk group import status after {total_time}/{timeout} seconds: {state}")
                total_time += wait_time
                sleep(wait_time)
                resp = self.groups_api.get_bulk_group_import_status(
                    self.config.destination_host, self.config.destination_token, iid)
            else:
                self.log.error(f"Time limit exceeded. {log_string}")
                break
        return imported
