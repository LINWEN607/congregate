"""
    Congregate - GitLab instance migration utility

    Copyright (c) 2020 - GitLab
"""

import os
import json
from traceback import print_exc
from re import sub
from time import time
from requests.exceptions import RequestException

from congregate.helpers import api
from congregate.helpers.migrate_utils import get_export_filename_from_namespace_and_name, get_dst_path_with_namespace, get_full_path_with_parent_namespace, \
    is_top_level_group, get_failed_export_from_results, get_results, get_staged_groups_without_failed_export, get_staged_projects_without_failed_export
from congregate.helpers.misc_utils import get_dry_log, json_pretty, is_dot_com, clean_data, \
    add_post_migration_stats, rotate_logs, write_results_to_file, migration_dry_run
from congregate.helpers.processes import start_multi_process
from congregate.aws import AwsClient
from congregate.cli.stage_projects import stage_projects
from congregate.helpers.base_class import BaseClass
from congregate.migration.gitlab.importexport import ImportExportClient
from congregate.migration.gitlab.badges import BadgesClient
from congregate.migration.gitlab.variables import VariablesClient
from congregate.migration.gitlab.users import UsersClient
from congregate.migration.gitlab.api.users import UsersApi
from congregate.migration.gitlab.groups import GroupsClient
from congregate.migration.gitlab.projects import ProjectsClient
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.pushrules import PushRulesClient
from congregate.migration.gitlab.branches import BranchesClient
from congregate.migration.gitlab.merge_request_approvals import MergeRequestApprovalsClient
from congregate.migration.gitlab.registries import RegistryClient
from congregate.migration.mirror import MirrorClient
from congregate.migration.gitlab.keys import KeysClient
from congregate.migration.gitlab.hooks import HooksClient
from congregate.migration.gitlab.environments import EnvironmentsClient
from congregate.migration.bitbucket import client as bitbucket

b = BaseClass()
aws = AwsClient()
ie = ImportExportClient()
mirror = MirrorClient()
variables = VariablesClient()
badges = BadgesClient()
users = UsersClient()
users_api = UsersApi()
groups = GroupsClient()
projects = ProjectsClient()
projects_api = ProjectsApi()
pushrules = PushRulesClient()
branches = BranchesClient()
mr_approvals = MergeRequestApprovalsClient()
registries = RegistryClient()
keys = KeysClient()
hooks = HooksClient()
environments = EnvironmentsClient()

_DRY_RUN = True
_PROCESSES = None
_ONLY_POST_MIGRATION_INFO = False


def migrate(
        processes=None,
        dry_run=True,
        skip_users=False,
        skip_group_export=False,
        skip_group_import=False,
        skip_project_import=False,
        skip_project_export=False,
        only_post_migration_info=False):

    global _DRY_RUN
    _DRY_RUN = dry_run

    global _PROCESSES
    _PROCESSES = processes

    global _ONLY_POST_MIGRATION_INFO
    _ONLY_POST_MIGRATION_INFO = only_post_migration_info

    start = time()

    # TODO: Revisit and refactor accordingly
    if b.config.external_source_url:
        with open("%s" % b.config.repo_list, "r") as f:
            repo_list = json.load(f)
        start_multi_process(
            bitbucket.handle_bitbucket_migration, repo_list, processes=_PROCESSES)
    else:
        # Dry-run and log cleanup
        if _DRY_RUN:
            clean_data(dry_run=False, files=[
                "dry_run_user_migration.json",
                "dry_run_group_migration.json",
                "dry_run_project_migration.json"])
        rotate_logs()

        # Migrate users
        migrate_user_info(start, skip_users)

        # Migrate groups
        migrate_group_info(start, skip_group_export, skip_group_import)

        # Migrate projects
        migrate_project_info(start, skip_project_export, skip_project_import)

        # Migrate system hooks (except to gitlab.com)
        if is_dot_com(b.config.destination_host):
            hooks.migrate_system_hooks(dry_run=_DRY_RUN)

        # Remove import user from parent group to avoid inheritance (self-managed only)
        if not _DRY_RUN and b.config.dstn_parent_id and not is_dot_com(b.config.destination_host):
            groups.remove_import_user(b.config.dstn_parent_id)

    add_post_migration_stats(start)


