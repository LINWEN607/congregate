"""
    Congregate - GitLab instance migration utility

    Copyright (c) 2020 - GitLab
"""

import os
import json
import traceback
from re import sub
from collections import Counter
from requests.exceptions import RequestException

from congregate.helpers import api, migrate_utils
from congregate.helpers.misc_utils import get_dry_log, json_pretty, write_json_to_file, \
    is_dot_com, clean_data, add_post_migration_stats, rotate_log
from congregate.helpers.threads import start_multi_process
from congregate.aws import AwsClient
from congregate.cli.stage_projects import stage_projects
from congregate.helpers.base_class import BaseClass
from congregate.migration.gitlab.importexport import ImportExportClient
from congregate.migration.gitlab.badges import BadgesClient
from congregate.migration.gitlab.variables import VariablesClient
from congregate.migration.gitlab.users import UsersClient
from congregate.migration.gitlab.groups import GroupsClient
from congregate.migration.gitlab.projects import ProjectsClient
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.pushrules import PushRulesClient
from congregate.migration.gitlab.branches import BranchesClient
from congregate.migration.gitlab.merge_request_approvals import MergeRequestApprovalsClient
from congregate.migration.gitlab.registries import RegistryClient
from congregate.migration.mirror import MirrorClient
from congregate.migration.gitlab.deploy_keys import DeployKeysClient
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
groups = GroupsClient()
projects = ProjectsClient()
projects_api = ProjectsApi()
pushrules = PushRulesClient()
branches = BranchesClient()
mr_approvals = MergeRequestApprovalsClient()
registries = RegistryClient()
deploy_keys = DeployKeysClient()
hooks = HooksClient()
environments = EnvironmentsClient()

full_parent_namespace = groups.find_parent_group_path()
_DRY_RUN = True
_THREADS = None


def migrate(
        threads=None,
        dry_run=True,
        skip_users=False,
        skip_group_export=False,
        skip_group_import=False,
        skip_project_import=False,
        skip_project_export=False):

    global _DRY_RUN
    _DRY_RUN = dry_run

    global _THREADS
    _THREADS = threads

    # TODO: Revisit and refactor accordingly
    if b.config.external_source_url:
        with open("%s" % b.config.repo_list, "r") as f:
            repo_list = json.load(f)
        start_multi_process(
            bitbucket.handle_bitbucket_migration, repo_list, threads=_THREADS)
    else:
        # Dry-run and log cleanup
        if dry_run:
            clean_data(dry_run=False, files=[
                "dry_run_user_migration.json",
                "dry_run_group_migration.json",
                "dry_run_project_migration.json"])
        rotate_log()

        # Migrate users
        # TODO: Replace threading with multiprocessing
        if not skip_users:
            users.migrate_user_info(dry_run=_DRY_RUN, threads=_THREADS)

        # Migrate groups
        migrate_group_info(skip_group_export, skip_group_import)

        # Migrate projects
        migrate_project_info(skip_project_export, skip_project_import)

        # Migrate system hooks (except for gitlab.com)
        if is_dot_com(b.config.destination_host):
            hooks.migrate_system_hooks()

        add_post_migration_stats()


def are_results(results, var, stage):
    if not results:
        raise Exception(
            "Results from {0} {1} returned as empty. Aborting.".format(var, stage))


def is_loc_supported(loc):
    if loc not in ["filesystem", "aws"]:
        raise Exception("Unsupported export location: {}".format(loc))


