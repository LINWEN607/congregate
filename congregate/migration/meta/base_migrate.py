"""
    Congregate - GitLab instance migration utility

    Copyright (c) 2023 - GitLab
"""

import os
import sys
from time import time
from traceback import print_exc
from requests import Response
from requests.exceptions import RequestException
from importlib import import_module

from gitlab_ps_utils import json_utils, misc_utils, string_utils

import congregate.helpers.migrate_utils as mig_utils
from congregate.migration.meta.constants import EXT_CI_SOURCE_CLASSES
from congregate.helpers.utils import rotate_logs
from congregate.helpers.reporting import Reporting
from congregate.cli.stage_projects import ProjectStageCLI
from congregate.helpers.base_class import BaseClass
from congregate.migration.gitlab.users import UsersClient
from congregate.migration.gitlab.api.users import UsersApi
from congregate.migration.gitlab.keys import KeysClient
from congregate.migration.gitlab.projects import ProjectsClient, ProjectsApi
from congregate.migration.gitlab.groups import GroupsClient, GroupsApi
from congregate.migration.meta.base_ext_ci import BaseExternalCiClient
from congregate.migration.bitbucket.keys import KeysClient as bbKeysClient


class MigrateClient(BaseClass):
    def __init__(
        self,
        dry_run=True,
        processes=None,
        only_post_migration_info=False,
        start=time(),
        skip_users=False,
        remove_members=False,
        hard_delete=False,
        stream_groups=False,
        skip_groups=False,
        skip_projects=False,
        skip_group_export=False,
        skip_group_import=False,
        skip_project_export=False,
        skip_project_import=False,
        subgroups_only=False,
        scm_source=None,
        group_structure=False,
        retain_contributors=False
    ):
        self.users = UsersClient()
        self.users_api = UsersApi()
        self.groups = GroupsClient()
        self.groups_api = GroupsApi()
        self.projects = ProjectsClient()
        self.projects_api = ProjectsApi()
        self.keys = KeysClient()
        self.bbkeys = bbKeysClient()
        super().__init__()
        self.dry_run = dry_run
        self.processes = processes
        self.only_post_migration_info = only_post_migration_info
        self.start = start
        self.skip_users = skip_users
        self.stream_groups = stream_groups
        self.remove_members = remove_members
        self.hard_delete = hard_delete
        self.skip_groups = skip_groups
        self.skip_projects = skip_projects
        self.skip_group_export = skip_group_export
        self.skip_group_import = skip_group_import
        self.skip_project_export = skip_project_export
        self.skip_project_import = skip_project_import
        self.subgroups_only = subgroups_only
        self.scm_source = scm_source
        self.group_structure = group_structure
        self.retain_contributors = retain_contributors

    # keep for overriden function but reuse functionality from the various migrate_from_* functions
    def migrate(self):
        raise NotImplementedError

    def check_reporting_requirements(self):
        '''
        Return true if congregate.conf is correct, log an error if not.

        '''
        if self.config.reporting:
            if all([
                self.config.reporting,
                self.config.reporting.get("post_migration_issues"),
                self.config.reporting.get("pmi_project_id")
            ]):
                self.log.info(
                    "Successfully got reporting config from congregate.conf. Proceeding to make our issues.")
                return True
            self.log.error(
                "Couldn't find a required REPORTING config in [DESTINATION] section of congregate.conf.\n"
                "Issues will not be created."
            )

    def create_issue_reporting(self, staged_projects, import_results):
        '''
        Use the Reporting class to create/update whatever issues are in the congregate.conf for a given staged_projects
        and import_results.

        '''

        if self.check_reporting_requirements():
            if report := Reporting(
                reporting_project_id=self.config.reporting['pmi_project_id'],
                dry_run=self.dry_run
            ):
                report.handle_creating_issues(staged_projects, import_results)
            else:
                self.log.warning(
                    "REPORTING: Failed to instantiate the reporting module")

    def are_results(self, results, var, stage):
        if not results:
            self.log.warning(
                f"Results from {var} {stage} returned as empty. Aborting.")
            mig_utils.add_post_migration_stats(self.start, log=self.log)
            sys.exit(os.EX_OK)

    def migrate_user_info(self):
        staged_users = mig_utils.get_staged_users()
        if staged_users:
            if not self.skip_users:
                dry_log = misc_utils.get_dry_log(self.dry_run)
                self.log.info(f"{dry_log}Migrating user info")
                staged = self.users.handle_users_not_found(
                    "staged_users",
                    self.users.search_for_staged_users()[0],
                    keep=not self.only_post_migration_info
                )
                new_users = list(nu for nu in self.multi.start_multi_process(
                    self.handle_user_creation, staged, self.processes))
                self.are_results(new_users, "user", "creation")
                formatted_users = {}
                for nu in new_users:
                    formatted_users[nu["email"]] = nu
                new_users.append(mig_utils.get_results(new_users))
                self.log.info(
                    f"### {dry_log}User creation results ###\n{json_utils.json_pretty(new_users)}")
                mig_utils.write_results_to_file(
                    formatted_users, result_type="user", log=self.log)
                if self.dry_run and not self.only_post_migration_info:
                    self.log.info(
                        f"{dry_log}Outputting various USER migration data to 'dry_run_user_migration.json'")
                    mig_utils.migration_dry_run("user", list(self.multi.start_multi_process(
                        self.users.generate_user_data, staged_users, self.processes)))
            else:
                self.log.info(
                    "SKIP: Assuming staged users are already migrated")
        else:
            self.log.warning("SKIP: No users staged for migration")

    def handle_user_creation(self, user):
        """
            This is called when importing staged_users.json.
            Inactive users will be skipped if we do NOT 'keep_inactive_users'.

            :param user: Each iterable called is a user from the staged_users.json file
            :return:
        """
        response = None
        state = user.get("state").lower()
        email = user.get("email")
        name = user.get("name")
        username = user.get("username")
        new_user = {
            "email": email,
            "id": None
        }
        old_user = {
            "email": email,
            "id": user.get("id")
        }
        try:
            if not self.only_post_migration_info:
                if (state == "active" or (state in self.INACTIVE and self.config.keep_inactive_users)) and all(
                        v for v in [name, username, email]):
                    user_data = self.users.generate_user_data(user)
                    self.log.info(
                        f"{misc_utils.get_dry_log(self.dry_run)}Attempting to create user {email}")
                    response = self.users_api.create_user(
                        self.config.destination_host,
                        self.config.destination_token,
                        user_data
                    ) if not self.dry_run else None
                else:
                    self.log.info(
                        f"SKIP: Not migrating {state} user:\n{json_utils.json_pretty(user)}")
                if response is not None:
                    # NOTE: Persist 'inactive' user state regardless of domain
                    # and creation status.
                    if user_data.get("state").lower() in self.INACTIVE:
                        self.users.block_user(user_data)
                    new_user = self.users.handle_user_creation_status(
                        response, user_data)
            if not self.dry_run and self.config.source_type == "gitlab":
                self.gl_user_creation(new_user, old_user, email, user)
            if not self.dry_run and self.config.source_type == "bitbucket server":
                self.bb_user_creation(new_user, username, email, user)
        except RequestException as e:
            self.log.error(
                f"Failed to create user {user_data}, with error:\n{e}")
        except Exception as e:
            self.log.error(
                f"Could not get response text/JSON for {user}. Error was {e}")
            self.log.error(print_exc(e))
        return new_user

    def gl_user_creation(self, new_user, old_user, email, user):
        if new_user:
            found_user = new_user if new_user.get(
                "id") is not None else mig_utils.find_user_by_email_comparison_without_id(email)
            new_user["id"] = found_user.get(
                "id") if found_user else None
            if found_user:
                if not self.config.skip_keys_migration:
                    # Migrate SSH keys
                    self.keys.migrate_user_ssh_keys(old_user, new_user)
                    # Migrate GPG keys
                    self.keys.migrate_user_gpg_keys(old_user, new_user)
                else:
                    self.log.warning(f"SKIP: Not migrating SSH & GPG keys for user: {email}")
        else:
            user_data = self.users.generate_user_data(user)
            self.log.warning(
                f"Could not create user. User may exist with a different primary email. Check previous logs warnings. Userdata follows:\n{user_data}")
            # Return the "original" new_user setting
            return {
                "email": email,
                "id": None
            }

    def bb_user_creation(self, new_user, old_user, email, user):
        if new_user:
            found_user = new_user if new_user.get(
                "id") is not None else mig_utils.find_user_by_email_comparison_without_id(email)
            new_user["id"] = found_user.get(
                "id") if found_user else None
            if found_user:
                # Migrate SSH keys
                if not self.config.skip_keys_migration:
                    self.bbkeys.migrate_bb_user_ssh_keys(old_user, new_user)
                else:
                    self.log.warning(f"SKIP: Not migrating SSH keys for user: {email}")
        else:
            user_data = self.users.generate_user_data(user)
            self.log.warning(
                f"Could not create user. User may exist with a different primary email. Check previous logs warnings. Userdata follows:\n{user_data}")
            # Return the "original" new_user setting
            return {
                "email": email,
                "id": None
            }

    def disable_shared_ci(self, path, pid):
        # Disable Auto DevOps
        self.log.info(
            f"Disabling Auto DevOps on imported project {path} (ID: {pid})")
        data = {"auto_devops_enabled": False}
        # Disable shared runners
        if not self.config.shared_runners_enabled:
            data["shared_runners_enabled"] = self.config.shared_runners_enabled
        self.projects_api.edit_project(
            self.config.destination_host, self.config.destination_token, pid, data)

    def rollback(self):
        rotate_logs()
        dry_log = misc_utils.get_dry_log(self.dry_run)

        # Remove groups and projects OR only empty groups
        if not self.skip_groups:
            self.log.info("{0}Removing staged groups{1} on destination".format(
                dry_log, "" if self.skip_projects else " and projects"))
            self.groups.delete_groups(
                dry_run=self.dry_run, skip_projects=self.skip_projects)

        # Remove only projects
        if not self.skip_projects:
            self.log.info(
                "{}Removing staged projects on destination".format(dry_log))
            self.projects.delete_projects(dry_run=self.dry_run)

        if not self.skip_users:
            self.log.info("{0}Removing staged users on destination (hard_delete={1})".format(
                dry_log,
                self.hard_delete))
            self.users.delete_users(
                dry_run=self.dry_run, hard_delete=self.hard_delete)

        mig_utils.add_post_migration_stats(self.start, log=self.log)

    def get_total_migrated_count(self):
        # group_projects = api.get_count(
        # self.config.destination_host, self.config.destination_token,
        # "groups/%d/projects" % self.config.dstn_parent_id)
        subgroup_count = 0
        for group in self.groups_api.get_all_subgroups(self.config.dstn_parent_id,
                                                       self.config.destination_host, self.config.destination_token):
            count = self.groups_api.api.get_count(
                self.config.destination_host, self.config.destination_token, "groups/%d/projects" % group["id"])
            sub_count = 0
            if group.get("child_ids", None) is not None:
                for child_id in group["child_ids"]:
                    sub_count += self.projects_api.api.get_count(self.config.destination_host,
                                                                 self.config.destination_token, "groups/%d/projects" % child_id)
            subgroup_count += count
        # return subgroup_count + group_projects
        self.log.inf(
            "Total count of migrated projects: {}".format(subgroup_count))

    def stage_unimported_projects(self):
        ids = []
        with open("{}/data/unimported_projects.txt".format(self.app_path), "r") as f:
            unimported_projects = f.read()
        available_projects = self.projects.get_projects()
        rewritten_projects = {}
        for i in enumerate(available_projects):
            new_obj = available_projects[i]
            id_num = available_projects[i]["path"]
            rewritten_projects[id_num] = new_obj

        unimported_projects = unimported_projects.split("\n")
        for up in unimported_projects:
            if up is not None and up:
                if rewritten_projects.get(up.split("/")[1], None) is not None:
                    ids.append(rewritten_projects.get(up.split("/")[1])["id"])
        if ids is not None and ids:
            pcli = ProjectStageCLI()
            pcli.stage_data(ids, self.dry_run)

    def remove_import_user(self, dst_id, gl_type="project", host=None, token=None):
        import_uid = self.config.import_user_id if not (
            host and token) else self.get_import_user(host, token)
        host = self.config.destination_host if not host else host
        token = self.config.destination_token if not token else token
        self.log.info(
            f"Removing import user (ID: {import_uid}) from {gl_type} (ID: {dst_id})")
        try:
            if gl_type == "group":
                resp = self.groups_api.remove_member(
                    dst_id, import_uid, host, token)
            else:
                resp = self.projects_api.remove_member(
                    dst_id, import_uid, host, token)
            if not isinstance(resp, Response) or resp.status_code not in [204, 404]:
                self.log.error(
                    f"Failed to remove import user (ID: {import_uid}) from {gl_type} (ID: {dst_id}):\n{resp}")
        except RequestException as re:
            self.log.error(
                f"Failed to remove import user (ID: {import_uid}) from {gl_type} (ID: {dst_id}), with error:\n{re}")

    def get_import_user(self, host, token):
        return misc_utils.safe_json_response(self.users_api.get_current_user(host, token)).get('id')

    def handle_member_retention(self, members, dst_id, group=False):
        status = "retained"
        if self.remove_members:
            if group:
                members = misc_utils.safe_json_response(self.groups_api.get_all_group_members(
                    dst_id, self.config.destination_host, self.config.destination_token)) or []
            # Leave the import user as the only (Owner) member
            members = [m for m in members if m["id"]
                       != self.config.import_user_id]
            for m in members:
                # Remove GitLab group or GitHub repo member
                uid = m["id"] if group else m["user_id"]
                if group:
                    resp = self.groups_api.remove_member(
                        dst_id, uid, self.config.destination_host, self.config.destination_token)
                else:
                    resp = self.projects_api.remove_member(
                        dst_id, uid, self.config.destination_host, self.config.destination_token)
                if not isinstance(resp, Response) or resp.status_code != 204:
                    status = "partial"
                    self.log.error(
                        f"Failed to remove {'group' if group else 'project'} {dst_id} member {uid}:\n{resp}")
            status = "partial" if status == "partial" else "removed"
        return status

    def migrate_external_group(self, group):
        result = False
        members = group.pop("members")
        group["full_path"] = mig_utils.get_full_path_with_parent_namespace(
            group["full_path"])
        group["parent_id"] = self.config.dstn_parent_id
        group_id = None
        group["description"] = group.get("description") or ""
        host = self.config.destination_host
        token = self.config.destination_token
        if group_id := self.groups.find_group_id_by_path(host, token, group["full_path"]):
            self.log.info(
                f"{group['full_path']} ({group_id}) found. Skipping import. Adding members")
            result = group_id
        if not self.dry_run:
            result = {}
            if not group_id:
                resp = misc_utils.safe_json_response(
                    self.groups_api.create_group(host, token, group))
                is_error, resp = misc_utils.is_error_message_present(resp)
                if resp and not is_error:
                    group_id = resp.get("id")
                    result["response"] = resp
                else:
                    self.log.error(
                        f"Unable to create group {group['full_path']} due to: {result}")
            if group_id:
                if not self.remove_members:
                    result["members"] = self.groups.add_members_to_destination_group(
                        host, token, group_id, members)
                self.remove_import_user(group_id, gl_type="group")
        return {
            group["full_path"]: result
        }

    def get_ci_client(self, ci_source, host, user, token) -> BaseExternalCiClient:
        """
            Dynamically get and initialize external CI source client class
        """
        for source in EXT_CI_SOURCE_CLASSES:
            if source.source == ci_source:
                return getattr(import_module(source.module), source.class_name)(
                    host,
                    user,
                    token
                )

    def handle_ext_ci_src_migration(self, result, project, project_id):
        for ci_source, ci_configs in self.config.ci_sources.items():
            for config in ci_configs:
                client = self.get_ci_client(
                    ci_source,
                    config[f"{ci_source}_ci_src_hostname"],
                    config[f"{ci_source}_ci_src_username"],
                    string_utils.deobfuscate(
                        config[f"{ci_source}_ci_src_access_token"]
                    )
                )
                result[project["path_with_namespace"]][f"{ci_source}_variables"] = (
                    client.migrate_variables(
                        project,
                        project_id,
                        config[f"{ci_source}_ci_src_hostname"]
                    )
                )
                result[project["path_with_namespace"]][f"{ci_source}_build_configuration"] = (
                    client.migrate_build_configuration(
                        project,
                        project_id
                    )
                )