def are_results(results, var, stage, start):
    if not results:
        b.log.warning(
            "Results from {0} {1} returned as empty. Aborting.".format(var, stage))
        add_post_migration_stats(start)
        exit()


def migrate_user_info(start, skip_users=False):
    staged_users = users.get_staged_users()
    if staged_users:
        if not skip_users:
            b.log.info("{}Migrating user info".format(get_dry_log(_DRY_RUN)))
            staged = users.handle_users_not_found(
                "staged_users", users.search_for_staged_users()[0], keep=False if _ONLY_POST_MIGRATION_INFO else True)
            new_users = filter(None, start_multi_process(
                handle_user_creation, staged, _PROCESSES))
            are_results(new_users, "user", "creation", start)
            formatted_users = {}
            for nu in new_users:
                formatted_users[nu["email"]] = nu
            write_results_to_file(
                formatted_users, result_type="user", log=b.log)
            if _DRY_RUN:
                b.log.info(
                    "DRY-RUN: Outputing various USER migration data to dry_run_user_migration.json")
                migration_dry_run("user", list(start_multi_process(
                    users.generate_user_data, staged_users, _PROCESSES)))
        else:
            b.log.info("SKIP: Assuming staged users are already migrated")
    else:
        b.log.info("SKIP: No users to migrate")


def handle_user_creation(user):
    """
        This is called when importing staged_users.json.
        Blocked users will be skipped if we do NOT 'keep_blocked_users'.

        :param user: Each iterable called is a user from the staged_users.json file
        :return:
    """
    response = None
    new_user = None
    state = user.get("state", None).lower()
    email = user.get("email", None)
    old_user = {
        "email": email,
        "id": user["id"]
    }
    try:
        if not _ONLY_POST_MIGRATION_INFO:
            if state == "active" or (state == "blocked" and b.config.keep_blocked_users):
                user_data = users.generate_user_data(user)
                b.log.info("{0}Attempting to create user {1}".format(
                    get_dry_log(_DRY_RUN), email))
                response = users_api.create_user(
                    b.config.destination_host, b.config.destination_token, user_data) if not _DRY_RUN else None
            else:
                b.log.info("SKIP: Not migrating {0} user:\n{1}".format(
                    state, json_pretty(user)))
            if response is not None:
                # NOTE: Persist 'blocked' user state regardless of domain and creation status.
                if user_data.get("state", None).lower() == "blocked":
                    users.block_user(user_data)
                new_user = users.handle_user_creation_status(
                    response, user_data)
        if not _DRY_RUN:
            # Migrate SSH keys
            keys.migrate_user_ssh_keys(
                old_user, new_user if new_user else users.find_user_by_email_comparison_without_id(email))
            # Migrate GPG keys
            keys.migrate_user_gpg_keys(
                old_user, new_user if new_user else users.find_user_by_email_comparison_without_id(email))
    except RequestException as e:
        b.log.error(
            "Failed to create user {0}, with error:\n{1}".format(user_data, e))
    except Exception as e:
        b.log.error(
            "Could not get response text/JSON. Error was {0}".format(e))
    return new_user


def migrate_group_info(start, skip_group_export=False, skip_group_import=False):
    staged_groups = [g for g in groups.get_staged_groups(
    ) if is_top_level_group(g)]
    dry_log = get_dry_log(_DRY_RUN)
    if staged_groups:
        if not skip_group_export:
            b.log.info("{}Exporting groups".format(dry_log))
            export_results = start_multi_process(
                handle_exporting_groups, staged_groups, processes=_PROCESSES)

            are_results(export_results, "group", "export", start)

            # Create list of groups that failed export
            failed = get_failed_export_from_results(
                export_results)
            b.log.warning("SKIP: Groups that failed to export or already exist on destination:\n{}".format(
                json_pretty(failed)))

            # Append total count of groups exported
            export_results.append(get_results(export_results))
            b.log.info("### {0}Group export results ###\n{1}"
                       .format(dry_log, json_pretty(export_results)))

            # Filter out the failed ones
            staged_groups = get_staged_groups_without_failed_export(
                staged_groups, failed)
        else:
            b.log.info("SKIP: Assuming staged groups are already exported")
        if not skip_group_import:
            b.log.info("{}Importing groups".format(dry_log))
            import_results = start_multi_process(
                handle_importing_groups, staged_groups, processes=_PROCESSES)

            are_results(import_results, "group", "import", start)

            # append Total : Successful count of groups imports
            import_results.append(get_results(import_results))
            b.log.info("### {0}Group import results ###\n{1}"
                       .format(dry_log, json_pretty(import_results)))
            write_results_to_file(
                import_results, result_type="group", log=b.log)

            # Migrate sub-group info
            staged_subgroups = [g for g in groups.get_staged_groups(
            ) if not is_top_level_group(g)]
            if staged_subgroups:
                start_multi_process(migrate_subgroup_info,
                                    staged_subgroups, processes=_PROCESSES)
        else:
            b.log.info("SKIP: Assuming staged groups will be later imported")
    else:
        b.log.info("SKIP: No groups to migrate")


