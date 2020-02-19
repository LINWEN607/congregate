"""
    Congregate - GitLab instance migration utility

    Copyright (c) 2020 - GitLab
"""

import os
import json
from re import sub
from multiprocessing.dummy import Pool as ThreadPool
from multiprocessing import Lock
from collections import Counter
from requests.exceptions import RequestException
from datetime import datetime

from congregate.helpers import api, migrate_utils
from congregate.helpers.misc_utils import get_dry_log, json_pretty
from congregate.aws import AwsClient
from congregate.cli.stage_projects import stage_projects
from congregate.helpers import base_module as b
from congregate.migration.gitlab.importexport import ImportExportClient
from congregate.migration.gitlab.badges import BadgesClient
from congregate.migration.gitlab.variables import VariablesClient
from congregate.migration.gitlab.users import UsersClient
from congregate.migration.gitlab.groups import GroupsClient
from congregate.migration.gitlab.projects import ProjectsClient
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.pushrules import PushRulesClient
from congregate.migration.gitlab.branches import BranchesClient
from congregate.migration.gitlab.merge_request_approvers import MergeRequestApproversClient
from congregate.migration.gitlab.awards import AwardsClient
from congregate.migration.gitlab.registries import RegistryClient
from congregate.migration.gitlab.pipeline_schedules import PipelineSchedulesClient
from congregate.migration.gitlab.project_export import ProjectExportClient
from congregate.migration.mirror import MirrorClient
from congregate.migration.gitlab.deploy_keys import DeployKeysClient
from congregate.migration.gitlab.hooks import HooksClient
from congregate.migration.bitbucket import client as bitbucket

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
awards = AwardsClient()
mr_approvers = MergeRequestApproversClient()
awards = AwardsClient()
registries = RegistryClient()
p_schedules = PipelineSchedulesClient()
deploy_keys = DeployKeysClient()
hooks = HooksClient()
project_export = ProjectExportClient()

full_parent_namespace = groups.find_parent_group_path()


def migrate(
        threads=None,
        dry_run=True,
        skip_users=False,
        skip_groups=False,
        skip_project_import=False,
        skip_project_export=False):

    if threads is not None:
        b.config.threads = threads

    # TODO: Revisit and refactor accordingly
    if b.config.external_source_url:
        with open("%s" % b.config.repo_list, "r") as f:
            repo_list = json.load(f)
        start_multi_thead(bitbucket.handle_bitbucket_migration, repo_list)
    else:
        # Migrate users
        if not skip_users:
            migrate_user_info(dry_run)

        # Migrate system hooks
        hooks.migrate_system_hooks(dry_run)

        # Migrate groups
        if not skip_groups:
            migrate_group_info(dry_run)

        # Migrate projects
        migrate_project_info(dry_run, skip_project_export, skip_project_import)


def start_multi_thead(function, iterable):
    l = Lock()
    pool = ThreadPool(initializer=init_pool, initargs=(l,),
                      processes=b.config.threads)
    pool.map(function, iterable)
    pool.close()
    pool.join()


def init_pool(l):
    global lock
    lock = l


def migrate_user_info(dry_run=True):
    b.log.info("{}Migrating user info".format(get_dry_log(dry_run)))
    new_users = users.migrate_user_info(dry_run)

    with open("%s/data/user_migration_results.json" % b.app_path, "w") as f:
        json.dump(new_users, f, indent=4)

    # This list is of user ids from found users via email or newly created users
    # So, new_user_ids is a bit of a misnomer
    if new_users:
        with open("%s/data/new_user_ids.txt" % b.app_path, "w") as f:
            for new_user in new_users:
                f.write("%s\n" % new_user)

        # If we created or found users, do not force overwrite
        users.update_user_info(new_users)
    else:
        users.update_user_info(new_users, overwrite=False)


def migrate_group_info(dry_run=True):
    staged_groups = groups.get_staged_groups()
    if staged_groups:
        b.log.info("{}Migrating group info".format(get_dry_log(dry_run)))
        results = groups.migrate_group_info(dry_run)
        with open("%s/data/group_migration_results.json" % b.app_path, "w") as f:
            json.dump(results, f, indent=4)
    else:
        b.log.info("SKIP: No groups to migrate")


