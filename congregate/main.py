"""Congregate - GitLab instance migration utility 

Copyright (c) 2018 - GitLab

Usage:
    congregate list
    congregate config
    congregate stage <projects>...
    congregate migrate [--threads=<n>] [--dry-run] [--skip-users]
    congregate ui
    congregate import-projects
    congregate do_all
    congregate update-staged-user-info
    congregate update-new-users
    congregate update-aws-creds
    congregate add-users-to-parent-group
    congregate remove-blocked-users
    congregate update-user-permissions [--access-level=<level>]
    congregate get-total-count
    congregate find-unimported-projects
    congregate stage-unimported-projects
    congregate remove-users-from-parent-group
    congregate migrate-variables-in-stage
    congregate add-all-mirrors
    congregate remove-all-mirrors
    congregate find-all-internal-projects
    congregate make-all-internal-groups-private
    congregate check-projects-visibility
    congregate set-default-branch
    congregate enable_mirroring
    congregate count-unarchived-projects
    congregate archive-staged-projects [--dry-run]
    congregate unarchive-staged-projects [--dry-run]
    congregate find-empty-repos
    congregate compare-groups [--staged]
    congregate staged-user-list
    congregate generate-seed-data
    congregate map-new-users-to-groups-and-projects [--dry-run]
    congregate validate-staged-groups-schema
    congregate validate-staged-projects-schema
    congregate map-users
    congregate -h | --help

Options:
    -h, --help                              Show Usage.

Arguments:
    threads                                 Set number of threads to run in parallel.
    dry-run                                 Perform local listing of metadata that would be handled during the migration.
    skip-users                              Migrate all but users (staged_users.json).
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
    ui                                      Deploy UI to port 8000.
    import-projects                         Kick off import of exported projects onto destination instance.
    do_all                                  Configure system, retrieve all projects, users, and groups, stage all information, and commence migration.
    update-staged-user-info                 Update staged user information after migrating only users.
    update-new-users                        Update user IDs in staged groups and projects after migrating only users.
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

just_configured = False

if not os.path.isfile("%s/data/config.json" % app_path):
    configure.config()
    just_configured = True
    config = conf.ig()
else:
    config = conf.ig()

if __name__ == '__main__':
    arguments = docopt(__doc__)
    if arguments["config"]:
        if not just_configured:
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
            # except ImportError:
            #     import migration.users, migration.groups, migration.projects
            from congregate.cli import list_projects, stage_projects, do_all
        if config.external_source != False and config.external_source is not None:
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
            if arguments["list"]:
                list_projects.list_projects()
            if arguments["stage"]:
                stage_projects.stage_projects(arguments['<projects>'])
            if arguments["migrate"]:
                threads = None
                skip_users = False
                if arguments["--threads"]:
                    threads = arguments["--threads"]
                if arguments["--skip-users"]:
                    skip_users = True
                if not arguments["--dry-run"]:
                    migrate.migrate(threads=threads, skip_users=skip_users)
                else:
                    users.user_migration_dry_run()
            if arguments["do_all"]:
                do_all.do_all()
            if arguments["ui"]:
                # os.environ["FLASK_APP"] = "%s/congregate/ui" % app_path
                os.chdir(app_path + "/congregate")
                # os.environ["PYTHONPATH"] = app_path
                run_ui = "gunicorn -k gevent -w 4 ui:app --bind=0.0.0.0:8000"
                subprocess.call(run_ui.split(" "))
            if arguments["update-staged-user-info"]:
                users.update_staged_user_info()
            if arguments["update-new-users"]:
                users.update_new_users()
            if arguments["add-users-to-parent-group"]:
                users.add_users_to_parent_group()
            if arguments["update-aws-creds"]:
                command = "aws configure set aws_access_key_id {}".format(config.s3_access_key)
                subprocess.call(command.split(" "))
                log.info("Configured AWS access key")
                command = "aws configure set aws_secret_access_key {}".format(config.s3_secret_key)
                subprocess.call(command.split(" "))
                log.info("Configured AWS secret key")
            if arguments["remove-blocked-users"]:
                users.remove_blocked_users()
            if arguments["update-user-permissions"]:
                if arguments["--access-level"]:
                    access_level = arguments["--access-level"]
                    users.update_user_permissions(access_level=access_level)
                else:
                    log.warn("Missing access-level argument")
            if arguments["import-projects"]:
                migrate.kick_off_import()
            if arguments["get-total-count"]:
                print migrate.get_total_migrated_count()
            if arguments["find-unimported-projects"]:
                migrate.find_unimported_projects()
            if arguments["stage-unimported-projects"]:
                migrate.stage_unimported_projects()
            if arguments["remove-users-from-parent-group"]:
                users.remove_users_from_parent_group()
            if arguments["migrate-variables-in-stage"]:
                variables.migrate_variables_in_stage()
            if arguments["remove-all-mirrors"]:
                migrate.remove_all_mirrors()
            if arguments["find-all-internal-projects"]:
                groups.find_all_internal_projects()
            if arguments["make-all-internal-groups-private"]:
                groups.make_all_internal_groups_private()
            if arguments["check-projects-visibility"]:
                migrate.check_visibility()
            if arguments["add-all-mirrors"]:
                migrate.enable_mirror()
            if arguments["set-default-branch"]:
                migrate.set_default_branch()
            if arguments["count-unarchived-projects"]:
                migrate.count_unarchived_projects()
            if arguments["archive-staged-projects"]:
                migrate.archive_staged_projects(True) if arguments["--dry-run"] else migrate.archive_staged_projects()
            if arguments["unarchive-staged-projects"]:
                migrate.unarchive_staged_projects(True) if arguments["--dry-run"] else migrate.unarchive_staged_projects()
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
                users.map_new_users_to_groups_and_projects(True) if arguments["--dry-run"] else users.map_new_users_to_groups_and_projects()
            if arguments["validate-staged-groups-schema"]:
                groups.validate_staged_groups_schema()
            if arguments["validate-staged-projects-schema"]:
                projects.validate_staged_projects_schema()
            if arguments["map-users"]:
                map_users()
