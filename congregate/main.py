"""Congregate - GitLab instance migration utility 

Copyright (c) 2018 - GitLab

Usage:
    congregate list
    congregate config
    congregate stage <projects>...
    congregate migrate [--threads=<n>] [--skip-users] [--skip-project-import] [--skip-project-export] [--commit]
    congregate cleanup [--hard-delete] [--skip-users] [--skip-groups] [--skip-projects] [--commit]
    congregate ui
    congregate export-projects
    congregate import-projects [--commit]
    congregate do_all [--commit]
    congregate update-staged-user-info [--commit]
    congregate update-aws-creds
    congregate add-users-to-parent-group [--commit]
    congregate remove-blocked-users [--commit]
    congregate update-user-permissions [--access-level=<level>] [--commit]
    congregate get-total-count
    congregate find-unimported-projects
    congregate stage-unimported-projects
    congregate remove-users-from-parent-group [--commit]
    congregate migrate-variables-in-stage [--commit]
    congregate add-all-mirrors [--commit]
    congregate remove-all-mirrors [--commit]
    congregate find-all-internal-projects
    congregate make-all-internal-groups-private
    congregate check-projects-visibility
    congregate set-default-branch
    congregate enable_mirroring
    congregate count-unarchived-projects
    congregate archive-staged-projects [--commit]
    congregate unarchive-staged-projects [--commit]
    congregate find-empty-repos
    congregate compare-groups [--staged]
    congregate staged-user-list
    congregate generate-seed-data
    congregate map-new-users-to-groups-and-projects [--commit]
    congregate validate-staged-groups-schema
    congregate validate-staged-projects-schema
    congregate map-users
    congregate -h | --help

Options:
    -h, --help                              Show Usage.

Arguments:
    threads                                 Set number of threads to run in parallel.
    commit                                  Disable the dry-run and perform the full migration with all reads/writes. 
    skip-users                              Include groups and projects.
    hard-delete                             Remove user contributions and solely owned groups.
    skip-groups                             Include users and projects.
    skip-projects                           Include ONLY users (removing ONLY groups is not possible).
    skip-project-import                     Will do all steps up to import (export, re-write exported project json,
                                                etc). Useful for testing export contents.
    skip-project-export                     Skips the project export and assumes that the project file is already ready
                                                for rewrite. Currently does NOT work for exports through filesystem-aws.
    access-level                            Update parent group level user permissions (Guest/Reporter/Developer/Maintainer/Owner).
    staged                                  Compare two groups that are staged for migration.

Commands:
    list                                    List all projects of a source instance and save it to {CONGREGATE_PATH}/data/project_json.json.
    config                                  Configure congregate for migrating between two instances and save it to {CONGREGATE_PATH}/data/config.json.
    stage                                   Stage projects to {CONGREGATE_PATH}/data/stage.json,
                                                users to {CONGREGATE_PATH}/data/staged_users.json,
                                                groups to {CONGREGATE_PATH}/data/staged_groups.json.
                                                All projects can be staged with a '.' or 'all'.
    migrate                                 Commence migration based on configuration and staged assets.
    cleanup                                 Remove staged users/groups/projects on destination.
    ui                                      Deploy UI to port 8000.
    export-projects                         Export and update source instance projects. Bulk project export without user/group info.
    import-projects                         Import exported and updated projects onto destination instance. Destination user/group info required.
    do_all                                  Configure system, retrieve all projects, users, and groups, stage all information, and commence migration.
    update-staged-user-info                 Update staged user information after migrating only users.
    update-aws-creds                        Run awscli commands based on the keys stored in the config. Useful for docker updates.
    add-users-to-parent-group               If a parent group is set, all users staged will be added to the parent group.
    remove-blocked-users                    Remove all blocked users from staged projects and groups.
    update-user-permissions                 Update parent group member access level. Mainly for lowering to Guest/Reporter.
    get-total-count                         Get total count of migrated projects. Used to compare exported projects to imported projects.
    find-unimported-projects                Return a list of projects that failed import.
    stage-unimported-projects               Stage unimported projects based on {CONGREGATE_PATH}/data/unimported_projects.txt.
    remove-users-from-parent-group          Remove all users with at most reporter access from the parent group.
    migrate-variables-in-stage              Migrate CI variables for staged projects.
    add-all-mirrors                         Set up project mirroring for staged projects.
    remove-all-mirrors                      Remove all project mirrors for staged projects.
    find-all-internal-projects              Find all internal projects.
    make-all-internal-groups-private        Make all internal migrated groups private.
    check-projects-visibility               Return list of all migrated projects' visibility.
    find-empty-repos                        Inspect project repo sizes between source and destination instance in search for empty repos.
                                                This could be misleading as it sometimes shows 0 (zero) commits/tags/bytes for fully migrated projects.
    compare-groups                          Compare source and destination group results.
    staged-user-list                        Output a list of all staged users and their respective user IDs. Used to confirm IDs were updated correctly.
    archive-staged-projects                 Archive projects that are staged, not necessarily migrated.
    unarchive-staged-projects               Unarchive projects that are staged, not necessarily migrate.
    generate-seed-data                      Generate dummy data to test a migration.
    map-new-users-to-groups-and-projects    Map new_users.json to the staged_groups.json and stage.json (projects) files without making API calls.
                                                Requires that update-staged-user-info has been called, first, to create new_users.json.
    validate-staged-groups-schema           Check staged_groups.json for missing group data.
    validate-staged-projects-schema         Check stage.json for missing project data.
    map-users                               Maps staged user emails to emails defined in the user-provided user_map.csv
"""