def handle_exporting_groups(group):
    full_path = group["full_path"]
    gid = group["id"]
    dry_log = get_dry_log(_DRY_RUN)
    filename = get_export_filename_from_namespace_and_name(
        full_path)
    result = {
        filename: False
    }
    try:
        b.log.info("{0}Exporting group {1} (ID: {2}) as {3}"
                   .format(dry_log, full_path, gid, filename))
        result[filename] = ie.export_group(
            gid, full_path, filename, dry_run=_DRY_RUN)
    except (IOError, RequestException) as oe:
        b.log.error("Failed to export group {0} (ID: {1}) as {2} with error:\n{3}".format(
            full_path, gid, filename, oe))
    except Exception as e:
        b.log.error(e)
        b.log.error(print_exc())
    return result


def handle_importing_groups(group):
    full_path = group["full_path"]
    src_gid = group["id"]
    full_path_with_parent_namespace = get_full_path_with_parent_namespace(
        full_path)
    filename = get_export_filename_from_namespace_and_name(
        full_path)
    result = {
        full_path_with_parent_namespace: False
    }
    import_id = None
    try:
        if isinstance(group, str):
            group = json.loads(group)
        b.log.info("Searching on destination for group {}".format(
            full_path_with_parent_namespace))
        dst_grp = groups.find_group_by_path(
            b.config.destination_host, b.config.destination_token, full_path_with_parent_namespace)
        dst_gid = dst_grp.get("id", None) if dst_grp else None
        if dst_gid:
            b.log.info("{0}Group {1} (ID: {2}) already exists on destination".format(
                get_dry_log(_DRY_RUN), full_path, dst_gid))
            result[full_path_with_parent_namespace] = dst_gid
            if _ONLY_POST_MIGRATION_INFO and not _DRY_RUN:
                import_id = dst_gid
                group = dst_grp
            else:
                result[full_path_with_parent_namespace] = dst_gid
        else:
            b.log.info("{0}Group {1} NOT found on destination, importing..."
                       .format(get_dry_log(_DRY_RUN), full_path_with_parent_namespace))
            ie.import_group(
                group, full_path_with_parent_namespace, filename, dry_run=_DRY_RUN)
            # In place of checking the import status
            if not _DRY_RUN:
                group = ie.wait_for_group_import(
                    full_path_with_parent_namespace)
                import_id = group.get("id", None)
        if import_id and not _DRY_RUN:
            result[full_path_with_parent_namespace] = group
            # Migrate CI/CD Variables
            variables.migrate_variables(
                import_id, src_gid, "group", full_path)
            # Remove import user
            groups.remove_import_user(import_id)
    except (RequestException, KeyError, OverflowError) as oe:
        b.log.error("Failed to import group {0} (ID: {1}) as {2} with error:\n{3}".format(
            full_path, src_gid, filename, oe))
    except Exception as e:
        b.log.error(e)
        b.log.error(print_exc())
    return result


def migrate_subgroup_info(subgroup):
    full_path = subgroup["full_path"]
    src_gid = subgroup["id"]
    full_path_with_parent_namespace = get_full_path_with_parent_namespace(
        full_path)
    try:
        if isinstance(subgroup, str):
            subgroup = json.loads(subgroup)
        b.log.info("Searching on destination for sub-group {}".format(
            full_path_with_parent_namespace))
        dst_gid = groups.find_group_id_by_path(
            b.config.destination_host, b.config.destination_token, full_path_with_parent_namespace)
        if dst_gid:
            b.log.info("{0}Sub-group {1} (ID: {2}) found on destination".format(
                get_dry_log(_DRY_RUN), full_path, dst_gid))
            if not _DRY_RUN:
                # Migrate CI/CD Variables
                variables.migrate_variables(
                    dst_gid, src_gid, "group", full_path)
                # Remove import user
                groups.remove_import_user(dst_gid)
        else:
            b.log.info("{0}Sub-group {1} NOT found on destination".format(
                get_dry_log(_DRY_RUN), full_path_with_parent_namespace))
    except (RequestException, KeyError, OverflowError) as oe:
        b.log.error(
            "Failed to migrate sub-group {0} (ID: {1}) info with error:\n{2}".format(full_path, src_gid, oe))
    except Exception as e:
        b.log.error(e)
        b.log.error(print_exc())


