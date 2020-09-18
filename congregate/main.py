"""Congregate - GitLab instance migration utility

Copyright (c) 2020 - GitLab

Usage:
    congregate init
    congregate list
    congregate configure
    congregate stage-projects <projects>... [--skip-users] [--commit]
    congregate stage-groups <groups>... [--skip-users] [--commit]
    congregate stage-wave <wave> [--commit]
    congregate migrate [--processes=<n>] [--skip-users] [--skip-group-export] [--skip-group-import] [--skip-project-export] [--skip-project-import] [--only-post-migration-info] [--commit]
    congregate rollback [--hard-delete] [--skip-users] [--skip-groups] [--skip-projects] [--commit]
    congregate ui
    congregate do-all [--commit]
    congregate do-all-users [--commit]
    congregate do-all-groups-and-projects [--commit]
    congregate search-for-staged-users
    congregate update-aws-creds
    congregate add-users-to-parent-group [--commit]
    congregate remove-blocked-users [--commit]
    congregate update-user-permissions [--access-level=<level>] [--commit]
    congregate get-total-count
    # TODO: Refactor, project name matching does not seem correct
    congregate find-unimported-projects [--commit]
    congregate stage-unimported-projects [--commit] # TODO: Refactor, broken
    congregate remove-users-from-parent-group [--commit]
    congregate migrate-variables-in-stage [--commit]
    congregate mirror-staged-projects [--commit]
    congregate remove-all-mirrors [--commit]
    congregate find-all-non-private-groups
    # TODO: Refactor or rename, as it does not make any changes
    congregate make-all-internal-groups-private
    # TODO: Refactor or rename, as it's not a check but does an update. Add dry-run
    congregate check-projects-visibility
    congregate set-default-branch [--commit]
    congregate enable-mirroring [--commit] # TODO: Find a use for it or remove
    congregate count-unarchived-projects
    congregate archive-staged-projects [--commit]
    congregate unarchive-staged-projects [--commit]
    congregate find-empty-repos
    congregate compare-groups [--staged]
    congregate staged-user-list
    congregate generate-seed-data [--commit] # TODO: Refactor, broken
    congregate validate-staged-groups-schema
    congregate validate-staged-projects-schema
    congregate map-users [--commit]
    congregate generate-diff [--processes=<n>] [--staged] [--rollback]
    congregate clean [--commit]
    congregate stitch-results [--result-type=<project|group|user>] [--no-of-files=<n>] [--head|--tail]
    congregate obfuscate
    congregate -h | --help
    congregate -v | --version

Options:
    -h, --help                              Show Usage.
    -v, --version                           Show current version of congregate.

Arguments:
    processes                               Set number of processes to run in parallel.
    commit                                  Disable the dry-run and perform the full migration with all reads/writes.
    skip-users                              Stage: Skip staging users; Migrate: Skip migrating users; Rollback: Remove only groups and projects.
    hard-delete                             Remove user contributions and solely owned groups.
    skip-groups                             Rollback: Remove only users and projects.
    skip-group-export                       Skip exporting groups from source instance.
    skip-group-import                       Skip importing groups to destination instance.
    skip-projects                           Rollback: Remove only users and empty groups.
    skip-project-export                     Skips the project export and assumes that the project file is already ready
                                                for rewrite. Currently does NOT work for exports through filesystem-aws.
    skip-project-import                     Will do all steps up to import (export, re-write exported project json,
                                                etc). Useful for testing export contents. Will also skip any external source imports
    only-post-migration-info                Skips migrating all content except for post-migration information. Use when import is handled outside of congregate
    access-level                            Update parent group level user permissions (Guest/Reporter/Developer/Maintainer/Owner).
    staged                                  Compare using staged data
    no-of-files                             Number of files used to go back when stitching JSON results
    result-type                             For stitching result files. Options are project, group, or user
    head                                    Read results files in chronological order
    tail                                    Read results files in reverse chronological order (default for stitch-results)

Commands:
    list                                    List all projects of a source instance and save it to {CONGREGATE_PATH}/data/project_json.json.
    init                                    Creates additional directories and files required by congregate
    configure                               Configure congregate for migrating between two instances and save it to {CONGREGATE_PATH}/data/congregate.conf.
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
    migrate                                 Commence migration based on configuration and staged assets.
    rollback                                Remove staged users/groups/projects on destination.
    ui                                      Deploy UI to port 8000.
    do-all*                                 Configure system, retrieve all projects, users, and groups, stage all information, and commence migration.
    search-for-staged-users                 Search for staged users on destination based on email
    update-aws-creds                        Run awscli commands based on the keys stored in the config. Useful for docker updates.
    add-users-to-parent-group               If a parent group is set, all staged users will be added to the parent group with guest permissions.
    remove-blocked-users                    Remove all blocked users from staged projects and groups.
    update-user-permissions                 Update parent group member access level. Mainly for lowering to Guest/Reporter.
    get-total-count                         Get total count of migrated projects. Used to compare exported projects to imported projects.
    find-unimported-projects                Return a list of projects that failed import.
    stage-unimported-projects               Stage unimported projects based on {CONGREGATE_PATH}/data/unimported_projects.txt.
    remove-users-from-parent-group          Remove all users with at most reporter access from the parent group.
    migrate-variables-in-stage              Migrate CI variables for staged projects.
    mirror-staged-projects                  Set up project mirroring for staged projects.
    remove-all-mirrors                      Remove all project mirrors for staged projects.
    find-all-non-private-groups             Return list of all groups on destination that are either internal or public.
    make-all-internal-groups-private        Make all internal migrated groups private.
    check-projects-visibility               Return list of all migrated projects' visibility.
    set-default-branch                      Set default branch to master for all projects on destination.
    enable-mirroring                        Start pull mirror process for all projects on destination.
    count-unarchived-projects               Return total number and list of all anarchived projects on source.
    find-empty-repos                        Inspect project repo sizes between source and destination instance in search for empty repos.
                                                This could be misleading as it sometimes shows 0 (zero) commits/tags/bytes for fully migrated projects.
    compare-groups                          Compare source and destination group results.
    staged-user-list                        Output a list of all staged users and their respective user IDs. Used to confirm IDs were updated correctly.
    archive-staged-projects                 Archive projects that are staged, not necessarily migrated.
    unarchive-staged-projects               Unarchive projects that are staged, not necessarily migrate.
    generate-seed-data                      Generate dummy data to test a migration.
    validate-staged-groups-schema           Check staged_groups.json for missing group data.
    validate-staged-projects-schema         Check staged_projects.json for missing project data.
    clean                                   Delete all retrieved and staged data
    stitch-results                          Stitches together migration results from multiple migration runs
    generate-diff                           Generates HTML files containing the diff results of the migration
    map-users                               Maps staged user emails to emails defined in the user-provided user_map.csv
    obfuscate                               Obfuscate a secret or password that you want to manually update in the config.
"""

