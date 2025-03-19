"""Congregate - GitLab instance migration utility

Copyright (c) 2022 - GitLab

Usage:
    congregate align-user-mapping-emails [--commit]
    congregate archive-staged-projects [--commit] [--dest] [--scm-source=hostname] [--rollback]
    congregate clean [--commit]
    congregate clean-database [--commit] [--keys]
    congregate configure # Deprecated. Manually create config file and validate it by running 'congregate validate-config'
    congregate count-unarchived-projects [--local]
    congregate create-stage-wave-csv [--commit]
    congregate create-staged-projects-fork-relation [--commit]
    congregate create-staged-projects-structure [--commit] [--disable-cicd]
    congregate delete-all-staged-projects-pull-mirrors [--commit]
    congregate delete-staged-projects-push-mirrors [--all] [--commit]
    congregate deobfuscate
    congregate do-all [--commit]
    congregate do-all-groups-and-projects [--commit]
    congregate do-all-users [--commit]
    congregate dump-database
    congregate filter-projects-by-state [--commit] [--archived]
    congregate find-empty-repos
    congregate find-unimported-projects [--commit]
    congregate generate-diff [--processes=<n>] [--staged] [--rollback] [--scm-source=hostname] [--skip-users] [--skip-groups] [--skip-projects] [--subgroups-only]
    congregate generate-reporting
    congregate generate-seed-data [--commit] # TODO: Refactor, broken
    congregate init
    congregate ldap-group-sync <file-path> [--commit]
    congregate list [--processes=<n>] [--partial] [--skip-users] [--skip-groups] [--skip-group-members] [--skip-projects] [--skip-project-members] [--skip-ci] [--src-instances] [--subset] [--skip-archived-projects] [--only-specific-projects=<ids>]
    congregate list-staged-projects-contributors [--commit]
    congregate map-and-stage-users-by-email-match [--commit]
    congregate map-users [--commit]
    congregate migrate [--commit] [--processes=<n>] [--reporting] [--skip-users] [--remove-members] [--sync-members] [--stream-groups] [--skip-group-export] [--skip-group-import] [--skip-project-export] [--skip-project-import] [--only-post-migration-info] [--subgroups-only] [--scm-source=hostname] [--reg-dry-run] [--group-structure] [--retain-contributors]
    congregate migrate-linked-issues [--commit]
    congregate obfuscate
    congregate pull-mirror-staged-projects [--commit] [--protected-only] [--force] [--overwrite]
    congregate push-mirror-staged-projects [--disabled] [--keep_div_refs] [--force] [--commit]
    congregate reingest <assets>...
    congregate remove-inactive-users [--commit] [--membership]
    congregate remove-users-from-parent-group [--commit]
    congregate rollback [--commit] [--hard-delete] [--skip-users] [--skip-groups] [--skip-projects] [--permanent]
    congregate search-for-staged-users [--table]
    congregate set-bb-read-only-branch-permissions [--bb-projects] [--commit]
    congregate set-bb-read-only-member-permissions [--bb-projects] [--commit]
    congregate set-default-branch [--name=<name>] [--commit]
    congregate set-staged-users-public-email [--commit] [--hide]
    congregate stage-groups <groups>... [--skip-users] [--commit] [--scm-source=hostname]
    congregate stage-projects <projects>... [--skip-users] [--commit] [--scm-source=hostname]
    congregate stage-unimported-projects [--commit] # TODO: Refactor, broken
    congregate stage-users <users>... [--commit]
    congregate stage-wave <wave> [--commit] [--scm-source=hostname]
    congregate stitch-results [--result-type=<project|group|user>] [--no-of-files=<n>] [--head|--tail]
    congregate toggle-maintenance-mode [--commit] [--off] [--dest] [--msg=<multi+word+message>]
    congregate toggle-staged-projects-push-mirror [--disable] [--commit]
    congregate ui
    congregate unarchive-staged-projects [--commit] [--dest] [--scm-source=hostname] [--rollback]
    congregate unset-bb-read-only-branch-permissions [--bb-projects] [--commit]
    congregate unset-bb-read-only-member-permissions [--bb-projects] [--commit]
    congregate update-aws-creds
    congregate update-members-access-level [--commit] [--current-level=<level>] [--target-level=<level>] [--skip-groups] [--skip-projects]
    congregate update-parent-group-members [--commit] [--access-level=<level>] [--add-members]
    congregate url-rewrite-only [--commit]
    congregate validate-config
    congregate validate-staged-groups-schema
    congregate validate-staged-projects-schema
    congregate verify-staged-projects-push-mirror [--disabled] [--keep_div_refs]
    congregate -h | --help
    congregate -v | --version

Options:
    -h, --help                              Show Usage.
    -v, --version                           Show current version of congregate.

Arguments:
    processes                               Set number of processes to run in parallel.
    commit                                  Disable the dry-run and perform the full migration with all reads/writes.
    src-instances                           Present if there are multiple GH source instances
    subset                                  Provide input file with list of URLs to list a subset of groups (--skip-projects) or projects (--skip-groups). BitBucket ONLY.
    scm-source                              Specific SCM source hostname
    skip-users                              Stage: Skip staging users; Migrate: Skip migrating users; Rollback: Remove only groups and projects.
    remove-members                          Remove all members of created (GitHub) or imported (GitLab) groups. Skip adding any members of BitBucket Server repos and projects.
    sync-members                            Align group members list between source and destination by adding missing members on destination.
    hard-delete                             DESTRUCTIVE: Remove user contributions and solely owned groups
    permanent                               DESTRUCTIVE: Permanently delete group and/or project. Otherwise, by default, scheduled for deletion
    stream-groups                           Streamed approach of migrating staged groups in bulk
    skip-groups                             Rollback: Remove only users and projects
    skip-group-members                      Add empty list instead of listing GitLab group members. Skip saving BBS project user groups as GL group members.
    skip-group-export                       Skip exporting groups from source instance
    skip-group-import                       Skip importing groups to destination instance
    skip-projects                           Rollback: Remove only users and empty groups
    skip-archived-projects                  Skip archived projects (Bitbucket only right now)
    skip-project-members                    Add empty list instead of listing GitLab project members. Skip saving BBS repo user groups as GL project members.
    skip-project-export                     Skips the project export and assumes that the project file is already ready
                                                for rewrite. Currently does NOT work for exports through filesystem-aws
    skip-project-import                     Will do all steps up to import (export, re-write exported project json,
                                                etc). Useful for testing export contents. Will also skip any external source imports
    skip-ci                                 Skip migrating data from CI sources
    only-post-migration-info                Skips migrating all content except for post-migration information. Use when import is handled outside of congregate
    only-specific-projects                  List only specific projects (comma separated IDs) and their dependencies (Azure DevOps only right now)
    subgroups-only                          Expects that only sub-groups are staged and that their parent groups already exist on destination
    reg-dry-run                             If registry migration is configured, instead of doing the actual migration, write the tags to the logs for use in the brute force migration. Can also be useful when renaming targets
    retain-contributors                     Searches a project for all contributors to a project and adds them as members before exporting the project. Only required for GitLab file-based migrations.
    group-structure                         Let the GitHub and BitBucket Server importers create the missing sub-group layers.
    access-level                            Update parent group level user permissions (None/Minimal/Guest/Reporter/Developer/Maintainer/Owner).
    current-level                           Current destination group/project members access level.
    target-level                            Target destination group/project members access level.
    staged                                  Compare using staged data
    no-of-files                             Number of files used to go back when stitching JSON results
    result-type                             For stitching result files. Options are project, group, or user
    head                                    Read results files in chronological order
    tail                                    Read results files in reverse chronological order (default for stitch-results)
    partial                                 Option used when listing. Keeps existing data in mongo instead of dropping it before retrieving new data
    off                                     Toggle maintenance mode off, otherwise on by default
    dest                                    Toggle maintenance mode on destination instance
    msg                                     Maintenance mode message, with "+" in place of " "
    reporting                               Create reporting issues, based off reporting data supplied in congregate.conf
    archived                                Filter out archived projects from the list of staged projects
    membership                              Remove inactive members from staged groups and projects on source
    local                                   Use locally listed data instead of API
    keys                                    Drop all collections of deploy keys creation, gathered during multiple migration waves. Use when migrating from scratch
    hide                                    Unset metadata field i.e. set to None/null
    disable-cicd                            Disable CI/CD when creating empty GitLab project structures
    disabled                                Disable project push mirror when creating it
    disable                                 Disable staged project push mirror
    keep_div_refs                           Set keep_divergent_refs to True (False by default) and avoid overwriting changes on the mirror repo
    force                                   Immediately trigger push mirroring with a repo change e.g. new branch
    overwrite                               DESTRUCTIVE: Overwrites pull mirrored branches on destination that have diverged from source. Therefore, recommended to make change in new branches on destination instead.
    name                                    Project branch name
    all                                     Include all listed objects.
    bb-projects                             Target BitBucket repo branches from a project level

Commands:
    list                                    List all projects of a source instance and save it to {CONGREGATE_PATH}/data/projects.json.
    init                                    Creates additional directories and files required by congregate
    configure                               Configure congregate for migrating between two instances and save it to {CONGREGATE_PATH}/data/congregate.conf.
    validate-config                         Run configuration validator
    generate-reporting                      Run reporting on staged projects.
    stage-projects                          Stage projects to {CONGREGATE_PATH}/data/staged_projects.json,
                                                their parent groups to {CONGREGATE_PATH}/data/staged_groups.json.
                                                all project and group members to {CONGREGATE_PATH}/data/staged_users.json,
                                                All projects can be staged with '.' or 'all'.
                                                Individual ones can be staged as a space delimited list of integers (project IDs).
    stage-groups                            Stage groups and sub-groups to {CONGREGATE_PATH}/data/staged_groups.json,
                                                all their projects (except shared - with_shared=False) to {CONGREGATE_PATH}/data/staged_projects.json,
                                                all project and group members to {CONGREGATE_PATH}/data/staged_users.json,
                                                All groups can be staged with '.' or 'all'.
                                                Individual ones can be staged as a space delimited list of integers (group IDs).
    stage-users                             Stage individual users {CONGREGATE_PATH}/data/staged_users.json
    stage-wave                              Stage wave of projects based on migration wave spreadsheet. This only takes a single wave for input.
                                                Add '--skip-group-import' to avoid creating groups.
                                                Add '--group-structure' to allow the GitHub and BitBucket Server importers to create the missing sub-group layers.
    create-stage-wave-csv                   Generate a baseline version of the CSV for stage wave from the listed data
    migrate                                 Commence migration based on configuration and staged assets.
    rollback                                Remove staged users/groups/projects on destination.
    ui                                      Deploy UI to port 8000.
    do-all*                                 Configure system, retrieve all projects, users, and groups, stage all information, and commence migration.
    search-for-staged-users                 Search for staged users on destination by primary email
    update-aws-creds                        Run awscli commands based on the keys stored in the config. Useful for docker updates.
    update-parent-group-members             Add (optional) and/or update access levels (to Guest by default) of all staged users for a configured GitLab destination parent group.
    update-members-access-level             Update access level (to Guest by default) of all staged group and project members on destination GitLab instance.
    remove-inactive-users                   Remove all inactive users from staged projects and groups.
    find-unimported-projects                Return a list of projects that failed import.
    stage-unimported-projects               Stage unimported projects based on {CONGREGATE_PATH}/data/unimported_projects.txt.
    url-rewrite-only                        Performs the URL rewrite portion of a migration as a stand-alone step, instead of as a post-migration step. Requires the projects to be staged, and to exist on destination
    remove-users-from-parent-group          Remove all users with at most Reporter access from the parent group.
    migrate-linked-issues                   Migrate Linked items in issues for staged projects.
    pull-mirror-staged-projects             Create and start project pull mirroring for staged projects.
    push-mirror-staged-projects             Set up and enable (by default) project push mirroring for staged projects.
                                                Assuming both the mirrored repo and empty project structure (create-staged-projects-structure) for mirroring already exist on destination.
                                                NOTE: Destination instance only mirroring.
    toggle-staged-projects-push-mirror      Enable/disable push mirror created via command push-mirror-staged-projects.
                                                NOTE: Destination instance only mirroring.
    verify-staged-projects-push-mirror      Verify that each staged project push mirror exists and is not failing. Preferably run a few minutes after creating push mirrors.
    delete-staged-projects-push-mirrors     Remove project push mirrors for staged projects. Only remove destination instance host (+'dstn_parent_group_path' if configured) mirrors. Add '--all' to remove all mirrors.
    delete-all-staged-projects-pull-mirrors Remove all project pull mirrors for staged projects.
    set-default-branch                      Set default branch for staged projects on destination.
    count-unarchived-projects               Return total number and list of all unarchived projects on source.
    find-empty-repos                        Inspect project repo sizes between source and destination instance in search for empty repos.
                                                This could be misleading as it sometimes shows 0 (zero) commits/tags/bytes for fully migrated projects.
    archive-staged-projects                 Archive GitLab source (or destination if '--dest') projects that are staged, not necessarily migrated.
    unarchive-staged-projects               Unarchive GitLab source (or destination if '--dest') projects that are staged, not necessarily migrate.
    set-bb-read-only-branch-permissions     Add read-only branch permission/restriction to all branches (*) on staged BitBucket repos (or projects if '--bb-projects').
    unset-bb-read-only-branch-permissions   Remove read-only branch permission/restriction from all branches (*) on staged BitBucket repos (or projects if '--bb-projects').
    set-bb-read-only-member-permissions     Demote ALL non-read-only staged repo and project users and groups to REPO_READ i.e. PROJECT_READ permissions.
    unset-bb-read-only-member-permissions   Promote back permissions for ALL staged repo and project users and groups demoted by 'set-bb-read-only-member-permissions'.
    filter-projects-by-state                Filter out projects by state archived or unarchived (default) from the list of staged projects and overwrite staged_projects.json.
                                                GitLab source only
    generate-seed-data                      Generate dummy data to test a migration.
    validate-staged-groups-schema           Check staged_groups.json for missing group data.
    validate-staged-projects-schema         Check staged_projects.json for missing project data.
    clean                                   Delete all retrieved and staged data
    stitch-results                          Stitches together migration results from multiple migration runs
    generate-diff                           Generates HTML files containing the diff results of the migration
    map-users                               Maps staged user emails to emails defined in the user-provided user_map.csv
    map-and-stage-users-by-email-match      Maps staged user emails to emails defined in the user-provided user_map.csv. Matches by old/new email instead of username
    obfuscate                               Obfuscate a secret or password that you want to manually update in the config.
    deobfuscate                             Deobfuscate a secret or password from the config.
    dump-database                           Dump all database collections to various JSON files
    reingest                                Reingest database dumps into mongo. Specify the asset type (users, groups, projects, teamcity, jenkins)
    clean-database                          Drop all collections in the congregate MongoDB database and rebuilds the structure
    toggle-maintenance-mode                 Reduce write operations to a minimum by blocking all external actions that change the internal state. Operational as of GitLab version 13.9
    ldap-group-sync                         Perform LDAP Group sync operations over a pipe-delimited file of group_id|CN
    set-staged-users-public-email           Set/unset the staged users public_email field on source. Mandatory for migrations from GitLab 14.0+.
    align-user-mapping-emails               Add new email to source users based on 'user_mapping_by_<field>.json' src:dest primary/public email mapping file.
    create-staged-projects-structure        Create empty project structures on GitLab destination for staged projects. Optionally, disable CI/CD on creation.
    create-staged-projects-fork-relation    Create a forked from/to relation between (group) projects on destination, based on staged projects. Assumes fork and forked project have already been migrated.
    list-staged-projects-contributors       List all non-member contributors for all staged projects and save to file. GitLab ONLY.
"""