def migrate_group_info(skip_group_export=False, skip_group_import=False):
    staged_groups = groups.get_staged_groups()
    dry_log = get_dry_log(_DRY_RUN)
    if staged_groups:
        if not skip_group_export:
            b.log.info("{}Exporting groups".format(dry_log))
            export_results = start_multi_process(
                handle_exporting_groups, staged_groups, threads=_THREADS)

            are_results(export_results, "group", "export")

            # Append total count of groups exported
            export_results.append(
                Counter(k for d in export_results for k, v in d.items() if v))
            b.log.info("### {0}Group export results ###\n{1}"
                       .format(dry_log, json_pretty(export_results)))

            # Create list of groups that failed export
            failed = migrate_utils.get_failed_export_from_results(
                export_results)
            b.log.warning("The following groups (group.json) failed to export and will not be imported:\n{0}"
                          .format(json_pretty(failed)))

            # Filter out the failed ones
            staged_groups = migrate_utils.get_staged_groups_without_failed_export(
                staged_groups, failed)
        else:
            b.log.info("SKIP: Assuming staged groups are already exported")
        if not skip_group_import:
            b.log.info("{}Importing groups".format(dry_log))
            import_results = start_multi_process(
                handle_importing_groups, staged_groups, threads=_THREADS)

            are_results(import_results, "group", "import")

            # append Total : Successful count of groups imports
            import_results.append({
                "group import results": {
                    "Total": len(import_results),
                    "Successful": sum([len(import_results[x]) for x in xrange(len(import_results)) if isinstance(import_results[x][import_results[x].keys()[0]], dict)])
                }
            })
            b.log.info("### {0}Group import results ###\n{1}"
                       .format(dry_log, json_pretty(import_results)))
            migrate_utils.write_results_to_file(import_results, result_type="group")
        else:
            b.log.info("SKIP: Assuming staged groups will be later imported")
    else:
        b.log.info("SKIP: No groups to migrate")


def handle_exporting_groups(group):
    full_path = group["full_path"]
    gid = group["id"]
    loc = b.config.location.lower()
    dry_log = get_dry_log(_DRY_RUN)
    try:
        is_loc_supported(loc)
        filename = migrate_utils.get_export_filename_from_namespace_and_name(
            full_path)
        exported = False
        b.log.info("{0}Exporting group {1} (ID: {2}) as {3}"
                   .format(dry_log, full_path, gid, filename))
        if loc == "filesystem":
            exported = ie.export_group_thru_filesystem(
                gid, full_path, full_parent_namespace, filename) if not _DRY_RUN else True
        # TODO: Refactor and sync with other scenarios (#119)
        elif loc == "filesystem-aws":
            b.log.error(
                "NOTICE: Filesystem-AWS exports are not currently supported")
        # NOTE: Group export does not yet support AWS (S3) user attributes
        elif loc == "aws":
            b.log.error(
                "NOTICE: AWS group exports are not currently supported")
        return {"filename": filename, "exported": exported}
    except (IOError, RequestException) as e:
        b.log.error("Failed to export group {0} (ID: {1}) to {2} with error:\n{3}".format(
            full_path, gid, loc, e))
    except Exception as e:
        b.log.error(e)
        b.log.error(traceback.print_exc)


def handle_importing_groups(group):
    full_path = group["full_path"]
    src_gid = group["id"]
    results = {
        full_path: False
    }
    try:
        if isinstance(group, str):
            group = json.loads(group)
        full_path_with_parent_namespace = "{0}{1}".format(
            full_parent_namespace + "/" if full_parent_namespace else "", full_path)
        b.log.info("Searching on destination for group {}".format(
            full_path_with_parent_namespace))
        filename = migrate_utils.get_export_filename_from_namespace_and_name(
            full_path)
        dst_gid = groups.find_group_by_path(
            b.config.destination_host, b.config.destination_token, full_path_with_parent_namespace)
        if dst_gid:
            b.log.info("{0}Group {1} (ID: {2}) already exists on destination".format(
                get_dry_log(_DRY_RUN), full_path, dst_gid))
        else:
            b.log.info("{0}Group {1} NOT found on destination, importing..."
                       .format(get_dry_log(_DRY_RUN), full_path_with_parent_namespace))
            ie.import_group(
                group, full_path_with_parent_namespace, filename, dry_run=_DRY_RUN)
            # In place of checking the import status
            if not _DRY_RUN:
                results[full_path] = ie.wait_for_group_import(
                    full_path_with_parent_namespace)
                if results[full_path] and results[full_path].get("id", None):
                    # Migrate CI/CD Variables
                    variables.migrate_variables(
                        results[full_path]["id"], src_gid, "group", full_path)
                    # Remove import user
                    groups.remove_import_user(results[full_path]["id"])
    except RequestException, e:
        b.log.error(e)
    except KeyError as e:
        b.log.error(e)
        raise KeyError("Something broke in handle_importing_groups group {0} (ID: {1})".format(
            full_path, src_gid))
    except OverflowError as e:
        b.log.error(e)
    except Exception as e:
        b.log.error(e)
        b.log.error(traceback.print_exc)
    return results