def migrate_project_info(dry_run=True, skip_project_export=False, skip_project_import=False):
    staged_projects = projects.get_staged_projects()
    dry_log = get_dry_log(dry_run)
    if staged_projects:
        if not skip_project_export:
            b.log.info("{}Exporting projects".format(dry_log))
            export_pool = ThreadPool(b.config.threads)
            export_results = export_pool.map(
                lambda project: handle_exporting_projects(
                    project,
                    dry_run),
                staged_projects)
            export_pool.close()
            export_pool.join()

            # Create list of projects that failed update
            if not export_results or len(export_results) == 0:
                raise Exception(
                    "Results from exporting projects returned as empty. Aborting.")

            # Append total count of projects exported/updated
            export_results.append(
                Counter(k for d in export_results for k, v in d.items() if v))
            b.log.info("### {0}Project export results ###\n{1}"
                       .format(dry_log, json_pretty(export_results)))

            failed_update = migrate_utils.get_failed_update_from_results(
                export_results)
            b.log.warning("The following projects (project.json) failed to update and will not be imported:\n{0}"
                          .format(json_pretty(failed_update)))

            # Filter out the failed ones
            staged_projects = migrate_utils.get_staged_projects_without_failed_update(
                staged_projects, failed_update)
        else:
            b.log.info("SKIP: Assuming staged projects are already exported")

        if not skip_project_import:
            b.log.info("{}Importing projects".format(dry_log))
            import_pool = ThreadPool(b.config.threads)
            import_results = import_pool.map(
                lambda project: migrate_given_export(
                    project,
                    dry_run),
                staged_projects)
            import_pool.close()
            import_pool.join()

            # append Total : Successful count of project imports
            import_results.append(Counter("Total : Successful: {}"
                                          .format(len(import_results)) for d in import_results for k, v in d.items() if v)
                                  or "Total : Successful: 0 : 0")
            b.log.info("### {0}Project import results ###\n{1}"
                       .format(dry_log, json_pretty(import_results)))
            end_time = str(datetime.now()).replace(" ", "_")
            file_path = "%s/data/project_results_%s.json" % (b.app_path, end_time)
            b.log.info("### Writing output to %s" % file_path)
            with open(file_path, "w") as f:
                json.dump(import_results, f)
        else:
            b.log.info("SKIP: Assuming staged projects will be later imported")
    else:
        b.log.info("SKIP: No projects to migrate")


def handle_exporting_projects(project, dry_run=True):
    name = project["name"]
    pid = project["id"]
    loc = b.config.location.lower()
    dry_log = get_dry_log(dry_run)
    try:
        namespace = migrate_utils.get_project_namespace(project)
        filename = ie.get_export_filename_from_namespace_and_name(
            namespace, name)
        if loc not in ["filesystem", "aws"]:
            raise Exception("Unsupported export location: {}".format(loc))
        exported = False
        b.log.info("{0}Exporting project {1} (ID: {2}) as {3}"
                   .format(dry_log, name, pid, filename))
        if loc == "filesystem":
            exported = ie.export_thru_filesystem(
                pid, name, namespace) if not dry_run else True
        # TODO: Refactor and sync with other scenarios (#119)
        elif loc == "filesystem-aws":
            b.log.error(
                "NOTICE: Filesystem-AWS exports are not currently supported")
            # exported = ie.export_thru_fs_aws(pid, name, namespace) if not dry_run else True
        elif loc == "aws":
            exported = ie.export_project_thru_aws(
                pid, name, namespace, full_parent_namespace) if not dry_run else True
        updated = False
        if exported:
            b.log.info("{0}Updating project {1} (ID: {2}) export members in {3}"
                       .format(dry_log, name, pid, filename))
            if loc == "filesystem":
                updated = project_export.update_project_export_members_for_local(
                    name, namespace, filename) if not dry_run else True
            # TODO: Refactor and sync with other scenarios (#119)
            elif loc == "filesystem-aws":
                b.log.error(
                    "NOTICE: Filesystem-AWS exports are not currently supported")
            elif loc == "aws":
                updated = project_export.update_project_export_members(
                    name, namespace, filename) if not dry_run else True
        return {"filename": filename, "exported": exported, "updated": updated}
    except (IOError, RequestException) as e:
        b.log.error("Failed to export project (ID: {0}) to {1} and update members with error:\n{2}"
                    .format(pid, loc, e))


