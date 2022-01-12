"""Congregate - GitLab instance migration utility

Copyright (c) 2021 - GitLab

Usage:
    congregate init
    congregate list [--processes=<n>] [--partial] [--skip-users] [--skip-groups] [--skip-projects] [--skip-ci] [--src-instances]
    congregate configure
    congregate generate-reporting
    congregate stage-projects <projects>... [--skip-users] [--commit] [--scm-source=hostname]
    congregate stage-groups <groups>... [--skip-users] [--commit] [--scm-source=hostname]
    congregate stage-wave <wave> [--commit] [--scm-source=hostname]
    congregate create-stage-wave-csv [--commit]
    congregate migrate [--processes=<n>] [--reporting] [--skip-users] [--remove-members] [--skip-group-export] [--skip-group-import] [--skip-project-export] [--skip-project-import] [--only-post-migration-info] [--subgroups-only] [--scm-source=hostname] [--commit] [--reg-dry-run]
    congregate rollback [--hard-delete] [--skip-users] [--skip-groups] [--skip-projects] [--commit]
    congregate ui
    congregate do-all [--commit]
    congregate do-all-users [--commit]
    congregate do-all-groups-and-projects [--commit]
    congregate search-for-staged-users [--table]
    congregate update-aws-creds
    congregate add-users-to-parent-group [--commit]
    congregate remove-inactive-users [--commit] [--membership]
    congregate update-user-permissions [--access-level=<level>] [--commit]
    congregate get-total-count
    # TODO: Refactor, project name matching does not seem correct
    congregate find-unimported-projects [--commit]
    congregate stage-unimported-projects [--commit] # TODO: Refactor, broken
    congregate url-rewrite-only [--commit]
    congregate remove-users-from-parent-group [--commit]
    congregate migrate-variables-in-stage [--commit]
    congregate mirror-staged-projects [--commit]
    congregate push-mirror-staged-projects [--disabled] [--overwrite] [--force] [--commit]
    congregate toggle-staged-projects-push-mirror [--disable] [--commit]
    congregate verify-staged-projects-remote-mirror
    congregate remove-all-mirrors [--commit]
    # TODO: Add dry-run, potentially remove
    congregate update-projects-visibility
    congregate set-default-branch [--name=<name>] [--commit]
    congregate enable-mirroring [--commit] # TODO: Find a use for it or remove
    congregate count-unarchived-projects [--local]
    congregate archive-staged-projects [--commit] [--dest] [--scm-source=hostname]
    congregate unarchive-staged-projects [--commit] [--dest] [--scm-source=hostname]
    congregate filter-projects-by-state [--commit] [--archived]
    congregate find-empty-repos
    congregate compare-groups [--staged]
    congregate staged-user-list
    congregate generate-seed-data [--commit] # TODO: Refactor, broken
    congregate validate-staged-groups-schema
    congregate validate-staged-projects-schema
    congregate map-users [--commit]
    congregate map-and-stage-users-by-email-match [--commit]
    congregate generate-diff [--processes=<n>] [--staged] [--rollback] [--scm-source=hostname] [--skip-users] [--skip-groups] [--skip-projects] [--subgroups-only]
    congregate clean [--commit]
    congregate stitch-results [--result-type=<project|group|user>] [--no-of-files=<n>] [--head|--tail]
    congregate obfuscate
    congregate deobfuscate
    congregate dump-database
    congregate reingest <assets>...
    congregate clean-database [--commit] [--keys]
    congregate toggle-maintenance-mode [--commit] [--off] [--dest] [--msg=<multi+word+message>]
    congregate ldap-group-sync <file-path> [--commit]
    congregate set-staged-users-public-email [--commit] [--hide]
    congregate create-staged-projects-structure [--commit] [--disable-cicd]
    congregate create-staged-projects-fork-relation [--commit]
    congregate -h | --help
    congregate -v | --version

Options:
    -h, --help                              Show Usage.
    -v, --version                           Show current version of congregate.

Arguments:
    processes                               Set number of processes to run in parallel.
    commit                                  Disable the dry-run and perform the full migration with all reads/writes.
    src_instances                           Present if there are multiple GH source instances
    scm_source                              Specific SCM source hostname
    skip-users                              Stage: Skip staging users; Migrate: Skip migrating users; Rollback: Remove only groups and projects.
    remove-members                          Remove all members of created (GitHub) or imported (GitLab) groups. Skip adding any members of BitBucket imported repos.
    hard-delete                             Remove user contributions and solely owned groups
    skip-groups                             Rollback: Remove only users and projects
    skip-group-export                       Skip exporting groups from source instance
    skip-group-import                       Skip importing groups to destination instance
    skip-projects                           Rollback: Remove only users and empty groups
    skip-project-export                     Skips the project export and assumes that the project file is already ready
                                                for rewrite. Currently does NOT work for exports through filesystem-aws
    skip-project-import                     Will do all steps up to import (export, re-write exported project json,
                                                etc). Useful for testing export contents. Will also skip any external source imports
    skip-ci                                 Skip migrating data from CI sources
    only-post-migration-info                Skips migrating all content except for post-migration information. Use when import is handled outside of congregate
    subgroups-only                          Expects that only sub-groups are staged and that their parent groups already exist on destination
    reg-dry-run                             If registry migration is configured, instead of doing the actual migration, write the tags to the logs for use in the brute force migration. Can also be useful when renaming targets
    access-level                            Update parent group level user permissions (Guest/Reporter/Developer/Maintainer/Owner).
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
    overwrite                               Disable keep_divergent_refs (True by default) and overwrite mirror repo on next push
    force                                   Immediately trigger push mirroring with a repo change e.g. new branch
    name                                    Project branch name

Commands:
    list                                    List all projects of a source instance and save it to {CONGREGATE_PATH}/data/projects.json.
    init                                    Creates additional directories and files required by congregate
    configure                               Configure congregate for migrating between two instances and save it to {CONGREGATE_PATH}/data/congregate.conf.
    generate-reporting                                  Run reporting on staged projects.
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
    stage-wave                              Stage wave of projects based on migration wave spreadsheet. This only takes a single wave for input
    create-stage-wave-csv                   Generate a baseline version of the CSV for stage wave from the listed data
    migrate                                 Commence migration based on configuration and staged assets.
    rollback                                Remove staged users/groups/projects on destination.
    ui                                      Deploy UI to port 8000.
    do-all*                                 Configure system, retrieve all projects, users, and groups, stage all information, and commence migration.
    search-for-staged-users                 Search for staged users on destination based on primary email
    update-aws-creds                        Run awscli commands based on the keys stored in the config. Useful for docker updates.
    add-users-to-parent-group               If a parent group is set, all staged users will be added to the parent group with guest permissions.
    remove-inactive-users                   Remove all inactive users from staged projects and groups.
    update-user-permissions                 Update parent group member access level. Mainly for lowering to Guest/Reporter.
    get-total-count                         Get total count of migrated projects. Used to compare exported projects to imported projects.
    find-unimported-projects                Return a list of projects that failed import.
    stage-unimported-projects               Stage unimported projects based on {CONGREGATE_PATH}/data/unimported_projects.txt.
    url-rewrite-only                        Performs the URL rewrite portion of a migration as a stand-alone step, instead of as a post-migration step. Requires the projects to be staged, and to exist on destination
    remove-users-from-parent-group          Remove all users with at most reporter access from the parent group.
    migrate-variables-in-stage              Migrate CI variables for staged projects.
    mirror-staged-projects                  Set up project mirroring for staged projects.
    push-mirror-staged-projects             Set up and enable (by default) project push mirroring for staged projects.
                                                Assuming both the mirrored repo and empty project structure (create-staged-projects-structure) for mirroring already exist on destination.
                                                NOTE: Destination instance only mirroring.
    toggle-staged-projects-push-mirror      Enable/disable push mirror created via command push-mirror-staged-projects.
                                                NOTE: Destination instance only mirroring.
    verify-staged-projects-remote-mirror    Verify that each staged project remote push mirror exists and is not failing.
    remove-all-mirrors                      Remove all project mirrors for staged projects.
    update-projects-visibility              Return list of all migrated projects' visibility.
    set-default-branch                      Set default branch for staged projects on destination.
    enable-mirroring                        Start pull mirror process for all projects on destination.
    count-unarchived-projects               Return total number and list of all unarchived projects on source.
    find-empty-repos                        Inspect project repo sizes between source and destination instance in search for empty repos.
                                                This could be misleading as it sometimes shows 0 (zero) commits/tags/bytes for fully migrated projects.
    compare-groups                          Compare source and destination group results.
    staged-user-list                        Output a list of all staged users and their respective user IDs. Used to confirm IDs were updated correctly.
    archive-staged-projects                 Archive projects that are staged, not necessarily migrated.
    unarchive-staged-projects               Unarchive projects that are staged, not necessarily migrate.
    filter-projects-by-state                Filter out projects by state archived or unarchived (default) from the list of staged projects and overwrite staged_projects.json.
                                                GitLab source only
    generate-seed-data                      Generate dummy data to test a migration.
    validate-staged-groups-schema           Check staged_groups.json for missing group data.
    validate-staged-projects-schema         Check staged_projects.json for missing project data.
    clean                                   Delete all retrieved and staged data
    stitch-results                          Stitches together migration results from multiple migration runs
    generate-diff                           Generates HTML files containing the diff results of the migration
    map-users                               Maps staged user emails to emails defined in the user-provided user_map.csv
    map-and-stage-users-by-email-match                Maps staged user emails to emails defined in the user-provided user_map.csv. Matches by old/new email instead of username
    obfuscate                               Obfuscate a secret or password that you want to manually update in the config.
    deobfuscate                             Deobfuscate a secret or password from the config.
    dump-database                           Dump all database collections to various JSON files
    reingest                                Reingest database dumps into mongo. Specify the asset type (users, groups, projects, teamcity, jenkins)
    clean-database                          Drop all collections in the congregate MongoDB database and rebuilds the structure
    toggle-maintenance-mode                 Reduce write operations to a minimum by blocking all external actions that change the internal state. Operational as of GitLab version 13.9
    ldap-group-sync                         Perform LDAP Group sync operations over a pipe-delimited file of group_id|CN
    set-staged-users-public-email           Set/unset the staged users public_email field on source. Mandatory for migrations from GitLab 14.0+.
    create-staged-projects-structure        Create empty project structures on GitLab destination for staged projects. Optionally, disable CI/CD on creation.
    create-staged-projects-fork-relation    Create a forked from/to relation between (group) projects on destination, based on staged projects. Assumes fork and forked project have already been migrated.
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
            sys.exit()
        DRY_RUN = not arguments["--commit"]
        STAGED = arguments["--staged"]
        ROLLBACK = arguments["--rollback"]
        PROCESSES = arguments["--processes"] or conf.Config().processes
        SKIP_USERS = arguments["--skip-users"]
        SKIP_GROUPS = arguments["--skip-groups"]
        SKIP_PROJECTS = arguments["--skip-projects"]
        REMOVE_MEMBERS = arguments["--remove-members"]
        ONLY_POST_MIGRATION_INFO = arguments["--only-post-migration-info"]
        PARTIAL = arguments["--partial"]
        SRC_INSTANCES = arguments["--src-instances"]
        SCM_SOURCE = arguments["--scm-source"]
        ARCHIVED = arguments["--archived"]
        MEMBERSHIP = arguments["--membership"]
        SUBGROUPS_ONLY = arguments["--subgroups-only"]
        REG_DRY_RUN = arguments["--reg-dry-run"]
        DEST = arguments["--dest"]

        if SCM_SOURCE:
            SCM_SOURCE = strip_netloc(SCM_SOURCE)

        from congregate.cli.config import generate_config
        from congregate.helpers.migrate_utils import clean_data, add_post_migration_stats, write_results_to_file

        if arguments["configure"]:
            generate_config()
        else:
            from gitlab_ps_utils.string_utils import convert_to_underscores
            from congregate.migration.gitlab.users import UsersClient
            from congregate.migration.gitlab.groups import GroupsClient
            from congregate.migration.gitlab.projects import ProjectsClient
            from congregate.migration.gitlab.variables import VariablesClient
            from congregate.migration.gitlab.compare import CompareClient
            from congregate.migration.migrate import MigrateClient
            from congregate.migration.gitlab.branches import BranchesClient
            from congregate.cli import list_source, do_all
            from congregate.cli.stage_projects import ProjectStageCLI
            from congregate.cli.stage_groups import GroupStageCLI
            from congregate.cli.stage_wave import WaveStageCLI
            from congregate.cli.stage_wave_csv_generator import WaveStageCSVGeneratorCLI
            from congregate.helpers.seed.generator import SeedDataGenerator
            from congregate.migration.gitlab.diff.userdiff import UserDiffClient
            from congregate.migration.gitlab.diff.projectdiff import ProjectDiffClient
            from congregate.migration.gitlab.diff.groupdiff import GroupDiffClient
            from congregate.migration.github.diff.repodiff import RepoDiffClient
            from congregate.helpers.user_util import map_users, map_and_stage_users_by_email_match
            from congregate.helpers.mdbc import MongoConnector
            from congregate.migration.github.repos import ReposClient
            from congregate.cli.ldap_group_sync import LdapGroupSync

            config = conf.Config()
            users = UsersClient()
            groups = GroupsClient()
            projects = ProjectsClient()
            variables = VariablesClient()
            compare = CompareClient()
            branches = BranchesClient()

            if not config.ssl_verify:
                log.warning(
                    "ssl_verify is set to False. Suppressing downstream SSL warnings. Consider enforcing SSL "
                    "verification in the future"
                )

            if arguments["list"]:
                start = time()
                rotate_logs()
                list_source.list_data(
                    processes=PROCESSES,
                    partial=PARTIAL,
                    skip_users=SKIP_USERS,
                    skip_groups=SKIP_GROUPS,
                    skip_projects=SKIP_PROJECTS,
                    skip_ci=arguments["--skip-ci"],
                    src_instances=SRC_INSTANCES
                )
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

            if arguments["migrate"]:
                migrate = MigrateClient(
                    processes=PROCESSES,
                    dry_run=DRY_RUN,
                    skip_users=SKIP_USERS,
                    remove_members=REMOVE_MEMBERS,
                    skip_group_export=bool(
                        arguments["--skip-group-export"] or ONLY_POST_MIGRATION_INFO),
                    skip_group_import=arguments["--skip-group-import"],
                    skip_project_export=bool(
                        arguments["--skip-project-export"] or ONLY_POST_MIGRATION_INFO),
                    skip_project_import=arguments["--skip-project-import"],
                    only_post_migration_info=ONLY_POST_MIGRATION_INFO,
                    subgroups_only=SUBGROUPS_ONLY,
                    scm_source=SCM_SOURCE,
                    reg_dry_run=REG_DRY_RUN
                )
                migrate.migrate()

            if arguments["rollback"]:
                migrate = MigrateClient(
                    dry_run=DRY_RUN,
                    skip_users=SKIP_USERS,
                    hard_delete=arguments["--hard-delete"],
                    skip_groups=SKIP_GROUPS,
                    skip_projects=SKIP_PROJECTS
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
            if arguments["add-users-to-parent-group"]:
                users.add_users_to_parent_group(dry_run=DRY_RUN)
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
            if arguments["update-user-permissions"]:
                access_level = arguments["--access-level"]
                if access_level:
                    users.update_user_permissions(
                        access_level, dry_run=DRY_RUN)
                else:
                    log.warning("Missing access-level argument")
            if arguments["get-total-count"]:
                migrate = MigrateClient()
                migrate.get_total_migrated_count()
            if arguments["find-unimported-projects"]:
                projects.find_unimported_projects(dry_run=DRY_RUN)
            if arguments["stage-unimported-projects"]:
                migrate = MigrateClient(dry_run=DRY_RUN)
                migrate.stage_unimported_projects()
            if arguments["remove-users-from-parent-group"]:
                users.remove_users_from_parent_group(dry_run=DRY_RUN)
            if arguments["migrate-variables-in-stage"]:
                variables.migrate_variables_in_stage(dry_run=DRY_RUN)
            if arguments["remove-all-mirrors"]:
                migrate = MigrateClient(dry_run=DRY_RUN)
                migrate.remove_all_mirrors()
            if arguments["update-projects-visibility"]:
                migrate = MigrateClient()
                migrate.update_visibility()
            if arguments["mirror-staged-projects"]:
                migrate = MigrateClient(dry_run=DRY_RUN)
                migrate.mirror_staged_projects()
            if arguments["push-mirror-staged-projects"]:
                projects.push_mirror_staged_projects(
                    disabled=arguments["--disabled"], overwrite=arguments["--overwrite"], force=arguments["--force"], dry_run=DRY_RUN)
            if arguments["toggle-staged-projects-push-mirror"]:
                projects.toggle_staged_projects_push_mirror(
                    disable=arguments["--disable"], dry_run=DRY_RUN)
            if arguments["verify-staged-projects-remote-mirror"]:
                projects.verify_staged_projects_remote_mirror()
            if arguments["set-default-branch"]:
                branches.set_default_branch(
                    name=arguments["--name"], dry_run=DRY_RUN)
            if arguments["count-unarchived-projects"]:
                projects.count_unarchived_projects(local=arguments["--local"])
            if arguments["archive-staged-projects"]:
                if config.source_type == "gitlab" or (
                        config.source_type == "bitbucket server" and DEST):
                    projects.update_staged_projects_archive_state(
                        dest=DEST, dry_run=DRY_RUN)
                elif config.source_type == "github" or config.list_multiple_source_config("github_source") is not None:
                    if SCM_SOURCE is not None:
                        for single_source in config.list_multiple_source_config(
                                "github_source"):
                            if SCM_SOURCE in single_source.get(
                                    "src_hostname", None):
                                gh_repos = ReposClient(single_source["src_hostname"], deobfuscate(
                                    single_source["src_access_token"]))
                    else:
                        gh_repos = ReposClient(
                            config.source_host, config.source_token)
                    gh_repos.archive_staged_repos(dry_run=DRY_RUN)
                else:
                    log.warning(
                        f"Bulk archive not available for {config.source_type}. Did you mean to add '--dest'?")
            if arguments["unarchive-staged-projects"]:
                if config.source_type == "gitlab" or (
                        config.source_type == "bitbucket server" and DEST):
                    projects.update_staged_projects_archive_state(
                        archive=False, dest=DEST, dry_run=DRY_RUN)
                else:
                    log.warning(
                        f"Bulk unarchive not available for {config.source_type}. Did you mean to add '--dest'?")
            if arguments["filter-projects-by-state"]:
                if config.source_type == "gitlab":
                    projects.filter_projects_by_state(
                        archived=ARCHIVED, dry_run=DRY_RUN)
                else:
                    log.warning(
                        f"The 'archived' field is currently not present when listing on {config.source_type}")
            if arguments["find-empty-repos"]:
                projects.find_empty_repos()
            if arguments["compare-groups"]:
                if arguments["--staged"]:
                    results, unknown_users = compare.create_group_migration_results(
                        staged=True)
                else:
                    results, unknown_users = compare.create_group_migration_results()
                with open(f"{app_path}/data/groups_audit.json", "w") as f:
                    dump(results, f, indent=4)
                with open(f"{app_path}/data/unknown_users.json", "w") as f:
                    dump(unknown_users, f, indent=4)
            if arguments["staged-user-list"]:
                results = compare.compare_staged_users()
                log.info(
                    f"Staged user list:\n{dumps(results, indent=4, sort_keys=True)}")
                log.info(
                    f"Length: {{key: len(value) for key, value in results.items()}}")
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
                            user_diff.generate_diff_report(),
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
                            group_diff.generate_diff_report(),
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
                            project_diff.generate_diff_report(),
                            "/data/results/project_migration_results.html"
                        )
                elif config.source_type == "github" or SCM_SOURCE is not None:
                    if SCM_SOURCE is not None:
                        for single_instance in config.list_multiple_source_config(
                                "github_source"):
                            if SCM_SOURCE == strip_netloc(
                                    single_instance.get('src_hostname', '')):
                                repo_diff = RepoDiffClient(
                                    single_instance['src_hostname'],
                                    deobfuscate(
                                        single_instance['src_access_token']),
                                    staged=STAGED,
                                    processes=PROCESSES,
                                    rollback=ROLLBACK,
                                )
                    else:
                        repo_diff = RepoDiffClient(
                            config.source_host,
                            config.source_token,
                            staged=STAGED,
                            processes=PROCESSES,
                            rollback=ROLLBACK
                        )
                    repo_diff.generate_diff_report()
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
                m = MongoConnector()
                for collection in m.db.list_collection_names():
                    print(f"Dumping collection {collection} to file")
                    m.dump_collection_to_file(
                        collection, f"{app_path}/data/{convert_to_underscores(collection)}.json")
            if arguments["reingest"]:
                m = MongoConnector()
                for asset in arguments["<assets>"]:
                    print(f"Reingesting {asset} into database")
                    m.re_ingest_into_mongo(asset)
            if arguments["clean-database"]:
                if not DRY_RUN:
                    m = MongoConnector()
                    m.clean_db(keys=arguments["--keys"])
                else:
                    print("\nThis command will drop all collections in the congregate database and then recreate the structure. Please append `--commit` to clean the database")
            if arguments["toggle-maintenance-mode"]:
                migrate = MigrateClient()
                migrate.toggle_maintenance_mode(
                    off=arguments["--off"],
                    msg=arguments["--msg"],
                    dest=DEST,
                    dry_run=DRY_RUN)
            if arguments["ldap-group-sync"]:
                if not DRY_RUN:
                    ldap = LdapGroupSync()
                    ldap.load_pdv(arguments['<file-path>'])
                    ldap.synchronize_groups(dry_run=DRY_RUN)
                else:
                    print(
                        "\nThis command will setup LDAP group sync based on the file passed in via <file-path>")
            if arguments["set-staged-users-public-email"]:
                users.set_staged_users_public_email(
                    dry_run=DRY_RUN, hide=arguments["--hide"])
            if arguments["create-staged-projects-structure"]:
                projects.create_staged_projects_structure(
                    dry_run=DRY_RUN, disable_cicd=arguments["--disable-cicd"])
            if arguments["create-staged-projects-fork-relation"]:
                projects.create_staged_projects_fork_relation(dry_run=DRY_RUN)
        if arguments["obfuscate"]:
            data = obfuscate("Secret:")
            if platform == "darwin":
                subprocess.run("pbcopy", universal_newlines=True,
                               input=data, check=True)
                print("Masked secret copied to clipboard (pbcopy)")
            else:
                print(f"Masked secret: {data}")
        if arguments["deobfuscate"]:
            data = deobfuscate(input("Masked secret:"))
            if platform == "darwin":
                subprocess.run("pbcopy", universal_newlines=True,
                               input=data, check=True)
                print("Secret copied to clipboard (pbcopy)")
            else:
                print(f"Secret: {data}")
        if arguments["url-rewrite-only"]:
            projects.perform_url_rewrite_only(dry_run=DRY_RUN)

if __name__ == "__main__":
    main()