import os
import subprocess
from json import dump, dumps
from docopt import docopt

if __name__ == '__main__':
    if __package__ is None:
        import sys

        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from congregate.helpers import conf
        from congregate.helpers.logger import myLogger
        from congregate.cli import config as configure
        from congregate.helpers.misc_utils import get_congregate_path
        from congregate.helpers.user_util import map_users
    else:
        from .helpers import conf
        from .helpers.logger import myLogger
        from .helpers.misc_utils import get_congregate_path
        from .helpers.user_util import map_users
else:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from congregate.cli import config as configure
    from congregate.helpers import conf
    from congregate.helpers.logger import myLogger

app_path = get_congregate_path()

log = myLogger(__name__)

config = conf.ig()

if __name__ == '__main__':
    arguments = docopt(__doc__)
    if arguments["config"]:
        configure.config()
    else:
        # try:
        # from migration import users, groups, projects
        if __package__ is None:
            from congregate.migration.gitlab.users import UsersClient
            from congregate.migration.gitlab.groups import GroupsClient
            from congregate.migration.gitlab.projects import ProjectsClient
            from congregate.migration.gitlab.variables import VariablesClient
            from congregate.migration.gitlab.compare import CompareClient
            from congregate.migration.mirror import MirrorClient
            from congregate.migration import migrate
            from congregate.migration.gitlab.branches import BranchesClient
            # except ImportError:
            #     import migration.users, migration.groups, migration.projects
            from congregate.cli import list_projects, stage_projects, do_all
            from congregate.helpers.seed.generator import SeedDataGenerator
        else:
            from .migration.gitlab.users import UsersClient
            from .migration.gitlab.groups import GroupsClient
            from .migration.gitlab.projects import ProjectsClient
            from .migration.gitlab.compare import CompareClient
            from .migration.mirror import MirrorClient
            from congregate.migration import migrate
            from .migration.gitlab.branches import BranchesClient
            # except ImportError:
            #     import migration.users, migration.groups, migration.projects
            from congregate.cli import list_projects, stage_projects, do_all
        if config.external_source is not None and config.external_source:
            if arguments["migrate"]:
                if arguments["--threads"]:
                    migrate.migrate(threads=arguments["--threads"])
                else:
                    migrate.migrate()
            elif arguments["ui"]:
                # os.environ["FLASK_APP"] = "%s/congregate/ui:app" % app_path
                os.chdir(app_path + "/congregate")
                # os.environ["PYTHONPATH"] = app_path
                run_ui = "gunicorn -k gevent -w 4 ui:app --bind=0.0.0.0:8000"
                subprocess.call(run_ui.split(" "))
            elif arguments["enable_mirroring"]:
                mirror = MirrorClient()
                mirror.enable_mirroring()
            # elif arguments["gather_metrics"]:
            #     other.gather_metrics()
            else:
                print "External migration only currently supports the migrate " + \
                      "and ui commands to generate shell projects with mirrors."
        else:
            users = UsersClient()
            groups = GroupsClient()
            projects = ProjectsClient()
            variables = VariablesClient()
            compare = CompareClient()
            branches = BranchesClient()
            if arguments["list"]:
                list_projects.list_projects()
            if arguments["stage"]:
                stage_projects.stage_projects(arguments['<projects>'])
            if arguments["migrate"]:
                threads = None
                dry_run=True
                skip_users = False
                skip_project_import = False
                skip_project_export = False
                if arguments["--threads"]:
                    threads = arguments["--threads"]
                if arguments["--skip-users"]:
                    skip_users = True
                if arguments["--skip-project-import"]:
                    skip_project_import = True
                if arguments["--skip-project-export"]:
                    skip_project_export = True
                if arguments["--commit"]:
                    dry_run = False
                migrate.migrate(
                    threads=threads,
                    dry_run=dry_run,
                    skip_users=skip_users,
                    skip_project_import=skip_project_import,
                    skip_project_export=skip_project_export)
            if arguments["cleanup"]:
                dry_run=True
                skip_users = False
                hard_delete = False
                skip_groups = False
                skip_projects = False
                if arguments["--commit"]:
                    dry_run = False
                if arguments["--skip-users"]:
                    skip_users = True
                if arguments["--hard-delete"]:
                    hard_delete = True
                if arguments["--skip-groups"]:
                    skip_groups = True
                if arguments["--skip-projects"]:
                    skip_projects = True
                migrate.cleanup(
                    dry_run=dry_run,
                    skip_users=skip_users,
                    hard_delete=hard_delete,
                    skip_groups=skip_groups,
                    skip_projects=skip_projects)
            if arguments["do_all"]:
                do_all.do_all(dry_run=False) if arguments["--commit"] else do_all.do_all()
            if arguments["ui"]:
                # os.environ["FLASK_APP"] = "%s/congregate/ui" % app_path
                os.chdir(app_path + "/congregate")
                # os.environ["PYTHONPATH"] = app_path
                run_ui = "gunicorn -k gevent -w 4 ui:app --bind=0.0.0.0:8000"
                subprocess.call(run_ui.split(" "))
            if arguments["update-staged-user-info"]:
                users.update_staged_user_info(dry_run=False) if arguments["--commit"] else users.update_staged_user_info()
            if arguments["add-users-to-parent-group"]:
                users.add_users_to_parent_group(dry_run=False) if arguments["--commit"] else users.add_users_to_parent_group()
            if arguments["update-aws-creds"]:
                command = "aws configure set aws_access_key_id {}".format(config.s3_access_key)
                subprocess.call(command.split(" "))
                log.info("Configured AWS access key")
                command = "aws configure set aws_secret_access_key {}".format(config.s3_secret_key)
                subprocess.call(command.split(" "))
                log.info("Configured AWS secret key")
            if arguments["remove-blocked-users"]:
                users.remove_blocked_users(dry_run=False) if arguments["--commit"] else users.remove_blocked_users()
            if arguments["update-user-permissions"]:
                access_level = arguments["--access-level"]
                if access_level:
                    if arguments["--commit"]:
                        users.update_user_permissions(access_level, dry_run=False)
                    else:
                        users.update_user_permissions(access_level)
                else:
                    log.warning("Missing access-level argument")
            if arguments["export-projects"]:
                migrate.migrate_project_info(skip_project_import=True)
            if arguments["import-projects"]:
                if arguments["--commit"]:
                    migrate.migrate_project_info(dry_run=False, skip_project_export=True)
                else:
                    migrate.migrate_project_info(skip_project_export=True)
            if arguments["get-total-count"]:
                print migrate.get_total_migrated_count()
            if arguments["find-unimported-projects"]:
                migrate.find_unimported_projects()
            if arguments["stage-unimported-projects"]:
                migrate.stage_unimported_projects()
            if arguments["remove-users-from-parent-group"]:
                users.remove_users_from_parent_group(dry_run=False) if arguments["--commit"] else users.remove_users_from_parent_group()
            if arguments["migrate-variables-in-stage"]:
                variables.migrate_variables_in_stage(dry_run=False) if arguments["--commit"] else variables.migrate_variables_in_stage()
            if arguments["remove-all-mirrors"]:
                migrate.remove_all_mirrors(dry_run=False) if arguments["--commit"] else migrate.remove_all_mirrors()
            if arguments["find-all-internal-projects"]:
                groups.find_all_internal_projects()
            if arguments["make-all-internal-groups-private"]:
                groups.make_all_internal_groups_private()
            if arguments["check-projects-visibility"]:
                migrate.check_visibility()
            if arguments["add-all-mirrors"]:
                migrate.enable_mirror(dry_run=False) if arguments["--commit"] else migrate.enable_mirror()
            if arguments["set-default-branch"]:
                branches.set_default_branches_to_master()
            if arguments["count-unarchived-projects"]:
                projects.count_unarchived_projects()
            if arguments["archive-staged-projects"]:
                projects.archive_staged_projects(dry_run=False) if arguments["--commit"] else projects.archive_staged_projects()
            if arguments["unarchive-staged-projects"]:
                projects.unarchive_staged_projects(dry_run=False) if arguments["--commit"] else projects.unarchive_staged_projects()
            if arguments["find-empty-repos"]:
                migrate.find_empty_repos()
            if arguments["compare-groups"]:
                if arguments["--staged"]:
                    results, unknown_users = compare.create_group_migration_results(staged=True)
                else:
                    results, unknown_users = compare.create_group_migration_results()
                with open("%s/data/groups_audit.json" % app_path, "w") as f:
                    dump(results, f, indent=4)
                with open("%s/data/unknown_users.json" % app_path, "w") as f:
                    dump(unknown_users, f, indent=4)
            if arguments["staged-user-list"]:
                results = compare.compare_staged_users()
                print dumps(results, indent=4)
            if arguments["generate-seed-data"]:
                s = SeedDataGenerator()
                s.generate_seed_data()
            if arguments["map-new-users-to-groups-and-projects"]:
                if arguments["--commit"]:
                    users.map_new_users_to_groups_and_projects(dry_run=False)
                else:
                    users.map_new_users_to_groups_and_projects()
            if arguments["validate-staged-groups-schema"]:
                groups.validate_staged_groups_schema()
            if arguments["validate-staged-projects-schema"]:
                projects.validate_staged_projects_schema()
            if arguments["map-users"]:
                map_users()
