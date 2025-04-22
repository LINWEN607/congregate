"""
    Congregate - GitLab instance migration utility

    Copyright (c) 2023 - GitLab
"""

from time import time

from gitlab_ps_utils import misc_utils

import congregate.helpers.migrate_utils as mig_utils
from congregate.helpers.utils import rotate_logs
from congregate.helpers.base_class import BaseClass
from congregate.migration.gitlab.projects import ProjectsClient
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.api.project_repository import ProjectRepositoryApi
from congregate.migration.gitlab.variables import VariablesClient
from congregate.migration.gitlab.migrate import GitLabMigrateClient
from congregate.migration.github.migrate import GitHubMigrateClient
from congregate.migration.bitbucket.migrate import BitBucketServerMigrateClient
from congregate.migration.bitbucket_cloud.migrate import BitbucketCloudMigrateClient
from congregate.migration.ado.migrate import AzureDevopsMigrateClient


class MigrateClient(BaseClass):
    def __init__(
        self,
        dry_run=True,
        processes=None,
        only_post_migration_info=False,
        start=time(),
        skip_users=False,
        remove_members=False,
        sync_members=False,
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
        reg_dry_run=False,
        group_structure=False,
        retain_contributors=False
    ):
        self.projects = ProjectsClient()
        self.projects_api = ProjectsApi()
        self.project_repository_api = ProjectRepositoryApi()
        self.variables = VariablesClient()
        super().__init__()
        self.dry_run = dry_run
        self.processes = processes
        self.only_post_migration_info = only_post_migration_info
        self.start = start
        self.skip_users = skip_users
        self.stream_groups = stream_groups
        self.remove_members = remove_members
        self.sync_members = sync_members
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
        self.reg_dry_run = reg_dry_run
        self.retain_contributors = retain_contributors

    def migrate(self):
        self.log.info(
            f"{misc_utils.get_dry_log(self.dry_run)}Migrating data from {self.config.source_host} ({self.config.source_type}) to "
            f"{self.config.destination_host}"
        )

        # Dry-run and log cleanup
        if self.dry_run:
            mig_utils.clean_data(dry_run=False, files=[
                f"{self.app_path}/data/results/dry_run_user_migration.json",
                f"{self.app_path}/data/results/dry_run_group_migration.json",
                f"{self.app_path}/data/results/dry_run_project_migration.json"])
        rotate_logs()

        if self.config.source_type == "gitlab":
            GitLabMigrateClient(dry_run=self.dry_run,
                                processes=self.processes,
                                only_post_migration_info=self.only_post_migration_info,
                                start=self.start,
                                skip_users=self.skip_users,
                                remove_members=self.remove_members,
                                sync_members=self.sync_members,
                                hard_delete=self.hard_delete,
                                stream_groups=self.stream_groups,
                                skip_groups=self.skip_groups,
                                skip_projects=self.skip_projects,
                                skip_group_export=self.skip_group_export,
                                skip_group_import=self.skip_group_import,
                                skip_project_export=self.skip_project_export,
                                skip_project_import=self.skip_project_import,
                                subgroups_only=self.subgroups_only,
                                reg_dry_run=self.reg_dry_run,
                                group_structure=self.group_structure,
                                retain_contributors=self.retain_contributors
                                ).migrate()
        elif self.config.source_type == "bitbucket server":
            BitBucketServerMigrateClient(dry_run=self.dry_run,
                                         processes=self.processes,
                                         only_post_migration_info=self.only_post_migration_info,
                                         start=self.start,
                                         skip_users=self.skip_users,
                                         remove_members=self.remove_members,
                                         hard_delete=self.hard_delete,
                                         stream_groups=self.stream_groups,
                                         skip_groups=self.skip_groups,
                                         skip_projects=self.skip_projects,
                                         skip_group_export=self.skip_group_export,
                                         skip_group_import=self.skip_group_import,
                                         skip_project_export=self.skip_project_export,
                                         skip_project_import=self.skip_project_import,
                                         subgroups_only=self.subgroups_only,
                                         group_structure=self.group_structure
                                         ).migrate()
        elif self.config.source_type == "bitbucket cloud":
            BitbucketCloudMigrateClient(dry_run=self.dry_run,
                                        processes=self.processes,
                                        only_post_migration_info=self.only_post_migration_info,
                                        start=self.start,
                                        skip_users=self.skip_users,
                                        remove_members=self.remove_members,
                                        hard_delete=self.hard_delete,
                                        stream_groups=self.stream_groups,
                                        skip_groups=self.skip_groups,
                                        skip_projects=self.skip_projects,
                                        skip_group_export=self.skip_group_export,
                                        skip_group_import=self.skip_group_import,
                                        skip_project_export=self.skip_project_export,
                                        skip_project_import=self.skip_project_import,
                                        subgroups_only=self.subgroups_only,
                                        group_structure=self.group_structure
                                    ).migrate()
        elif self.config.source_type == "github" or self.config.list_multiple_source_config("github_source"):
            GitHubMigrateClient(dry_run=self.dry_run,
                                processes=self.processes,
                                only_post_migration_info=self.only_post_migration_info,
                                start=self.start,
                                skip_users=self.skip_users,
                                remove_members=self.remove_members,
                                hard_delete=self.hard_delete,
                                stream_groups=self.stream_groups,
                                skip_groups=self.skip_groups,
                                skip_projects=self.skip_projects,
                                skip_group_export=self.skip_group_export,
                                skip_group_import=self.skip_group_import,
                                skip_project_export=self.skip_project_export,
                                skip_project_import=self.skip_project_import,
                                subgroups_only=self.subgroups_only,
                                group_structure=self.group_structure
                                ).migrate()
        elif self.config.source_type == "azure devops":
            AzureDevopsMigrateClient(dry_run=self.dry_run,
                                    processes=self.processes,
                                    only_post_migration_info=self.only_post_migration_info,
                                    start=self.start,
                                    skip_users=self.skip_users,
                                    remove_members=self.remove_members,
                                    hard_delete=self.hard_delete,
                                    stream_groups=self.stream_groups,
                                    skip_groups=self.skip_groups,
                                    skip_projects=self.skip_projects,
                                    skip_group_export=self.skip_group_export,
                                    skip_group_import=self.skip_group_import,
                                    skip_project_export=self.skip_project_export,
                                    skip_project_import=self.skip_project_import,
                                    subgroups_only=self.subgroups_only,
                                    group_structure=self.group_structure
                                    ).migrate()
        
        else:
            self.log.warning(
                f"Configuration (data/congregate.conf) src_type {self.config.source_type} not supported")
        mig_utils.add_post_migration_stats(self.start, log=self.log)
        self.log.warning(
            f"{misc_utils.get_dry_log(self.dry_run)}Completed migrating from {self.config.source_host} to {self.config.destination_host}")