def migrate_project_info(skip_project_export=False, skip_project_import=False):
    staged_projects = projects.get_staged_projects()
    dry_log = get_dry_log(_DRY_RUN)
    if staged_projects:
        if not skip_project_export:
            b.log.info("{}Exporting projects".format(dry_log))
            export_results = start_multi_process(
                handle_exporting_projects, staged_projects, threads=_THREADS)

            are_results(export_results, "project", "export")

            # Append total count of projects exported
            export_results.append(
                Counter(k for d in export_results for k, v in d.items() if v))
            b.log.info("### {0}Project export results ###\n{1}"
                       .format(dry_log, json_pretty(export_results)))

            # Create list of projects that failed export
            failed = migrate_utils.get_failed_export_from_results(
                export_results)
            b.log.warning("The following projects (project.json) failed to export and will not be imported:\n{0}"
                          .format(json_pretty(failed)))

            # Filter out the failed ones
            staged_projects = migrate_utils.get_staged_projects_without_failed_export(
                staged_projects, failed)
        else:
            b.log.info("SKIP: Assuming staged projects are already exported")

        if not skip_project_import:
            b.log.info("{}Importing projects".format(dry_log))
            import_results = start_multi_process(
                handle_importing_projects, staged_projects, threads=_THREADS)

            are_results(import_results, "project", "import")

            # append Total : Successful count of project imports
            import_results.append({
                "project import results": {
                    "Total": len(import_results),
                    "Successful": sum([len(import_results[x]) for x in xrange(len(import_results)) if isinstance(import_results[x][import_results[x].keys()[0]], dict)])
                }
            })
            b.log.info("### {0}Project import results ###\n{1}"
                       .format(dry_log, json_pretty(import_results)))
            migrate_utils.write_results_to_file(import_results)
        else:
            b.log.info("SKIP: Assuming staged projects will be later imported")
    else:
        b.log.info("SKIP: No projects to migrate")





def handle_exporting_projects(project):
    name = project["name"]
    namespace = project["namespace"]
    pid = project["id"]
    loc = b.config.location.lower()
    dry_log = get_dry_log(_DRY_RUN)
    try:
        is_loc_supported(loc)
        filename = migrate_utils.get_export_filename_from_namespace_and_name(
            namespace, name)
        exported = False
        b.log.info("{0}Exporting project {1} (ID: {2}) as {3}"
                   .format(dry_log, project["path_with_namespace"], pid, filename))
        if loc == "filesystem":
            exported = ie.export_project_thru_filesystem(
                pid, name, namespace) if not _DRY_RUN else True
        # TODO: Refactor and sync with other scenarios (#119)
        elif loc == "filesystem-aws":
            b.log.error(
                "NOTICE: Filesystem-AWS exports are not currently supported")
            # exported = ie.export_thru_fs_aws(pid, name, namespace) if not dry_run else True
        elif loc == "aws":
            exported = ie.export_project_thru_aws(
                project) if not _DRY_RUN else True
        return {"filename": filename, "exported": exported}
    except (IOError, RequestException) as e:
        b.log.error("Failed to export project (ID: {0}) to {1} with error:\n{2}"
                    .format(pid, loc, e))
    except Exception as e:
        b.log.error(e)
        b.log.error(traceback.print_exc)