def migrate_given_export(project_json, dry_run=True):
    name = project_json["name"]
    namespace = project_json["namespace"]
    source_id = project_json["id"]
    archived = project_json["archived"]
    path = "{0}/{1}".format(namespace, name)
    project_exists = False
    project_id = None
    results = {
        path: False
    }
    if isinstance(project_json, str):
        project_json = json.loads(project_json)
    b.log.info("Searching on destination for project {}".format(path))
    try:
        project_exists, project_id = projects.find_project_by_path(
            b.config.destination_host,
            b.config.destination_token,
            full_parent_namespace,
            namespace,
            name)
        if project_id:
            import_check = ie.get_import_status(
                b.config.destination_host,
                b.config.destination_token,
                project_id).json()
            b.log.info("Project {0} (ID: {1}) found on destination, with import status: {2}".format(
                name,
                project_id,
                import_check["import_status"] if import_check is not None
                and import_check.get("import_status", None) is not None
                else import_check)
            )
        if not project_exists:
            b.log.info("{0}Project {1} (ID: {2}) not found on destination, importing..."
                       .format(get_dry_log(dry_run), path, project_id))
            import_id = ie.import_project(project_json, dry_run)
            if import_id and not dry_run:
                # Archived projects cannot be migrated
                if archived:
                    b.log.info(
                        "Unarchiving source project {0} (ID: {1})".format(name, source_id))
                    projects.projects_api.unarchive_project(
                        b.config.source_host, b.config.source_token, source_id)
                b.log.info(
                    "Migrating source project {0} (ID: {1}) info".format(name, source_id))
                post_import_results = migrate_single_project_info(
                    project_json, import_id)
                results[path] = post_import_results
    except RequestException, e:
        b.log.error(e)
    except KeyError, e:
        b.log.error(e)
        raise KeyError("Something broke in migrate_given_export project {0} (ID: {1})"
                       .format(name, source_id))
    except OverflowError, e:
        b.log.error(e)
    finally:
        if archived and not dry_run:
            b.log.info(
                "Archiving back source project {0} (ID: {1})".format(name, source_id))
            projects.projects_api.archive_project(
                b.config.source_host, b.config.source_token, source_id)
    return results


