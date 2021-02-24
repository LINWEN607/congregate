"""
Congregate - GitLab instance migration utility

Copyright (c) 2021 - GitLab
"""

import re

from congregate.cli.stage_base import BaseStageClass
from congregate.helpers.misc_utils import get_dry_log, remove_dupes, rewrite_list_into_dict


class GroupStageCLI(BaseStageClass):

    def stage_data(self, groups_to_stage, dry_run=True, skip_users=False, scm_source=None):
        """
            Stage data based on selected groups on source instance

            :param: groups_to_stage: (dict) the staged groups object
            :param: dry_run (bool) If true, it will only build the staging data lists
            :param: skip_users (bool) If true will skip writing staged users to file
        """
        self.build_staging_data(groups_to_stage, dry_run, scm_source)
        if not dry_run:
            self.write_staging_files(skip_users=skip_users)

    def build_staging_data(self, groups_to_stage, dry_run=True, scm_source=None):
        """
            Build data down from group level, including sub-groups, projects and users (members)

            :param: groups_to_stage: (dict) the staged groups objects
            :param: dry_run (bool) If true, it will only build the staging data lists.
        """
        i = 0
        if scm_source is not None:
            i = self.the_number_of_instance(scm_source) 
        if i == -1:
            self.log.warning(f"Couldn't find the correct GH instance with hostname: {scm_source}")    
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
            if groups_to_stage[0] in ["all", "."] or len(groups_to_stage) == len(groups):
                for p in projects:
                    self.log.info("{0}Staging project {1} (ID: {2})".format(
                        get_dry_log(dry_run), p["path_with_namespace"], p["id"]))
                    self.staged_projects.append(self.get_project_metadata(p))

                for g in groups:
                    self.log.info("{0}Staging group {1} (ID: {2})".format(
                        get_dry_log(dry_run), g["full_path"], g["id"]))
                    g.pop("projects", None)
                    self.staged_groups.append(g)

                for u in users:
                    self.log.info("{0}Staging user {1} (ID: {2})".format(
                        get_dry_log(dry_run), u["username"], u["id"]))
                    self.staged_users.append(u)
            # CLI range input
            elif re.search(r"\d+-\d+", groups_to_stage[0]) is not None:
                match = (re.search(r"\d+-\d+", groups_to_stage[0])).group(0)
                start = int(match.split("-")[0])
                if start != 0:
                    start -= 1
                end = int(match.split("-")[1])
                for i in range(start, end):
                    # Retrieve group object from groups.json
                    self.append_data(groups[i], groups_to_stage, p_range=range(
                        start, end), dry_run=dry_run)
            # Random selection
            else:
                for i, _ in enumerate(groups_to_stage):
                    # Hacky check for id or project name by explicitly checking
                    # variable type
                    try:
                        # Retrieve group object from groups.json
                        group = self.rewritten_groups[int(
                            re.sub("[^0-9]", "", groups_to_stage[i]))]
                    except (ValueError, KeyError) as e:
                        self.log.error(
                            f"Please use a space delimited list of integers (group IDs):\n{groups_to_stage}\n{e}")
                        exit()
                    self.append_data(group, groups_to_stage, dry_run=dry_run)
        else:
            self.log.info("Staging empty list")
            return self.staged_users, self.staged_groups, self.staged_projects
        return remove_dupes(self.staged_projects), remove_dupes(
            self.staged_users), remove_dupes(self.staged_groups)

    def append_data(self, group, groups_to_stage, p_range=0, dry_run=True):
        # Append all group projects to staged projects
        for project in group["projects"]:
            obj = self.get_project_metadata(project)
            # Append all project members to staged users
            for project_member in obj["members"]:
                self.append_member_to_members_list([], project_member, dry_run)
            self.log.info("{0}Staging project {1} (ID: {2})".format(
                get_dry_log(dry_run), obj["path_with_namespace"], obj["id"]))
            self.staged_projects.append(obj)

        self.log.info("{0}Staging group {1} (ID: {2}) [{3}/{4}]".format(get_dry_log(
            dry_run), group["full_path"], group["id"], len(self.staged_groups) + 1, len(p_range) if p_range else len(groups_to_stage)))
        group.pop("projects", None)
        self.staged_groups.append(group)

        # Append all group members to staged users
        for member in group["members"]:
            self.append_member_to_members_list([], member, dry_run)