def handle_importing_projects(project_json):
    src_id = project_json["id"]
    archived = project_json["archived"]
    path = project_json["path_with_namespace"]
    project_id = None
    results = {
        path: False
    }
    try:
        if isinstance(project_json, str):
            project_json = json.loads(project_json)
        dst_path_with_namespace = migrate_utils.get_dst_path_with_namespace(
            project_json)
        b.log.info("Searching on destination for project {}".format(
            dst_path_with_namespace))
        dst_pid = projects.find_project_by_path(
            b.config.destination_host, b.config.destination_token, dst_path_with_namespace)
        if dst_pid:
            import_status = projects_api.get_project_import_status(
                b.config.destination_host, b.config.destination_token, dst_pid).json()
            b.log.info("Project {0} (ID: {1}) found on destination, with import status: {2}".format(
                dst_path_with_namespace, dst_pid, import_status))
        else:
            b.log.info("{0}Project {1} (ID: {2}) NOT found on destination, importing..."
                       .format(get_dry_log(_DRY_RUN), dst_path_with_namespace, project_id))
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
                results[path] = post_import_results
    except RequestException as e:
        b.log.error(e)
    except KeyError as e:
        b.log.error(e)
        raise KeyError("Something broke in handle_importing_projects project {0} (ID: {1})"
                       .format(path, src_id))
    except OverflowError as e:
        b.log.error(e)
    except Exception as e:
        b.log.error(e)
        b.log.error(traceback.print_exc)
    finally:
        if archived and not _DRY_RUN:
            b.log.info(
                "Archiving back source project {0} (ID: {1})".format(path, src_id))
            projects.projects_api.archive_project(
                b.config.source_host, b.config.source_token, src_id)
    return results


def migrate_single_project_info(project, dst_id):
    """
        Subsequent function to update project info AFTER import
    """
    project.pop("members")
    path_with_namespace = project["path_with_namespace"]
    src_id = project["id"]
    results = {}

    results["id"] = dst_id

    # Shared with groups
    projects.add_shared_groups(src_id, dst_id)

    # CI/CD Variables
    results["variables"] = variables.migrate_cicd_variables(
        src_id, dst_id, path_with_namespace)

    # Push Rules
    results["push_rules"] = pushrules.migrate_push_rules(
        src_id, dst_id, path_with_namespace)

    # Merge Request Approvals
    results["project_level_mr_approvals"] = mr_approvals.migrate_project_level_mr_approvals(
        src_id, dst_id, path_with_namespace)

    # Deploy Keys (project only)
    results["deploy_keys"] = deploy_keys.migrate_deploy_keys(
        src_id, dst_id, path_with_namespace)

    # Container Registries
    results["container_registry"] = registries.migrate_registries(
        src_id, dst_id, path_with_namespace)

    # Environments
    results["environments"] = environments.migrate_project_environments(
        src_id, dst_id, path_with_namespace)

    # Project hooks (webhooks)
    results["project_hooks"] = hooks.migrate_project_hooks(
        src_id, dst_id, path_with_namespace)

    projects.remove_import_user(dst_id)

    return results


# TODO: Add multiprocessing
def rollback(dry_run=True,
             skip_users=False,
             hard_delete=False,
             skip_groups=False,
             skip_projects=False):
    rotate_log()
    dry_log = get_dry_log(dry_run)

    # Remove only projects
    if not skip_projects:
        b.log.info("{}Removing projects on destination".format(dry_log))
        projects.delete_projects(dry_run=dry_run)

    # Remove groups and projects OR only empty groups
    if not skip_groups:
        b.log.info("{0}Removing groups{1} on destination".format(
            dry_log,
            "" if skip_projects else " and projects"))
        groups.delete_groups(dry_run=dry_run, skip_projects=skip_projects)

    if not skip_users:
        b.log.info("{0}Removing staged users on destination (hard_delete={1})".format(
            dry_log,
            hard_delete))
        users.delete_users(dry_run=dry_run, hard_delete=hard_delete)

    add_post_migration_stats()


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
    # "groups/%d/projects" % b.config.parent_id)
    subgroup_count = 0
    for group in api.list_all(b.config.destination_host, b.config.destination_token,
                              "groups/%d/subgroups" % b.config.parent_id):
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
