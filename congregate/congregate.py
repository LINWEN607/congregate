"""Congregate - GitLab instance migration utility 

Copyright (c) 2018 - GitLab

Usage:
    congregate list
    congregate config
    congregate stage <projects>...
    congregate migrate [--threads=<n>]
    congregate ui
    congregate import-projects
    congregate do_all
    congregate update-staged-user-info
    congregate update-new-users
    congregate add-users-to-parent-group
    congregate remove-blocked-users
    congregate lower-user-permissions
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
    congregate find-empty-repos
    congregate -h | --help

Options:
    -h --help     Show this screen.

Commands:
    list                                List all projects of a child instance and save it to {CONGREGATE_PATH}/data/project_json.json
    config                              Configure congregate for migrating between two instances and save it to {CONGREGATE_PATH}/data/config.json
    stage                               Stage projects to {CONGREGATE_PATH}/data/stage.json,
                                        users to {CONGREGATE_PATH}/data/staged_users.json,
                                        groups to {CONGREGATE_PATH}/data/staged_groups.json.
                                        All projects can be staged with a '.' or 'all'.
    migrate                             mmence migration based on configuration and staged assets
    ui                                  Deploy UI to port 8000
    import-projects                     Kick off import of exported projects onto parent instance
    do_all                              Configure system, retrieve all projects, users, and groups, stage all information, and commence migration
    update-staged-user-info             Update staged user information after migrating only users
    update-new-users                    Update user IDs in staged groups and projects after migrating users
    add-users-to-parent-group           If a parent group is set, all users staged will be added to the parent group
    remove-blocked-users                Removes all blocked users from staged projects and groups
    lower-user-permissions              Sets all reporter users to guest users
    get-total-count                     Get total count of migrated projects. Used to compare exported projects to imported projects.
    find-unimported-projects            Returns a list of projects that failed import
    stage-unimported-projects           Stage unimported projects based on {CONGREGATE_PATH}/data/unimported_projects.txt
    remove-users-from-parent-group      Remove all users with at most reporter access from the parent group
    migrate-variables-in-stage          Migrate CI variables for staged projects
    add-all-mirrors                     Sets up project mirroring for staged projects
    remove-all-mirrors                  Remove all project mirrors for staged projects
    find-all-internal-projects          Finds all internal projects
    make-all-internal-groups-private    Makes all internal migrated groups private
    check-projects-visibility           Returns list of all migrated projects' visibility
"""

import os, subprocess
from helpers import conf
from helpers import logger as log
from cli import config as configure

app_path = os.getenv("CONGREGATE_PATH")

l = log.congregate_logger(__name__)

just_configured = False

if not os.path.isfile("%s/data/config.json" % app_path):
    configure.config()
    just_configured = True
    config = conf.ig()
else:
    config = conf.ig()

from docopt import docopt

if __name__ == '__main__':
    arguments = docopt(__doc__)
    if arguments["config"]:
        if just_configured == False:
                configure.config()
    else:
        # try:
            # from migration import users, groups, projects
        from migration.gitlab.users import UsersClient
        from migration.gitlab.groups import GroupsClient
        from migration.gitlab.projects import ProjectsClient
        from migration.gitlab.variables import VariablesClient
        from migration.mirror import MirrorClient
        from migration import migrate
        # except ImportError:
        #     import migration.users, migration.groups, migration.projects
        from cli import list_projects, stage_projects, do_all
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
                run_ui = "gunicorn -k gevent -w 4 ui:app --bind=0.0.0.0:8005"
                subprocess.call(run_ui.split(" "))
            elif arguments["enable_mirroring"]:
                mirror = MirrorClient()
                mirror.enable_mirroring()
            else:
                print "External migration only currently supports the migrate and ui commands to generate shell projects with mirrors."
        else:
            users = UsersClient()
            groups = GroupsClient()
            projects = ProjectsClient()
            variables = VariablesClient()
            if arguments["list"]:
                list_projects.list_projects()
            if arguments["stage"]:
                stage_projects.stage_projects(arguments['<projects>'])
            if arguments["migrate"]:
                if arguments["--threads"]:
                    migrate.migrate(threads=arguments["--threads"])
                else:
                    migrate.migrate()
            if arguments["do_all"]:
                do_all.do_all()
            if arguments["ui"]:
                # os.environ["FLASK_APP"] = "%s/congregate/ui" % app_path
                os.chdir(app_path + "/congregate")
                # os.environ["PYTHONPATH"] = app_path
                run_ui = "gunicorn -k gevent -w 4 ui:app --bind=0.0.0.0:8005"
                subprocess.call(run_ui.split(" "))
            if arguments["update-staged-user-info"]:
                users.update_user_after_migration()
            if arguments["update-new-users"]:
                users.update_user_info_separately()
            if arguments["add-users-to-parent-group"]:
                users.add_users_to_parent_group()
            if arguments["remove-blocked-users"]:
                users.remove_blocked_users()
            if arguments["lower-user-permissions"]:
                users.lower_user_permissions()
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
            if arguments["find-empty-repos"]:
                migrate.find_empty_repos()
        
        