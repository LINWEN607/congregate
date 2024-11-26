"""
Congregate - GitLab instance migration utility

Copyright (c) 2022 - GitLab
"""

import re
import sys
import os

from gitlab_ps_utils.misc_utils import get_dry_log
from gitlab_ps_utils.list_utils import remove_dupes
from gitlab_ps_utils.dict_utils import rewrite_list_into_dict

from congregate.cli.stage_base import BaseStageClass
from congregate.migration.ado import constants


class GroupStageCLI(BaseStageClass):
    def stage_data(self, groups_to_stage, dry_run=True,
                   skip_users=False, scm_source=None):
        """
            Stage data based on selected groups on source instance

            :param: groups_to_stage: (dict) the staged groups object
            :param: dry_run (bool) If true, it will only build the staging data lists
            :param: skip_users (bool) If true will skip writing staged users to file
        """
        self.build_staging_data(groups_to_stage, dry_run, scm_source)
        if self.config.source_type == "gitlab":
            self.list_staged_users_without_public_email()
        if not dry_run:
            self.write_staging_files(skip_users=skip_users)

    def build_staging_data(self, groups_to_stage,
                           dry_run=True, scm_source=None):
        """
            Build data down from group level, including sub-groups, projects and users (members)

            :param: groups_to_stage: (dict) the staged groups objects
            :param: dry_run (bool) If true, it will only build the staging data lists.
        """
        i = 0
        if scm_source is not None:
            i = self.the_number_of_instance(scm_source)
        if i == -1:
            self.log.warning(
                f"Couldn't find the correct GH instance with hostname: {scm_source}")
        # Loading projects information
        groups = self.open_groups_file(scm_source)
        projects = self.open_projects_file(scm_source)
        users = self.open_users_file(scm_source)

        # Rewriting projects to retrieve objects by ID more efficiently
        self.rewritten_users = rewrite_list_into_dict(users, "id")
        self.rewritten_projects = rewrite_list_into_dict(projects, "id")
        self.rewritten_groups = rewrite_list_into_dict(groups, "id")

        # If there is CLI or UI input
        if list(filter(None, groups_to_stage)):
            # Stage ALL
            if self.config.source_type == "azure devops":
                if groups_to_stage[0] in ["all", "."]:
                    for p in projects:
                        self.log.info(
                            f"{get_dry_log(dry_run)}Staging project '{p['path_with_namespace']}' (ID: {p['id']})")
                        self.staged_projects.append(
                            self.get_project_metadata(p))

                    for g in groups:
                        self.log.info(
                            f"{get_dry_log(dry_run)}Staging group '{g['full_path']}' (ID: {g['id']})")
                        self.staged_groups.append(self.format_group(g))

                    for u in users:
                        self.log.info(
                            f"{get_dry_log(dry_run)}Staging user '{u['email']}' (ID: {u['id']})")
                        self.staged_users.append(u)
                elif re.match(constants.UUID_PATTERN, groups_to_stage[0]):
                    groups = [group for group in groups if group["id"]
                              in groups_to_stage]
                    for g in groups:
                        self.log.info(
                            f"{get_dry_log(dry_run)}Staging group '{g['full_path']}' (ID: {g['id']})")
                        self.append_data(
                            g, i, groups_to_stage, dry_run=dry_run)
                else:
                    self.log.error(
                        f"Please use a space delimited list of UUIDs (group IDs), NOT {groups_to_stage[0]}")
                    sys.exit(os.EX_IOERR)

            else:
                if groups_to_stage[0] in ["all", "."]:
                    for p in projects:
                        self.log.info(
                            f"{get_dry_log(dry_run)}Staging project '{p['path_with_namespace']}' (ID: {p['id']})")
                        self.staged_projects.append(
                            self.get_project_metadata(p))

                    for g in groups:
                        self.log.info(
                            f"{get_dry_log(dry_run)}Staging group '{g['full_path']}' (ID: {g['id']})")
                        self.staged_groups.append(self.format_group(g))

                    for u in users:
                        self.log.info(
                            f"{get_dry_log(dry_run)}Staging user '{u['email']}' (ID: {u['id']})")
                        self.staged_users.append(u)
                # CLI range input
                elif re.search(r"\d+-\d+", groups_to_stage[0]) is not None:
                    match = (
                        re.search(r"\d+-\d+", groups_to_stage[0])).group(0)
                    start = int(match.split("-")[0])
                    if start != 0:
                        start -= 1
                    end = int(match.split("-")[1])
                    for i in range(start, end):
                        # Retrieve group object from groups.json
                        self.append_data(groups[i], i, groups_to_stage, p_range=range(
                            start, end), dry_run=dry_run)
                # Random selection
                else:
                    for i, g in enumerate(groups_to_stage):
                        # Hacky check for id or project name by explicitly checking
                        # variable type
                        try:
                            # Retrieve group object from groups.json
                            group = self.rewritten_groups[int(
                                re.sub("[^0-9]", "", groups_to_stage[i]))]
                        except ValueError:
                            self.log.error(
                                f"Please use a space delimited list of integers (group IDs), NOT {g}")
                            sys.exit(os.EX_IOERR)
                        except KeyError:
                            self.log.error(f"Unknown group ID {g}")
                            sys.exit(os.EX_DATAERR)
                        self.append_data(
                            group, i, groups_to_stage, dry_run=dry_run)
        else:
            self.log.info("Staging empty list")
            return self.staged_users, self.staged_groups, self.staged_projects
        return remove_dupes(self.staged_projects), remove_dupes(
            self.staged_users), remove_dupes(self.staged_groups)

    def append_data(self, group, group_index, groups_to_stage, p_range=0, dry_run=True):
        dry = get_dry_log(dry_run)

        # Append all group projects to staged projects
        for pid in group.get("projects", []):
            obj = self.get_project_metadata(pid, group=True)

            # Append all project members to staged users
            for pm in obj.get("members", []):
                self.append_member_to_members_list([], pm, dry_run)
            self.log.info(
                f"{dry}Staging project {obj.get('path_with_namespace')} (ID: {obj.get('id')})")
            self.staged_projects.append(obj)

        # Append all descendant groups to staged groups
        desc_groups = group.get("desc_groups", [])
        for i, dgid in enumerate(desc_groups):
            try:
                desc_group = self.rewritten_groups[dgid]

                # Append all descendant group projects to staged projects
                for pid in desc_group.get("projects", []):
                    obj = self.get_project_metadata(pid, group=True)

                    # Append all project members to staged users
                    for pm in obj.get("members", []):
                        self.append_member_to_members_list([], pm, dry_run)
                    self.log.info(
                        f"{dry}Staging project {obj.get('path_with_namespace')} (ID: {obj.get('id')})")
                    self.staged_projects.append(obj)

                self.log.info(
                    f"{dry}Staging descendant group {desc_group['full_path']} (ID: {dgid}) [{i+1}/{len(desc_groups)}]")
                self.staged_groups.append(self.format_group(desc_group))

                # Append all descendant group members to staged users
                for m in desc_group.get("members", []):
                    self.append_member_to_members_list([], m, dry_run)
            except KeyError:
                self.log.error(
                    f"Descendent group ID {dgid} NOT found among listed groups")
                sys.exit(os.EX_DATAERR)

        # Append all group members to staged users
        for m in group.get("members", []):
            self.append_member_to_members_list([], m, dry_run)

        self.log.info(
            f"{dry}Staging group {group['full_path']} (ID: {group['id']}) [{group_index + 1}/{len(p_range) if p_range else len(groups_to_stage)}]")
        self.staged_groups.append(self.format_group(group))
