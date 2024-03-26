"""
Congregate - GitLab instance migration utility

Copyright (c) 2022 - GitLab
"""

import re
import sys
import os

from gitlab_ps_utils.misc_utils import get_dry_log
from gitlab_ps_utils.list_utils import remove_dupes
from gitlab_ps_utils.dict_utils import rewrite_list_into_dict, dig
from gitlab_ps_utils.json_utils import json_pretty

from congregate.helpers.migrate_utils import get_staged_user_projects
from congregate.helpers.utils import is_dot_com
from congregate.cli.stage_base import BaseStageClass


class ProjectStageCLI(BaseStageClass):

    def stage_data(self, projects_to_stage, dry_run=True,
                   skip_users=False, scm_source=None):
        """
            Stage data based on selected projects on source instance

            :param: projects_to_stage: (dict) the staged projects object
            :param: dry_run (bool) If true, it will only build the staging data lists
            :param: skip_users (bool) If true will skip writing staged users to file
        """
        self.build_staging_data(projects_to_stage, dry_run, scm_source)
        if user_projects := get_staged_user_projects(
                remove_dupes(self.staged_projects)):
            self.log.warning(
                f"USER projects staged (Count : {len(user_projects)}):\n{json_pretty(user_projects)}")
            if is_dot_com(self.config.destination_host):
                self.log.warning(
                    "Please manually migrate USER projects to gitlab.com")
        if self.config.source_type == "gitlab":
            self.list_staged_users_without_public_email()
        if not dry_run:
            self.write_staging_files(skip_users=skip_users)

    def build_staging_data(self, projects_to_stage,
                           dry_run=True, scm_source=None):
        """
            Build data up from project level, including groups and users (members)

            :param: projects_to_stage: (dict) the staged projects objects
            :param: dry_run (bool) dry_run (bool) If true, it will only build the staging data lists.
        """
        i = 0
        if scm_source is not None:
            i = self.the_number_of_instance(scm_source)
        if i == -1:
            self.log.warning(
                f"Couldn't find the correct GH instance with hostname: {scm_source}")
        # Loading projects information
        projects = self.open_projects_file(scm_source)
        groups = self.open_groups_file(scm_source)
        users = self.open_users_file(scm_source)

        # Rewriting projects to retrieve objects by ID more efficiently
        self.rewritten_users = rewrite_list_into_dict(users, "id")
        self.rewritten_projects = rewrite_list_into_dict(projects, "id")
        self.rewritten_groups = rewrite_list_into_dict(groups, "id")

        # If there is CLI or UI input
        if list(filter(None, projects_to_stage)):
            # Stage ALL
            if projects_to_stage[0] in ["all", "."] or len(
                    projects_to_stage) == len(projects):
                for p in projects:
                    self.log.info(
                        f"{get_dry_log(dry_run)}Staging project '{p['path_with_namespace']}' (ID: {p['id']})")
                    self.staged_projects.append(self.get_project_metadata(p))

                for g in groups:
                    self.log.info(
                        f"{get_dry_log(dry_run)}Staging group '{g['full_path']}' (ID: {g['id']})")
                    self.staged_groups.append(self.format_group(g))

                for u in users:
                    self.log.info(
                        f"{get_dry_log(dry_run)}Staging user '{u['email']}' (ID: {u['id']})")
                    self.staged_users.append(u)
            # CLI range input
            elif re.search(r"\d+-\d+", projects_to_stage[0]) is not None:
                match = (re.search(r"\d+-\d+", projects_to_stage[0])).group(0)
                start = int(match.split("-")[0])
                if start != 0:
                    start -= 1
                end = int(match.split("-")[1])
                for i in range(start, end):
                    self.append_data(projects[i], projects_to_stage, p_range=range(
                        start, end), dry_run=dry_run)
            # Random selection
            else:
                for i, d in enumerate(projects_to_stage):
                    # Hacky check for id or project name by explicitly checking
                    # variable type
                    try:
                        # Retrieve group object from groups.json
                        project = self.rewritten_projects[int(
                            re.sub("[^0-9]", "", projects_to_stage[i]))]
                    except ValueError:
                        self.log.error(
                            f"Please use a space delimited list of integers (project IDs), NOT {d}")
                        sys.exit(os.EX_IOERR)
                    except KeyError:
                        self.log.error(f"Unknown project ID {d}")
                        sys.exit(os.EX_DATAERR)
                    self.append_data(
                        project, projects_to_stage, dry_run=dry_run)
        else:
            self.log.info("Staging empty list")
            return self.staged_users, self.staged_groups, self.staged_projects
        return remove_dupes(self.staged_projects), remove_dupes(
            self.staged_users), remove_dupes(self.staged_groups)

    def append_data(self, project, projects_to_stage, p_range=0, dry_run=True):
        obj = self.get_project_metadata(project)
        for member in obj.get("members", []):
            self.append_member_to_members_list([], member, dry_run)

        o_id = obj.get("id")
        o_path = obj.get("path_with_namespace")
        o_type = obj.get("project_type")
        try:
            if o_type == "group" or (o_type == "user" and not is_dot_com(self.config.destination_host)):
                if parent_group_id := dig(project, "namespace", "id"):
                    if group_to_stage := self.rewritten_groups[parent_group_id]:
                        self.log.info(
                            f"{get_dry_log(dry_run)}Staging group {group_to_stage['full_path']} (ID: {group_to_stage['id']})")
                        self.staged_groups.append(
                            self.format_group(group_to_stage))

                        # Append all group members to staged users
                        for member in group_to_stage.get("members", []):
                            self.append_member_to_members_list(
                                [], member, dry_run)
                        self.log.info(
                            f"{get_dry_log(dry_run)}Staging project '{o_path}' (ID: {o_id})"
                            f"[{len(self.staged_projects) + 1}/{len(p_range) if p_range else len(projects_to_stage)}]")
                        self.staged_projects.append(obj)
                    else:
                        self.log.warning(
                            f"Project '{o_path}' ({o_id}) parent group ID {parent_group_id} NOT found among listed groups")
                else:
                    self.log.warning(
                        f"Project '{o_path}' ({o_id}) NOT found among listed projects")
            else:
                self.log.warning(
                    f"Please manually migrate '{o_type}' project '{o_path}' to gitlab.com")
        except Exception as e:
            self.log.error(
                f"Failed to append project '{o_path}' ({o_id}) to staged projects:\n{e}")
            sys.exit(os.EX_DATAERR)