import os
import subprocess
from toml import load as load_toml
from json import dump, dumps
from docopt import docopt

if __name__ == '__main__':
    if __package__ is None:
        import sys
        sys.path.append(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))))
    from congregate.helpers import conf
    from congregate.helpers.logger import myLogger
    from congregate.helpers.misc_utils import get_congregate_path, clean_data, obfuscate, spin_up_ui, stitch_json_results, write_results_to_file
else:
    import sys
    sys.path.append(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))
    from congregate.helpers import conf
    from congregate.helpers.logger import myLogger
    from congregate.helpers.misc_utils import get_congregate_path, clean_data, obfuscate, stitch_json_results, write_results_to_file, spin_up_ui

app_path = get_congregate_path()


def main():
    if __name__ == '__main__':
        arguments = docopt(__doc__)
        DRY_RUN = False if arguments["--commit"] else True
        STAGED = True if arguments["--staged"] else False
        ROLLBACK = True if arguments["--rollback"] else False
        PROCESSES = arguments["--processes"] if arguments["--processes"] else None
        SKIP_USERS = True if arguments["--skip-users"] else False
        ONLY_POST_MIGRATION_INFO = True if arguments["--only-post-migration-info"] else False

        if arguments["--version"]:
            with open(f"{app_path}/pyproject.toml", "r") as f:
                print(f"Congregate {load_toml(f)['tool']['poetry']['version']}")
            exit()

        if arguments["init"]:
            if not os.path.exists('data'):
                print("Creating data directory and empty log file")
                os.makedirs('data')
                if not os.path.exists("%s/data/congregate.log" % app_path):
                    with open("%s/data/congregate.log" % app_path, "w") as f:
                        f.write("")
            else:
                print("Congregate already initialized")
            log = myLogger(__name__)
        else:
            log = myLogger(__name__)

        from congregate.cli.config import generate_config

        if arguments["configure"]:
            generate_config()
        else:
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
            from congregate.helpers.seed.generator import SeedDataGenerator
            from congregate.migration.gitlab.diff.userdiff import UserDiffClient
            from congregate.migration.gitlab.diff.projectdiff import ProjectDiffClient
            from congregate.migration.gitlab.diff.groupdiff import GroupDiffClient
            from congregate.helpers.user_util import map_users
            config = conf.Config()
            users = UsersClient()
            groups = GroupsClient()
            projects = ProjectsClient()
            variables = VariablesClient()
            compare = CompareClient()
            branches = BranchesClient()

            if arguments["list"]:
                list_source.list_data()

            if arguments["stage-projects"]:
                pcli = ProjectStageCLI()
                pcli.stage_data(arguments['<projects>'],
                                dry_run=DRY_RUN, skip_users=SKIP_USERS)

            if arguments["stage-groups"]:
                gcli = GroupStageCLI()
                gcli.stage_data(arguments['<groups>'],
                                dry_run=DRY_RUN, skip_users=SKIP_USERS)

            if arguments["stage-wave"]:
                wcli = WaveStageCLI()
                wcli.stage_wave(
                    arguments['<wave>'], dry_run=DRY_RUN)

            if arguments["migrate"]:
                migrate = MigrateClient(
                    processes=PROCESSES,
                    dry_run=DRY_RUN,
                    skip_users=SKIP_USERS,
                    skip_group_export=True if arguments["--skip-group-export"] or ONLY_POST_MIGRATION_INFO else False,
                    skip_group_import=True if arguments["--skip-group-import"] else False,
                    skip_project_export=True if arguments["--skip-project-export"] or ONLY_POST_MIGRATION_INFO else False,
                    skip_project_import=True if arguments["--skip-project-import"] else False,
                    only_post_migration_info=ONLY_POST_MIGRATION_INFO
                )
                migrate.migrate()

            if arguments["rollback"]:
                migrate = MigrateClient(
                    dry_run=DRY_RUN,
                    skip_users=SKIP_USERS,
                    hard_delete=True if arguments["--hard-delete"] else False,
                    skip_groups=True if arguments["--skip-groups"] else False,
                    skip_projects=True if arguments["--skip-projects"] else False
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
                users.search_for_staged_users()
            if arguments["add-users-to-parent-group"]:
                users.add_users_to_parent_group(dry_run=DRY_RUN)
            if arguments["update-aws-creds"]:
                if config.s3_access_key and config.s3_secret_key:
                    command = "aws configure set aws_access_key_id {}".format(
                        config.s3_access_key)
                    subprocess.call(command.split(" "))
                    command = "aws configure set aws_secret_access_key {}".format(
                        config.s3_secret_key)
                    subprocess.call(command.split(" "))
                    log.info(
                        "Configured local AWS access and secret keys (~/.aws/credentials)")
                else:
                    log.warning("No AWS configuration. Export location: {}".format(
                        config.location))
            if arguments["remove-blocked-users"]:
                users.remove_blocked_users(dry_run=DRY_RUN)
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
            if arguments["find-all-non-private-groups"]:
                groups.find_all_non_private_groups()
            if arguments["make-all-internal-groups-private"]:
                groups.make_all_internal_groups_private()
            if arguments["check-projects-visibility"]:
                migrate = MigrateClient()
                migrate.check_visibility()
            if arguments["mirror-staged-projects"]:
                migrate = MigrateClient(dry_run=DRY_RUN)
                migrate.mirror_staged_projects()
            if arguments["set-default-branch"]:
                branches.set_default_branches_to_master(dry_run=DRY_RUN)
            if arguments["count-unarchived-projects"]:
                projects.count_unarchived_projects()
            if arguments["archive-staged-projects"]:
                projects.archive_staged_projects(dry_run=DRY_RUN)
            if arguments["unarchive-staged-projects"]:
                projects.unarchive_staged_projects(dry_run=DRY_RUN)
            if arguments["find-empty-repos"]:
                projects.find_empty_repos()
            if arguments["compare-groups"]:
                if arguments["--staged"]:
                    results, unknown_users = compare.create_group_migration_results(
                        staged=True)
                else:
                    results, unknown_users = compare.create_group_migration_results()
                with open("%s/data/groups_audit.json" % app_path, "w") as f:
                    dump(results, f, indent=4)
                with open("%s/data/unknown_users.json" % app_path, "w") as f:
                    dump(unknown_users, f, indent=4)
            if arguments["staged-user-list"]:
                results = compare.compare_staged_users()
                log.info("Staged user list:\n{}".format(
                    dumps(results, indent=4, sort_keys=True)))
                log.info("Length: {}".format({key: len(value)
                                              for key, value in results.items()}))
            if arguments["generate-seed-data"]:
                s = SeedDataGenerator()
                s.generate_seed_data(dry_run=DRY_RUN)
            if arguments["validate-staged-groups-schema"]:
                groups.validate_staged_groups_schema()
            if arguments["validate-staged-projects-schema"]:
                projects.validate_staged_projects_schema()
            if arguments["map-users"]:
                map_users(dry_run=DRY_RUN)
            if arguments["clean"]:
                clean_data(dry_run=DRY_RUN)
            if arguments["generate-diff"]:
                user_diff = UserDiffClient(
                    "/data/user_migration_results.json", staged=STAGED, processes=PROCESSES, rollback=ROLLBACK)
                user_diff.generate_html_report(
                    user_diff.generate_diff_report(), "/data/user_migration_results.html")
                group_diff = GroupDiffClient(
                    "/data/group_migration_results.json", staged=STAGED, processes=PROCESSES, rollback=ROLLBACK)
                group_diff.generate_html_report(
                    group_diff.generate_diff_report(), "/data/group_migration_results.html")
                project_diff = ProjectDiffClient(
                    "/data/project_migration_results.json", staged=STAGED, processes=PROCESSES, rollback=ROLLBACK)
                project_diff.generate_html_report(
                    project_diff.generate_diff_report(), "/data/project_migration_results.html")
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
        if arguments["obfuscate"]:
            print(obfuscate("Secret:"))


if __name__ == "__main__":
    main()