def migrate_single_project_info(project, new_id):
    """
        Subsequent function to update project info AFTER import
    """
    members = project["members"]
    project.pop("members")
    name = project["name"]
    old_id = project["id"]
    results = {}

    b.log.info("Searching for project %s" % name)
    if new_id is None:
        _, new_id = projects.find_project_by_path(
            b.config.destination_host,
            b.config.destination_token,
            full_parent_namespace,
            project["namespace"],
            project["name"])

    # Project Members
    # NOTE: Members should be handled on import. If that is not the case, the line below and variable members should be uncommented.
    # TODO: Remove the `add_members` function once the import API can consistently add project members
    # projects.add_members(members, new_id)

    projects.remove_import_user_from_project(new_id)

    # Project Avatar
    # This assumes you have access to the host systems uploads as a URL instead of letting the
    # TODO: Remove the `migrate_avatar` function once the import API can consistently add project avatars
    # projects.migrate_avatar(new_id, old_id)

    # Shared with groups
    projects.add_shared_groups(old_id, new_id)

    # Update project badges to use destination path hostname
    results["badges"] = badges.update_project_badges(
        new_id, name, full_parent_namespace)

    # CI/CD Variables
    results["variables"] = variables.migrate_cicd_variables(
        old_id, new_id, name)

    # Push Rules
    results["push_rules"] = pushrules.migrate_push_rules(old_id, new_id, name)

    # Merge Request Approvers
    results["merge_request_approvers"] = mr_approvers.migrate_mr_approvers(
        old_id, new_id, name)
    mr_enabled = bool(results["merge_request_approvers"])

    # Default Branch
    results["default_branch"] = branches.update_default_branch(
        old_id, new_id, project)

    # Protected Branches
    results["protected_branches"] = branches.migrate_protected_branches(
        old_id, new_id, name)

    # Awards
    users_map = {}
    results["awards"] = awards.migrate_awards(
        old_id, new_id, name, users_map, mr_enabled)

    # Pipeline Schedules
    # TODO: Remove `pipelines_schedules.py` once the import API can consistently add project pipelines schedules OR
    # Address pending issues mentioned in congregate #205
    # results["pipeline_schedules"] = p_schedules.migrate_pipeline_schedules(old_id, new_id, users_map, name)

    # Deleting any impersonation tokens used by the awards migration
    users.delete_saved_impersonation_tokens(users_map)

    # Deploy Keys (project only)
    results["deploy_keys"] = deploy_keys.migrate_deploy_keys(
        old_id, new_id, name)

    # Container Registries
    results["container_registry"] = registries.migrate_registries(
        old_id, new_id, name)

    # Project hooks (webhooks)
    results["project_hooks"] = hooks.migrate_project_hooks(
        old_id, new_id, name)

    return results


def cleanup(dry_run=True,
            skip_users=False,
            hard_delete=False,
            skip_groups=False,
            skip_projects=False):
    dry_log = get_dry_log(dry_run)
    if not skip_users:
        b.log.info("{0}Removing staged users on destination (hard_delete={1})".format(
            dry_log,
            hard_delete))
        users.delete_users(dry_run, hard_delete)

    # Remove groups and projects OR only empty groups
    if not skip_groups:
        b.log.info("{0}Removing groups{1} on destination".format(
            dry_log,
            "" if skip_projects else " and projects"))
        groups.delete_groups(dry_run, skip_projects)
    # Remove only projects
    elif not skip_projects:
        b.log.info("{}Removing projects on destination".format(dry_log))
        projects.delete_projects(dry_run)


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

                        if "%s" % project_json["namespace"].lower() in proj["path_with_namespace"].lower():
                            if project_json["namespace"].lower() == proj["namespace"]["name"].lower():
                                b.log.debug("Adding {0}/{1}".format(
                                    project_json["namespace"], project_json["name"]))
                                # b.log.info("Migrating variables for %s" % proj["name"])
                                ids.append(proj["id"])
                                break
            except IOError, e:
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
    for project in api.list_all(b.config.destination_host, b.config.destination_token, "projects"):
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
    #     b.config.destination_host, b.config.destination_token, "groups/%d/projects" % b.config.parent_id)
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
        projects = f.read()
    projects = projects.split("\n")
    dedupe = set(projects)
    print len(dedupe)


def stage_unimported_projects(dry_run=True):
    ids = []
    with open("{}/data/unimported_projects.txt".format(b.app_path), "r") as f:
        projects = f.read()
    with open("{}/data/project_json.json".format(b.app_path), "r") as f:
        available_projects = json.load(f)
    rewritten_projects = {}
    for i in enumerate(available_projects):
        new_obj = available_projects[i]
        id_num = available_projects[i]["path"]
        rewritten_projects[id_num] = new_obj

    projects = projects.split("\n")
    for p in projects:
        if p is not None and p:
            if rewritten_projects.get(p.split("/")[1], None) is not None:
                ids.append(rewritten_projects.get(p.split("/")[1])["id"])
    if ids is not None and ids:
        stage_projects(ids, dry_run)


def generate_instance_map():
    for project in api.list_all(b.config.destination_host, b.config.destination_token, "projects"):
        if project.get("import_url", None) is not None:
            import_url = sub('//.+:.+@', '//', project["import_url"])
            with open("new_repomap.txt", "ab") as f:
                f.write("%s\t%s\n" % (import_url, project["id"]))