def migrate_project_info(start, skip_project_export=False, skip_project_import=False):
    staged_projects = projects.get_staged_projects()
    dry_log = get_dry_log(_DRY_RUN)
    if staged_projects:
        if not skip_project_export:
            b.log.info("{}Exporting projects".format(dry_log))
            export_results = start_multi_process(
                handle_exporting_projects, staged_projects, processes=_PROCESSES)

            are_results(export_results, "project", "export", start)

            # Create list of projects that failed export
            failed = get_failed_export_from_results(
                export_results)
            b.log.warning("SKIP: Projects that failed to export or already exist on destination:\n{}".format(
                json_pretty(failed)))

            # Append total count of projects exported
            export_results.append(get_results(export_results))
            b.log.info("### {0}Project export results ###\n{1}"
                       .format(dry_log, json_pretty(export_results)))

            # Filter out the failed ones
            staged_projects = get_staged_projects_without_failed_export(
                staged_projects, failed)
        else:
            b.log.info("SKIP: Assuming staged projects are already exported")

        if not skip_project_import:
            b.log.info("{}Importing projects".format(dry_log))
            import_results = start_multi_process(
                handle_importing_projects, staged_projects, processes=_PROCESSES)

            are_results(import_results, "project", "import", start)

            # append Total : Successful count of project imports
            import_results.append(get_results(import_results))
            b.log.info("### {0}Project import results ###\n{1}"
                       .format(dry_log, json_pretty(import_results)))
            write_results_to_file(import_results, log=b.log)
        else:
            b.log.info("SKIP: Assuming staged projects will be later imported")
    else:
        b.log.info("SKIP: No projects to migrate")


def handle_exporting_projects(project):
    name = project["name"]
    namespace = project["namespace"]
    pid = project["id"]
    dry_log = get_dry_log(_DRY_RUN)
    filename = get_export_filename_from_namespace_and_name(
        namespace, name)
    result = {
        filename: False
    }
    try:
        b.log.info("{0}Exporting project {1} (ID: {2}) as {3}"
                   .format(dry_log, project["path_with_namespace"], pid, filename))
        result[filename] = ie.export_project(project, dry_run=_DRY_RUN)
    except (IOError, RequestException) as oe:
        b.log.error("Failed to export project {0} (ID: {1}) as {2} with error:\n{3}".format(
            name, pid, filename, oe))
    except Exception as e:
        b.log.error(e)
        b.log.error(print_exc())
    return result


def handle_importing_projects(project_json):
    src_id = project_json["id"]
    archived = project_json["archived"]
    path = project_json["path_with_namespace"]
    dst_path_with_namespace = get_dst_path_with_namespace(
        project_json)
    result = {
        dst_path_with_namespace: False
    }
    import_id = None
    try:
        if isinstance(project_json, str):
            project_json = json.loads(project_json)
        dst_pid = projects.find_project_by_path(
            b.config.destination_host, b.config.destination_token, dst_path_with_namespace)
        if dst_pid:
            import_status = projects_api.get_project_import_status(
                b.config.destination_host, b.config.destination_token, dst_pid).json()
            b.log.info("Project {0} (ID: {1}) found on destination, with import status: {2}".format(
                dst_path_with_namespace, dst_pid, import_status))
            if _ONLY_POST_MIGRATION_INFO and not _DRY_RUN:
                import_id = dst_pid
            else:
                result[dst_path_with_namespace] = dst_pid
        else:
            b.log.info("{0}Project {1} NOT found on destination, importing...".format(
                get_dry_log(_DRY_RUN), dst_path_with_namespace))
            import_id = ie.import_project(project_json, dry_run=_DRY_RUN)

        if import_id and not _DRY_RUN:
            # Archived projects cannot be migrated
            if archived:
                b.log.info(
                    "Unarchiving source project {0} (ID: {1})".format(path, src_id))
                projects.projects_api.unarchive_project(
                    b.config.source_host, b.config.source_token, src_id)
            b.log.info(
                "Migrating source project {0} (ID: {1}) info".format(path, src_id))
            post_import_results = migrate_single_project_info(
                project_json, import_id)
            result[dst_path_with_namespace] = post_import_results
    except (RequestException, KeyError, OverflowError) as oe:
        b.log.error("Failed to import project {0} (ID: {1}) with error:\n{2}".format(
            path, src_id, oe))
    except Exception as e:
        b.log.error(e)
        b.log.error(print_exc())
    finally:
        if archived and not _DRY_RUN:
            b.log.info(
                "Archiving back source project {0} (ID: {1})".format(path, src_id))
            projects.projects_api.archive_project(
                b.config.source_host, b.config.source_token, src_id)
    return result


