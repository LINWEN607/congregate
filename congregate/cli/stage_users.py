"""
Congregate - GitLab instance migration utility

Copyright (c) 2024 - GitLab
"""

from gitlab_ps_utils.json_utils import write_json_to_file
from gitlab_ps_utils.list_utils import remove_dupes
from congregate.cli.stage_base import BaseStageClass
from congregate.helpers.csv_utils import parse_users_csv


class UserStageCLI(BaseStageClass):
    def __init__(self, format="json"):
        super().__init__()
        self.format = format

    def stage_data(self, users_to_stage, dry_run=True):
        """
            Stage data based on selected projects on source instance

            :param: projects_to_stage: (dict) the staged projects object
            :param: dry_run (bool) If true, it will only build the staging data lists
            :param: skip_users (bool) If true will skip writing staged users to file
        """
        self.build_staging_data(users_to_stage)
        # Direct-transfer uses Placeholder users
        if self.config.source_type == "gitlab" and not self.config.direct_transfer:
            self.are_staged_users_without_public_email()
        if not dry_run:
            write_json_to_file(f"{self.app_path}/data/staged_groups.json", [])
            write_json_to_file(
                f"{self.app_path}/data/staged_projects.json", [])
            self.write_staged_users_file()
            self.log.info(
                "Written metadata to staged users file 'data/staged_users.json', '[]' to staged groups and projects")

    def build_staging_data(self, users_to_stage):
        if self.format.lower() == "csv":
            users = parse_users_csv(self.app_path)
        else:
            users = self.open_users_file()
        if list(filter(None, users_to_stage)):
            if users_to_stage[0] in ["all", "."]:
                for u in users:
                    self.log.info(
                        f"Staging user '{u['email']}' (ID: {u['id']}) [{len(self.staged_users)}/{len(users)}]")
                    self.staged_users.append(u)
            else:
                for user in filter(None, users_to_stage):
                    for u in users:
                        if (user == u["username"]) or (user == str(u["id"])) or (user == u["email"]):
                            self.staged_users.append(u)
                            self.log.info(
                                f"Staging user '{u['email']}' (ID: {u['id']}) [{len(self.staged_users)}/{len(users)}]")
        else:
            self.log.info("Staging empty user list")
            return self.staged_users
        return remove_dupes(self.staged_users)
