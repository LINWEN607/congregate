"""
Congregate - GitLab instance migration utility

Copyright (c) 2024 - GitLab
"""

from gitlab_ps_utils.list_utils import remove_dupes
from congregate.cli.stage_base import BaseStageClass


class UserStageCLI(BaseStageClass):
    def stage_data(self, users_to_stage, dry_run=True,
                   skip_users=False, scm_source=None):
        """
            Stage data based on selected projects on source instance

            :param: projects_to_stage: (dict) the staged projects object
            :param: dry_run (bool) If true, it will only build the staging data lists
            :param: skip_users (bool) If true will skip writing staged users to file
        """
        self.build_staging_data(users_to_stage, dry_run)
        if self.config.source_type == "gitlab":
            self.list_staged_users_without_public_email()
        if not dry_run:
            self.write_staged_users_file()
    
    def build_staging_data(self, users_to_stage, dry_run=False):
        users = self.open_users_file()
        for user in filter(None, users_to_stage):
            for u in users:
                if (user == u["username"]) or (user == str(u["id"])) or (user == u["email"]):
                    self.staged_users.append(u)
                    self.log.info(
                        f"Staging user ({u['email']}) [{len(self.staged_users)}/{len(users)}]")
        return remove_dupes(self.staged_users)