def migrate_single_project_info(project, dst_id):
    """
        Subsequent function to update project info AFTER import
    """
    project.pop("members")
    path_with_namespace = project["path_with_namespace"]
    shared_with_groups = project["shared_with_groups"]
    src_id = project["id"]
    results = {}

    results["id"] = dst_id

    # Shared with groups
    results["shared_with_groups"] = projects.add_shared_groups(
        dst_id, path_with_namespace, shared_with_groups)

    # Environments
    results["environments"] = environments.migrate_project_environments(
        src_id, dst_id, path_with_namespace)

    # CI/CD Variables
    results["variables"] = variables.migrate_cicd_variables(
        src_id, dst_id, path_with_namespace)

    # Push Rules
    results["push_rules"] = pushrules.migrate_push_rules(
        src_id, dst_id, path_with_namespace)

    # Merge Request Approvals
    results["project_level_mr_approvals"] = mr_approvals.migrate_project_level_mr_approvals(
        src_id, dst_id, path_with_namespace)

    # Deploy Keys
    results["deploy_keys"] = keys.migrate_project_deploy_keys(
        src_id, dst_id, path_with_namespace)

    # Container Registries
    if b.config.source_registry and b.config.destination_registry:
        results["container_registry"] = registries.migrate_registries(
            src_id, dst_id, path_with_namespace)

    # Project hooks (webhooks)
    results["project_hooks"] = hooks.migrate_project_hooks(
        src_id, dst_id, path_with_namespace)

    projects.remove_import_user(dst_id)

    return results


def rollback(dry_run=True,
             skip_users=False,
             hard_delete=False,
             skip_groups=False,
             skip_projects=False):
    start = time()
    rotate_logs()
    dry_log = get_dry_log(dry_run)

    # Remove groups and projects OR only empty groups
    if not skip_groups:
        b.log.info("{0}Removing staged groups{1} on destination".format(
            dry_log,
            "" if skip_projects else " and projects"))
        groups.delete_groups(dry_run=dry_run, skip_projects=skip_projects)

    # Remove only projects
    if not skip_projects:
        b.log.info("{}Removing staged projects on destination".format(dry_log))
        projects.delete_projects(dry_run=dry_run)

    if not skip_users:
        b.log.info("{0}Removing staged users on destination (hard_delete={1})".format(
            dry_log,
            hard_delete))
        users.delete_users(dry_run=dry_run, hard_delete=hard_delete)

    add_post_migration_stats(start)


def remove_all_mirrors(dry_run=True):
    # if os.path.isfile("%s/data/new_ids.txt" % b.app_path):
    #     ids = []
    #     with open("%s/data/new_ids.txt" % b.app_path, "r") as f:
    #         for line in f:
    #             ids.append(int(line.split("\n")[0]))
    # else:
    ids = get_new_ids()
    for i in ids:
        mirror.remove_mirror(i, dry_run)


def get_new_ids():
    ids = []
    staged_projects = projects.get_staged_projects()
    if staged_projects:
        for project_json in staged_projects:
            try:
                b.log.debug("Searching for existing %s" % project_json["name"])
                for proj in projects.projects_api.search_for_project(b.config.destination_host,
                                                                     b.config.destination_token,
                                                                     project_json['name']):
                    if proj["name"] == project_json["name"]:

                        if "%s" % project_json["namespace"].lower(
                        ) in proj["path_with_namespace"].lower():
                            if project_json["namespace"].lower(
                            ) == proj["namespace"]["name"].lower():
                                b.log.debug("Adding {0}/{1}".format(
                                    project_json["namespace"], project_json["name"]))
                                # b.log.info("Migrating variables for %s" % proj["name"])
                                ids.append(proj["id"])
                                break
            except IOError as e:
                b.log.error(e)
        return ids


