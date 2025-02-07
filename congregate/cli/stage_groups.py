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

from congregate.cli.stage_base import BaseStageClass
from congregate.migration.meta import constants


class GroupStageCLI(BaseStageClass):
    def stage_data(self, groups_to_stage, dry_run=True,
                   skip_users=False, scm_source=None):
        """
            Stage data based on selected groups on source instance
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
        """
        i = 0
        if scm_source is not None:
            i = self.the_number_of_instance(scm_source)
        if i == -1:
            self.log.warning(
                f"Couldn't find the correct GH instance with hostname: {scm_source}")

        groups = self.open_groups_file(scm_source)
        projects = self.open_projects_file(scm_source)
        users = self.open_users_file(scm_source)

        self.rewritten_users = rewrite_list_into_dict(users, "id")
        self.rewritten_projects = rewrite_list_into_dict(projects, "id")
        self.rewritten_groups = rewrite_list_into_dict(groups, "id")

        # Track which groups have already been staged to avoid duplicates
        self.staged_group_ids = set()

        if list(filter(None, groups_to_stage)):
            # Stage ALL
            if self.config.source_type == "azure devops":
                if groups_to_stage[0] in ["all", "."]:
                    # Stage all projects
                    for p in projects:
                        self.log.info(
                            f"{get_dry_log(dry_run)}Staging project '{p['path_with_namespace']}' (ID: {p['id']})")
                        self.staged_projects.append(
                            self.get_project_metadata(p))

                    # Stage all groups
                    for g in groups:
                        self.log.info(
                            f"{get_dry_log(dry_run)}Staging group '{g['full_path']}' (ID: {g['id']})")
                        self.staged_groups.append(self.format_group(g))

                    # Stage all users
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
                    # Stage all projects
                    for p in projects:
                        self.log.info(
                            f"{get_dry_log(dry_run)}Staging project '{p['path_with_namespace']}' (ID: {p['id']})")
                        self.staged_projects.append(self.get_project_metadata(p))
                    # Stage all groups
                    for g in groups:
                        self.log.info(
                            f"{get_dry_log(dry_run)}Staging group '{g['full_path']}' (ID: {g['id']})")
                        self.staged_groups.append(self.format_group(g))
                    # Stage all users
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
                        self.append_data(groups[i], i, groups_to_stage, p_range=range(start, end), dry_run=dry_run)
                # Random selection of group IDs
                else:
                    for i, g in enumerate(groups_to_stage):
                        try:
                            gid = int(re.sub("[^0-9]", "", groups_to_stage[i]))
                            group = self.rewritten_groups[gid]
                        except ValueError:
                            self.log.error(
                                f"Please use a space delimited list of integers (group IDs), NOT {g}")
                            sys.exit(os.EX_IOERR)
                        except KeyError:
                            self.log.error(f"Unknown group ID {g}")
                            sys.exit(os.EX_DATAERR)
                        self.append_data(group, i, groups_to_stage, dry_run=dry_run)
        else:
            self.log.info("Staging empty list")
            return self.staged_users, self.staged_groups, self.staged_projects

        return remove_dupes(self.staged_projects), remove_dupes(
            self.staged_users), remove_dupes(self.staged_groups)

    def append_data(self, group, group_index, groups_to_stage, p_range=0, dry_run=True):
        dry = get_dry_log(dry_run)

        # Stage all parent groups first
        if parent_id := group.get("parent_id"):
            self.add_group_and_parents(parent_id, dry_run)

        # Stage the current group's projects
        for pid in group.get("projects", []):
            obj = self.get_project_metadata(pid, group=True)
            for pm in obj.get("members", []):
                self.append_member_to_members_list([], pm, dry_run)
            self.log.info(f"{dry}Staging project {obj.get('path_with_namespace')} (ID: {obj.get('id')})")
            self.staged_projects.append(obj)

        # Stage descendant groups (and their projects)
        desc_groups = group.get("desc_groups", [])
        for i, dgid in enumerate(desc_groups):
            try:
                desc_group = self.rewritten_groups[dgid]

                # Stage each descendant group's projects
                for pid in desc_group.get("projects", []):
                    obj = self.get_project_metadata(pid, group=True)
                    for pm in obj.get("members", []):
                        self.append_member_to_members_list([], pm, dry_run)
                    self.log.info(f"{dry}Staging project {obj.get('path_with_namespace')} (ID: {obj.get('id')})")
                    self.staged_projects.append(obj)

                self.log.info(
                    f"{dry}Staging descendant group {desc_group['full_path']} (ID: {dgid}) [{i+1}/{len(desc_groups)}]")
                self.staged_groups.append(self.format_group(desc_group))

                for m in desc_group.get("members", []):
                    self.append_member_to_members_list([], m, dry_run)

            except KeyError:
                self.log.error(f"Descendent group ID {dgid} NOT found among listed groups")
                sys.exit(os.EX_DATAERR)

        # Stage all group members
        for m in group.get("members", []):
            self.append_member_to_members_list([], m, dry_run)

        # Stage the current group
        self.log.info(
            f"{dry}Staging group {group['full_path']} (ID: {group['id']}) [{group_index + 1}/{len(p_range) if p_range else len(groups_to_stage)}]")
        self.staged_groups.append(self.format_group(group))


    def add_group_and_parents(self, group_id, dry_run=True):
        """
        Stage all ancestor groups of a given group.
        This does NOT stage the requested group itself, only its parents.
        """
        if group_id in self.staged_group_ids:
            return

        group_to_stage = self.rewritten_groups.get(group_id)
        if not group_to_stage:
            self.log.warning(f"Group ID {group_id} NOT found among listed groups")
            return

        # If there is a parent group, stage it first
        if parent_id := group_to_stage.get("parent_id"):
            self.add_group_and_parents(parent_id, dry_run)

        # Then stage this parent group
        self.log.info(f"{get_dry_log(dry_run)}Staging parent group '{group_to_stage['full_path']}' (ID: {group_to_stage['id']})")
        self.staged_groups.append(self.format_group(group_to_stage))
        self.staged_group_ids.add(group_id)

        # Stage members of this parent group
        for member in group_to_stage.get("members", []):
            self.append_member_to_members_list([], member, dry_run)