import os
import subprocess
from sys import platform
from pathlib import Path
from json import dump, dumps
from time import time
from toml import load as load_toml
from docopt import docopt

if __name__ == '__main__':
    if __package__ is None:
        import sys
        sys.path.append(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))))
    from gitlab_ps_utils.logger import myLogger
    from gitlab_ps_utils.misc_utils import strip_netloc
    from gitlab_ps_utils.dict_utils import dig
    from gitlab_ps_utils.string_utils import obfuscate, deobfuscate
    from congregate.helpers import conf
    from congregate.helpers.configuration_validator import ConfigurationValidator
    from congregate.helpers.utils import get_congregate_path, rotate_logs, stitch_json_results
    from congregate.helpers.ui_utils import spin_up_ui
else:
    import sys
    sys.path.append(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))
    from gitlab_ps_utils.logger import myLogger
    from gitlab_ps_utils.misc_utils import strip_netloc
    from gitlab_ps_utils.dict_utils import dig
    from gitlab_ps_utils.string_utils import obfuscate, deobfuscate
    from congregate.helpers import conf
    from congregate.helpers.configuration_validator import ConfigurationValidator
    from congregate.helpers.utils import get_congregate_path, rotate_logs, stitch_json_results
    from congregate.helpers.ui_utils import spin_up_ui