def mirror_staged_projects(dry_run=True):
    ids = get_new_ids()
    staged_projects = projects.get_staged_projects()
    if staged_projects:
        for i in enumerate(staged_projects):
            pid = ids[i]
            project = staged_projects[i]
            mirror.mirror_repo(project, pid, dry_run)


def check_visibility():
    count = 0
    if os.path.isfile("%s/data/new_ids.txt" % b.app_path):
        ids = []
        with open("%s/data/new_ids.txt" % b.app_path, "r") as f:
            for line in f:
                ids.append(int(line.split("\n")[0]))
    else:
        ids = get_new_ids()
    for i in ids:
        project = projects.projects_api.get_project(
            i, b.config.destination_host, b.config.destination_token).json()
        if project["visibility"] != "private":
            b.log.debug("Current destination path {0} visibility: {1}".format(
                project["path_with_namespace"], project["visibility"]))
            count += 1
            data = {
                "visibility": "private"
            }
            change = api.generate_put_request(
                b.config.destination_host, b.config.destination_token, "projects/%d?visibility=private" % int(
                    i),
                data=None)
            print change
    print count


def update_diverging_branch():
    for project in api.list_all(
            b.config.destination_host, b.config.destination_token, "projects"):
        if project.get("mirror_overwrites_diverged_branches", None) != True:
            id = project["id"]
            name = project["name"]
            b.log.debug(
                "Setting mirror_overwrites_diverged_branches to true for project {}".format(name))
            resp = api.generate_put_request(b.config.destination_host, b.config.destination_token,
                                            "projects/%d?mirror_overwrites_diverged_branches=true" % id, data=None)
            b.log.debug("Project {0} mirror_overwrites_diverged_branches status: {1}".format(
                name, resp.status_code))


def get_total_migrated_count():
    # group_projects = api.get_count(
    # b.config.destination_host, b.config.destination_token,
    # "groups/%d/projects" % b.config.dstn_parent_id)
    subgroup_count = 0
    for group in api.list_all(b.config.destination_host, b.config.destination_token,
                              "groups/%d/subgroups" % b.config.dstn_parent_id):
        count = api.get_count(
            b.config.destination_host, b.config.destination_token, "groups/%d/projects" % group["id"])
        sub_count = 0
        if group.get("child_ids", None) is not None:
            for child_id in group["child_ids"]:
                sub_count += api.get_count(b.config.destination_host,
                                           b.config.destination_token, "groups/%d/projects" % child_id)
        subgroup_count += count
    # return subgroup_count + group_projects
    return subgroup_count


def dedupe_imports():
    with open("%s/data/unimported_projects.txt" % b.app_path, "r") as f:
        unimported_projects = f.read()
    unimported_projects = unimported_projects.split("\n")
    dedupe = set(unimported_projects)
    print len(dedupe)


def stage_unimported_projects(dry_run=True):
    ids = []
    with open("{}/data/unimported_projects.txt".format(b.app_path), "r") as f:
        unimported_projects = f.read()
    available_projects = projects.get_projects()
    rewritten_projects = {}
    for i in enumerate(available_projects):
        new_obj = available_projects[i]
        id_num = available_projects[i]["path"]
        rewritten_projects[id_num] = new_obj

    unimported_projects = unimported_projects.split("\n")
    for up in unimported_projects:
        if up is not None and up:
            if rewritten_projects.get(up.split("/")[1], None) is not None:
                ids.append(rewritten_projects.get(up.split("/")[1])["id"])
    if ids is not None and ids:
        stage_projects(ids, dry_run)


def generate_instance_map():
    for project in api.list_all(
            b.config.destination_host, b.config.destination_token, "projects"):
        if project.get("import_url", None) is not None:
            import_url = sub('//.+:.+@', '//', project["import_url"])
            with open("new_repomap.txt", "ab") as f:
                f.write("%s\t%s\n" % (import_url, project["id"]))
