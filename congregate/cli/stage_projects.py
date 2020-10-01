"""
Congregate - GitLab instance migration utility

Copyright (c) 2020 - GitLab
"""

import re
from congregate.helpers.migrate_utils import get_staged_user_projects
from congregate.helpers.misc_utils import get_dry_log, remove_dupes, rewrite_list_into_dict
from congregate.cli.stage_base import BaseStageClass


class ProjectStageCLI(BaseStageClass):

    def stage_data(self, projects_to_stage, dry_run=True, skip_users=False):
        """
            Stage data based on selected projects on source instance

            :param: projects_to_stage: (dict) the staged projects object
            :param: dry_run (bool) If true, it will only build the staging data lists
            :param: skip_users (bool) If true will skip writing staged users to file
        """
        self.build_staging_data(projects_to_stage, dry_run)
        if user_projects := get_staged_user_projects(remove_dupes(self.staged_projects)):
            self.log.warning("User projects staged:\n{}".format(
                "\n".join(u for u in user_projects)))
        if not dry_run:
            self.write_staging_files(skip_users=skip_users)

    def build_staging_data(self, projects_to_stage, dry_run=True):
        """
            Build data up from project level, including groups and users (members)

            :param: projects_to_stage: (dict) the staged projects objects
            :param: dry_run (bool) dry_run (bool) If true, it will only build the staging data lists.
        """
        # Loading projects information
        projects = self.open_projects_file()
        groups = self.open_groups_file()
        users = self.open_users_file()

        # Rewriting projects to retrieve objects by ID more efficiently
        self.rewritten_users = rewrite_list_into_dict(users, "id")
        self.rewritten_projects = rewrite_list_into_dict(projects, "id")
        self.rewritten_groups = rewrite_list_into_dict(groups, "id")

        # If there is CLI or UI input
        if list(filter(None, projects_to_stage)):
            # Stage ALL
            if projects_to_stage[0] in ["all", "."] or len(projects_to_stage) == len(projects):
                for p in projects:
                    self.log.info("{0}Staging project {1} (ID: {2})".format(
                        get_dry_log(dry_run), p["path_with_namespace"], p["id"]))
                    self.staged_projects.append(self.get_project_metadata(p))

                for g in groups:
                    self.log.info("{0}Staging group {1} (ID: {2})".format(
                        get_dry_log(dry_run), g["full_path"], g["id"]))
                    # Decrease size of self.staged_groups.json
                    g.pop("projects", None)
                    self.staged_groups.append(g)

                for u in users:
                    self.log.info("{0}Staging user {1} (ID: {2})".format(
                        get_dry_log(dry_run), u["username"], u["id"]))
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
                for i, _ in enumerate(projects_to_stage):
                    # Hacky check for id or project name by explicitly checking
                    # variable type
                    try:
                        # Retrieve group object from groups.json
                        project = self.rewritten_projects[int(
                            re.sub("[^0-9]", "", projects_to_stage[i]))]
                    except (ValueError, KeyError):
                        self.log.error("Please use a space delimited list of integers (project IDs):\n{}".format(
                            projects_to_stage))
                        exit()
                    self.append_data(
                        project, projects_to_stage, dry_run=dry_run)
        else:
            self.log.info("Staging empty list")
            return self.staged_users, self.staged_groups, self.staged_projects
        return remove_dupes(self.staged_projects), remove_dupes(
            self.staged_users), remove_dupes(self.staged_groups)

    def append_data(self, project, projects_to_stage, p_range=0, dry_run=True):
        obj = self.get_project_metadata(project)
        for member in obj["members"]:
            self.append_member_to_members_list([], member, dry_run)

        if obj["project_type"] == "group":
            group_to_stage = self.rewritten_groups[project["namespace"]["id"]]
            self.log.info("{0}Staging group {1} (ID: {2})".format(get_dry_log(
                dry_run), group_to_stage["full_path"], group_to_stage["id"]))
            group_to_stage.pop("projects", None)
            self.staged_groups.append(group_to_stage)

            # Append all group members to staged users
            for member in group_to_stage["members"]:
                self.append_member_to_members_list([], member, dry_run)

        self.log.info("{0}Staging project {1} (ID: {2}) [{3}/{4}]".format(get_dry_log(
            dry_run), obj["path_with_namespace"], obj["id"], len(self.staged_projects) + 1, len(p_range) if p_range else len(projects_to_stage)))
        self.staged_projects.append(obj)