app_path = get_congregate_path()


def main():
    if __name__ == '__main__':
        arguments = docopt(__doc__)
        if arguments["init"]:
            Path("data/logs").mkdir(parents=True, exist_ok=True)
            Path("data/results").mkdir(parents=True, exist_ok=True)
            Path("data/reg_tuples").mkdir(parents=True, exist_ok=True)
            if not os.path.exists(f"{app_path}/data/logs/congregate.log"):
                with open(f"{app_path}/data/logs/congregate.log", "w") as f:
                    f.write("")
            log = myLogger(__name__)
        else:
            log = myLogger(__name__)

        if arguments["--version"]:
            with open(f"{app_path}/pyproject.toml", "r") as f:
                print(
                    f"Congregate {dig(load_toml(f), 'tool', 'poetry', 'version')}")
            sys.exit(os.EX_OK)
        DRY_RUN = not arguments["--commit"]
        STAGED = arguments["--staged"]
        ROLLBACK = arguments["--rollback"]
        PROCESSES = arguments["--processes"] or conf.Config().processes
        SKIP_USERS = arguments["--skip-users"]
        SKIP_GROUPS = arguments["--skip-groups"]
        SKIP_PROJECTS = arguments["--skip-projects"]
        REMOVE_MEMBERS = arguments["--remove-members"]
        SYNC_MEMBERS = arguments["--sync-members"]
        ONLY_POST_MIGRATION_INFO = arguments["--only-post-migration-info"]
        PARTIAL = arguments["--partial"]
        SRC_INSTANCES = arguments["--src-instances"]
        SCM_SOURCE = arguments["--scm-source"]
        ARCHIVED = arguments["--archived"]
        MEMBERSHIP = arguments["--membership"]
        SUBGROUPS_ONLY = arguments["--subgroups-only"]
        DEST = arguments["--dest"]

        if SCM_SOURCE:
            SCM_SOURCE = strip_netloc(SCM_SOURCE)

        from congregate.helpers.migrate_utils import clean_data, add_post_migration_stats, write_results_to_file, toggle_maintenance_mode

        if arguments["obfuscate"]:
            data = obfuscate("Secret:")
            if platform == "darwin":
                subprocess.run("pbcopy", universal_newlines=True,
                               input=data, check=True)
                print("Masked secret copied to clipboard (pbcopy)")
            else:
                print(f"Masked secret: {data}")
        elif arguments["deobfuscate"]:
            data = deobfuscate(input("Masked secret:"))
            if platform == "darwin":
                subprocess.run("pbcopy", universal_newlines=True,
                               input=data, check=True)
                print("Secret copied to clipboard (pbcopy)")
            else:
                print(f"Secret: {data}")
        elif arguments["configure"]:
            log.info(
                "Config CLI has been Deprecated. Validate config file by running `congregate validate-config`")
        elif arguments["validate-config"]:
            c = ConfigurationValidator()
            for v in dir(c):
                getattr(c, v)
        else:
            from gitlab_ps_utils.string_utils import convert_to_underscores
            from congregate.migration.gitlab.users import UsersClient
            from congregate.migration.gitlab.groups import GroupsClient
            from congregate.migration.gitlab.projects import ProjectsClient
            from congregate.migration.gitlab.variables import VariablesClient
            from congregate.migration.migrate import MigrateClient
            from congregate.migration.meta.base_migrate import MigrateClient as BaseMigrateClient
            from congregate.migration.gitlab.migrate import GitLabMigrateClient
            from congregate.migration.gitlab.branches import BranchesClient
            from congregate.cli import do_all
            from congregate.cli.list_source import ListClient
            from congregate.cli.stage_projects import ProjectStageCLI
            from congregate.cli.stage_groups import GroupStageCLI
            from congregate.cli.stage_users import UserStageCLI
            from congregate.cli.stage_wave import WaveStageCLI
            from congregate.cli.stage_wave_csv_generator import WaveStageCSVGeneratorCLI
            from congregate.helpers.seed.generator import SeedDataGenerator
            from congregate.migration.gitlab.diff.userdiff import UserDiffClient
            from congregate.migration.gitlab.diff.projectdiff import ProjectDiffClient
            from congregate.migration.gitlab.diff.groupdiff import GroupDiffClient
            from congregate.migration.github.diff.repodiff import RepoDiffClient as GHRepoDiffClient
            from congregate.migration.bitbucket.diff.repodiff import RepoDiffClient as BBSRepoDiffClient
            from congregate.helpers.user_util import map_users, map_and_stage_users_by_email_match
            from congregate.helpers.congregate_mdbc import CongregateMongoConnector
            from congregate.migration.github.repos import ReposClient as GHReposClient
            from congregate.migration.bitbucket.repos import ReposClient as BBReposClient
            from congregate.cli.ldap_group_sync import LdapGroupSync
            from congregate.migration.codecommit.projects import ProjectsClient
            from congregate.migration.codecommit.api.base import CodeCommitApiWrapper
            from congregate.migration.codecommit.base import CodeCommitWrapper
            from congregate.migration.codecommit.migrate import CodeCommitMigrateClient



            config = conf.Config()
            users = UsersClient()
            groups = GroupsClient()
            projects = ProjectsClient()
            bb_repos = BBReposClient()
            variables = VariablesClient()
            branches = BranchesClient()

            if not config.ssl_verify:
                log.warning(
                    "ssl_verify is set to False. Suppressing downstream SSL warnings. Consider enforcing SSL "
                    "verification in the future"
                )

            if arguments["list"]:
                start = time()
                rotate_logs()
                list_client = ListClient(
                    processes=PROCESSES,
                    partial=PARTIAL,
                    skip_users=SKIP_USERS,
                    skip_groups=SKIP_GROUPS,
                    skip_group_members=arguments["--skip-group-members"],
                    skip_projects=SKIP_PROJECTS,
                    skip_project_members=arguments["--skip-project-members"],
                    skip_ci=arguments["--skip-ci"],
                    src_instances=SRC_INSTANCES,
                    subset=arguments["--subset"],
                    skip_archived_projects=arguments["--skip-archived-projects"],
                    only_specific_projects=arguments["--only-specific-projects"]
                )
                list_client.list_data()
                add_post_migration_stats(start, log=log)

            if arguments["generate-reporting"] or arguments["--reporting"]:
                pass

            if arguments["stage-projects"]:
                pcli = ProjectStageCLI()
                pcli.stage_data(arguments['<projects>'],
                                dry_run=DRY_RUN, skip_users=SKIP_USERS, scm_source=SCM_SOURCE)

            if arguments["stage-groups"]:
                gcli = GroupStageCLI()
                gcli.stage_data(arguments['<groups>'],
                                dry_run=DRY_RUN, skip_users=SKIP_USERS, scm_source=SCM_SOURCE)

            if arguments["stage-users"]:
                ucli = UserStageCLI()
                ucli.stage_data(arguments['<users>'], dry_run=DRY_RUN)

            if arguments["stage-wave"]:
                wcli = WaveStageCLI()
                wcli.stage_data(
                    arguments['<wave>'], dry_run=DRY_RUN, skip_users=SKIP_USERS, scm_source=SCM_SOURCE)

            if arguments["create-stage-wave-csv"]:
                wscsvCli = WaveStageCSVGeneratorCLI()
                wscsvCli.generate(
                    destination_file=config.wave_spreadsheet_path,
                    header_info={
                        "headers": config.wave_spreadsheet_columns,
                        "header_map": config.wave_spreadsheet_column_to_project_property_mapping
                    },
                    dry_run=DRY_RUN
                )

            if arguments["migrate-linked-issues"]:
                migrate = GitLabMigrateClient(dry_run=DRY_RUN)
                migrate.migrate_linked_items_in_issues()

            if arguments["migrate"]:
                migrate = MigrateClient(
                    processes=PROCESSES,
                    dry_run=DRY_RUN,
                    skip_users=SKIP_USERS,
                    remove_members=REMOVE_MEMBERS,
                    sync_members=SYNC_MEMBERS,
                    stream_groups=arguments["--stream-groups"],
                    skip_group_export=bool(
                        arguments["--skip-group-export"] or ONLY_POST_MIGRATION_INFO),
                    skip_group_import=arguments["--skip-group-import"],
                    skip_project_export=bool(
                        arguments["--skip-project-export"] or ONLY_POST_MIGRATION_INFO),
                    skip_project_import=arguments["--skip-project-import"],
                    only_post_migration_info=ONLY_POST_MIGRATION_INFO,
                    subgroups_only=SUBGROUPS_ONLY,
                    scm_source=SCM_SOURCE,
                    reg_dry_run=arguments["--reg-dry-run"],
                    group_structure=arguments["--group-structure"],
                    retain_contributors=arguments["--retain-contributors"]
                )
                migrate.migrate()

            if arguments["rollback"]:
                migrate = BaseMigrateClient(
                    dry_run=DRY_RUN,
                    skip_users=SKIP_USERS,
                    hard_delete=arguments["--hard-delete"],
                    skip_groups=SKIP_GROUPS,
                    skip_projects=SKIP_PROJECTS,
                    permanent=arguments["--permanent"],
                )
                migrate.rollback()

            if arguments["do-all"]:
                do_all.do_all(dry_run=DRY_RUN)
            if arguments["do-all-users"]:
                do_all.do_all_users(dry_run=DRY_RUN)
            if arguments["do-all-groups-and-projects"]:
                do_all.do_all_groups_and_projects(dry_run=DRY_RUN)
            if arguments["ui"]:
                spin_up_ui(app_path, config.ui_port)
            if arguments["search-for-staged-users"]:
                users.search_for_staged_users(table=arguments["--table"])
            if arguments["update-parent-group-members"]:
                access_level = arguments["--access-level"] or "Guest"
                users.update_parent_group_members(
                    access_level, add_members=arguments["--add-members"], dry_run=DRY_RUN)
            if arguments["update-members-access-level"]:
                current_level = arguments["--current-level"] or "Owner"
                target_level = arguments["--target-level"] or "Guest"
                users.update_members_access_level(
                    current_level, target_level, skip_groups=SKIP_GROUPS, skip_projects=SKIP_PROJECTS, dry_run=DRY_RUN)
            if arguments["update-aws-creds"]:
                if config.s3_access_key and config.s3_secret_key:
                    command = f"aws configure set aws_access_key_id {config.s3_access_key}"
                    subprocess.call(command.split(" "))
                    command = f"aws configure set aws_secret_access_key {config.s3_secret_key}"
                    subprocess.call(command.split(" "))
                    log.info(
                        "Configured local AWS access and secret keys (~/.aws/credentials)")
                else:
                    log.warning(
                        f"No AWS configuration. Export location: {config.location}")
            if arguments["remove-inactive-users"]:
                users.remove_inactive_users(
                    membership=MEMBERSHIP, dry_run=DRY_RUN)
            if arguments["find-unimported-projects"]:
                projects.find_unimported_projects(dry_run=DRY_RUN)
            if arguments["stage-unimported-projects"]:
                BaseMigrateClient(dry_run=DRY_RUN).stage_unimported_projects()
            if arguments["remove-users-from-parent-group"]:
                users.remove_users_from_parent_group(dry_run=DRY_RUN)
            if arguments["delete-all-staged-projects-pull-mirrors"]:
                projects.delete_all_pull_mirrors(dry_run=DRY_RUN)
            if arguments["pull-mirror-staged-projects"]:
                projects.pull_mirror_staged_projects(
                    protected_only=arguments["--protected-only"], force=arguments["--force"], overwrite=arguments["--overwrite"], dry_run=DRY_RUN)
            if arguments["push-mirror-staged-projects"]:
                projects.push_mirror_staged_projects(
                    disabled=arguments["--disabled"], keep_div_refs=arguments["--keep_div_refs"], force=arguments["--force"], dry_run=DRY_RUN)
            if arguments["toggle-staged-projects-push-mirror"]:
                projects.toggle_staged_projects_push_mirror(
                    disable=arguments["--disable"], dry_run=DRY_RUN)
            if arguments["verify-staged-projects-push-mirror"]:
                projects.verify_staged_projects_push_mirror(
                    disabled=arguments["--disabled"], keep_div_refs=arguments["--keep_div_refs"])
            if arguments["delete-staged-projects-push-mirrors"]:
                projects.delete_staged_projects_push_mirrors(
                    remove_all=arguments["--all"], dry_run=DRY_RUN)
            if arguments["set-default-branch"]:
                branches.set_default_branch(
                    name=arguments["--name"], dry_run=DRY_RUN)
            if arguments["count-unarchived-projects"]:
                projects.count_unarchived_projects(local=arguments["--local"])
            if arguments["archive-staged-projects"]:
                # GitLab as source and/or destination instance
                if (config.source_type == "gitlab") or DEST:
                    projects.update_staged_projects_archive_state(
                        dest=DEST, dry_run=DRY_RUN, rollback=ROLLBACK)
                elif config.source_type == "github" or config.list_multiple_source_config("github_source"):
                    for single_source in config.list_multiple_source_config(
                            "github_source"):
                        if SCM_SOURCE in single_source.get("src_hostname"):
                            gh_repos = GHReposClient(single_source["src_hostname"], deobfuscate(
                                single_source["src_access_token"]))
                    gh_repos = GHReposClient(
                        config.source_host, config.source_token)
                    gh_repos.update_staged_repos_archive_state(dry_run=DRY_RUN)
                else:
                    log.warning(
                        f"Bulk archive not available for {config.source_type}. Did you mean to add '--dest'?")
            if arguments["unarchive-staged-projects"]:
                # GitLab as source and/or destination instance
                if (config.source_type == "gitlab") or DEST:
                    projects.update_staged_projects_archive_state(
                        archive=False, dest=DEST, dry_run=DRY_RUN, rollback=ROLLBACK)
                elif config.source_type == "github" or config.list_multiple_source_config("github_source"):
                    if SCM_SOURCE is not None:
                        for single_source in config.list_multiple_source_config(
                                "github_source"):
                            if SCM_SOURCE in single_source.get(
                                    "src_hostname"):
                                gh_repos = GHReposClient(single_source["src_hostname"], deobfuscate(
                                    single_source["src_access_token"]))
                    else:
                        gh_repos = GHReposClient(
                            config.source_host, config.source_token)
                    gh_repos.update_staged_repos_archive_state(
                        archived=False, dry_run=DRY_RUN)
                else:
                    log.warning(
                        f"Bulk unarchive not available for {config.source_type}. Did you mean to add '--dest'?")
            if arguments["set-bb-read-only-branch-permissions"]:
                if config.source_type == "bitbucket server":
                    bb_repos.update_branch_permissions(
                        is_project=arguments["--bb-projects"], dry_run=DRY_RUN)
                else:
                    log.warning(
                        "This command is ONLY intended for BitBucket source instances")
            if arguments["unset-bb-read-only-branch-permissions"]:
                if config.source_type == "bitbucket server":
                    bb_repos.update_branch_permissions(
                        restrict=False, is_project=arguments["--bb-projects"], dry_run=DRY_RUN)
                else:
                    log.warning(
                        "This command is ONLY intended for BitBucket source instances. Skipping")
            if arguments["set-bb-read-only-member-permissions"]:
                if config.source_type == "bitbucket server":
                    bb_repos.update_member_permissions(
                        is_project=arguments["--bb-projects"], dry_run=DRY_RUN)
                else:
                    log.warning(
                        "This command is ONLY intended for BitBucket source instances. Skipping")
            if arguments["unset-bb-read-only-member-permissions"]:
                if config.source_type == "bitbucket server":
                    bb_repos.update_member_permissions(
                        restrict=False, is_project=arguments["--bb-projects"], dry_run=DRY_RUN)
                else:
                    log.warning(
                        "This command is ONLY intended for BitBucket source instances")
            if arguments["filter-projects-by-state"]:
                if config.source_type == "gitlab":
                    projects.filter_projects_by_state(
                        archived=ARCHIVED, dry_run=DRY_RUN)
                else:
                    log.warning(
                        f"The 'archived' field is currently not present when listing on {config.source_type}")
            if arguments["find-empty-repos"]:
                projects.find_empty_repos()
            if arguments["generate-seed-data"]:
                s = SeedDataGenerator()
                s.generate_seed_data(dry_run=DRY_RUN)
            if arguments["validate-staged-groups-schema"]:
                groups.validate_staged_groups_schema()
            if arguments["validate-staged-projects-schema"]:
                projects.validate_staged_projects_schema()
            if arguments["map-users"]:
                map_users(dry_run=DRY_RUN)
            if arguments["map-and-stage-users-by-email-match"]:
                map_and_stage_users_by_email_match(dry_run=DRY_RUN)
            if arguments["clean"]:
                clean_data(dry_run=DRY_RUN)
            if arguments["generate-diff"]:
                start = time()
                rotate_logs()
                if config.source_type == "gitlab":
                    if not SKIP_USERS:
                        user_diff = UserDiffClient(
                            staged=STAGED,
                            processes=PROCESSES,
                            rollback=ROLLBACK
                        )
                        user_diff.generate_html_report(
                            "User",
                            user_diff.generate_diff_report(start),
                            "/data/results/user_migration_results.html"
                        )
                    if not SKIP_GROUPS:
                        group_diff = GroupDiffClient(
                            staged=STAGED,
                            subgroups_only=SUBGROUPS_ONLY,
                            processes=PROCESSES,
                            rollback=ROLLBACK
                        )
                        group_diff.generate_html_report(
                            "Group",
                            group_diff.generate_diff_report(start),
                            "/data/results/group_migration_results.html"
                        )
                    if not SKIP_PROJECTS:
                        project_diff = ProjectDiffClient(
                            staged=STAGED,
                            processes=PROCESSES,
                            rollback=ROLLBACK
                        )
                        project_diff.generate_html_report(
                            "Project",
                            project_diff.generate_diff_report(start),
                            "/data/results/project_migration_results.html"
                        )
                elif config.source_type == "bitbucket server":
                    repo_diff = BBSRepoDiffClient(
                        staged=STAGED,
                        processes=PROCESSES,
                        rollback=ROLLBACK
                    )
                    repo_diff.generate_diff_report(start)
                    repo_diff.generate_split_html_report()
                elif config.source_type == "github" or SCM_SOURCE is not None:
                    if SCM_SOURCE is not None:
                        for single_instance in config.list_multiple_source_config(
                                "github_source"):
                            if SCM_SOURCE == strip_netloc(
                                    single_instance.get('src_hostname', '')):
                                repo_diff = GHRepoDiffClient(
                                    single_instance['src_hostname'],
                                    deobfuscate(
                                        single_instance['src_access_token']),
                                    staged=STAGED,
                                    processes=PROCESSES,
                                    rollback=ROLLBACK,
                                )
                    else:
                        repo_diff = GHRepoDiffClient(
                            config.source_host,
                            config.source_token,
                            staged=STAGED,
                            processes=PROCESSES,
                            rollback=ROLLBACK
                        )
                    repo_diff.generate_diff_report(start)
                    repo_diff.generate_split_html_report()
                add_post_migration_stats(start, log=log)

            if arguments["stitch-results"]:
                result_type = str(
                    arguments["--result-type"]).rstrip("s") if arguments["--result-type"] else "project"
                steps = int(arguments["--no-of-files"]
                            ) if arguments["--no-of-files"] else 0
                if arguments["--head"]:
                    order = "head"
                else:
                    order = "tail"
                new_results = stitch_json_results(
                    result_type=result_type, steps=steps, order=order)
                write_results_to_file(new_results, result_type, log=log)
            if arguments["dump-database"]:
                m = CongregateMongoConnector()
                for collection in m.db.list_collection_names():
                    print(f"Dumping collection {collection} to file")
                    m.dump_collection_to_file(
                        collection, f"{app_path}/data/{convert_to_underscores(collection)}.json")
            if arguments["reingest"]:
                m = CongregateMongoConnector()
                for asset in arguments["<assets>"]:
                    print(f"Reingesting {asset} into database")
                    m.re_ingest_into_mongo(asset)
            if arguments["clean-database"]:
                if not DRY_RUN:
                    m = CongregateMongoConnector()
                    m.clean_db(keys=arguments["--keys"])
                else:
                    print("\nThis command will drop all collections in the congregate database and then recreate the structure. Please append `--commit` to clean the database")
            if arguments["toggle-maintenance-mode"]:
                toggle_maintenance_mode(
                    off=arguments["--off"],
                    msg=arguments["--msg"],
                    dest=DEST,
                    dry_run=DRY_RUN)
            if arguments["ldap-group-sync"]:
                ldap = LdapGroupSync()
                ldap.load_pdv(arguments['<file-path>'])
                ldap.synchronize_groups(dry_run=DRY_RUN)
            if arguments["set-staged-users-public-email"]:
                users.set_staged_users_public_email(
                    dry_run=DRY_RUN, hide=arguments["--hide"])
            if arguments["align-user-mapping-emails"]:
                users.align_user_mapping_emails(dry_run=DRY_RUN)
            if arguments["create-staged-projects-structure"]:
                projects.create_staged_projects_structure(
                    dry_run=DRY_RUN, disable_cicd=arguments["--disable-cicd"])
            if arguments["create-staged-projects-fork-relation"]:
                projects.create_staged_projects_fork_relation(dry_run=DRY_RUN)
            if arguments["url-rewrite-only"]:
                projects.perform_url_rewrite_only(dry_run=DRY_RUN)
            if arguments["list-staged-projects-contributors"]:
                projects.list_staged_projects_contributors(dry_run=DRY_RUN)


if __name__ == "__main__":
    main()
