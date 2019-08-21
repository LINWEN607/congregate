"""
    Congregate - GitLab instance migration utility

    Copyright (c) 2018 - GitLab
"""

import os
import json
from re import sub
from multiprocessing.dummy import Pool as ThreadPool
from multiprocessing import Lock
import requests

from congregate.helpers import api
from congregate.aws import AwsClient
from congregate.cli.stage_projects import stage_projects
from congregate.helpers import base_module as b
from congregate.migration.gitlab.importexport import ImportExportClient as ie_client
from congregate.migration.gitlab.variables import VariablesClient as vars_client
from congregate.migration.gitlab.users import UsersClient as users_client
from congregate.migration.gitlab.groups import GroupsClient as groups_client
from congregate.migration.gitlab.projects import ProjectsClient as proj_client
from congregate.migration.gitlab.pushrules import PushRulesClient as pushrules_client
from congregate.migration.gitlab.branches import BranchesClient
from congregate.migration.gitlab.merge_request_approvers import MergeRequestApproversClient
from congregate.migration.gitlab.awards import AwardsClient
from congregate.migration.gitlab.registries import RegistryClient
from congregate.migration.gitlab.pipeline_schedules import PipelineSchedulesClient
from congregate.migration.gitlab.project_export import ProjectExportClient
from congregate.migration.mirror import MirrorClient
from congregate.migration.gitlab.deploy_keys import DeployKeysClient
from congregate.migration.bitbucket import client as bitbucket
from congregate.helpers.exceptions import ConfigurationException

aws = AwsClient()
ie = ie_client()
mirror = MirrorClient()
variables = vars_client()
users = users_client()
groups = groups_client()
projects = proj_client()
pushrules = pushrules_client()
branches = BranchesClient()
awards = AwardsClient()
mr = MergeRequestApproversClient()
awards = AwardsClient()
registries = RegistryClient()
schedules = PipelineSchedulesClient()
deploy_keys = DeployKeysClient()
project_export = ProjectExportClient()

full_parent_namespace = groups.find_parent_group_path()


def migrate_project_info():
    """
        Subsequent function to update project info AFTER import
    """
    staged_projects = get_staged_projects()
    for project in staged_projects:
        members = project["members"]
        project.pop("members")
        b.log.debug("Searching for %s" % project["name"])
        new_project = api.search(
            b.config.destination_host, b.config.destination_token, 'projects', project['name'])
        if new_project is not None and new_project:
            if new_project[0]["name"] == project["name"] and \
                    new_project[0]["namespace"]["name"] == project["namespace"]:
                root_user_present = False
                for member in members:
                    if member["id"] == b.config.import_user_id:
                        root_user_present = True
                    new_member = {
                        "user_id": member["id"],
                        "access_level": member["access_level"]
                    }

                    try:
                        api.generate_post_request(b.config.destination_host, b.config.destination_token,
                                                  "projects/%d/members" % new_project[0]["id"], json.dumps(new_member))

                    except requests.exceptions.RequestException, e:
                        b.log.error(e)
                        b.log.error(
                            "Member might already exist. Attempting to update access level")
                        try:
                            api.generate_put_request(b.config.destination_host, b.config.destination_token,
                                                     "projects/%d/members/%d?access_level=%d" % (
                                                         new_project[0]["id"], member["id"], member["access_level"]),
                                                     data=None)
                        except requests.exceptions.RequestException, e:
                            b.log.error(e)
                            b.log.error(
                                "Attempting to update existing member failed")

                if not root_user_present:
                    b.log.info("removing root user from project")
                    api.generate_delete_request(b.config.destination_host, b.config.destination_token,
                                                "projects/%d/members/%d" % (
                                                    new_project[0]["id"], b.config.import_user_id))


def migrate_single_project_info(project, id):
    """
        Subsequent function to update project info AFTER import
    """
    members = project["members"]
    project.pop("members")
    name = project["name"]
    old_id = project["id"]
    results = {}

    b.log.info("Searching for project %s" % name)
    if id is None:
        _, id = projects.find_project_by_path(b.config.destination_host, b.config.destination_token, full_parent_namespace, project["namespace"], project["name"])

    # Project Members
    # TODO: Should this be commented out? Is in Master pre merge
    # projects.add_members(members, id)

    # Project Avatar
    # DOES THIS NEED TO STILL BE HERE AFTER MERGE?
    # No, as this assumes you have access to the host systems uploads as a URL instead of letting the
    # import of the TAR file handle it
    # projects.migrate_avatar(id, old_id)

    # Shared with groups
    projects.add_shared_groups(old_id, id)

    # CI/CD Variables
    try:
        if variables.are_enabled(old_id):
            b.log.info("Migrating {} CI/CD variables".format(name))
            variables.migrate_variables(
                id, old_id, "project")
            results["variables"] = True
        else:
            b.log.warn("CI/CD is disabled for project {}".format(name))
    except Exception, e:
        b.log.error("Failed to migrate {} CI/CD variables".format(name))
        b.log.error(e)
        results["variables"] = False

    # Push Rules
    try:
        push_rule = pushrules.get_push_rules(
            old_id, b.config.source_host, b.config.source_token).json()
        if push_rule is not None and push_rule:
            b.log.info("Migrating push rules for {}".format(name))
            pushrules.add_push_rule(id, b.config.destination_host,
                                    b.config.destination_token, push_rule)
            results["push_rules"] = True
    except Exception, e:
        b.log.error("Failed to migrate push rules for {}".format(name))
        b.log.error(e)
        results["push_rules"] = False

    # Merge Request Approvers
    try:
        if mr.are_enabled(old_id):
            b.log.info("Migrating merge request approvers for {}".format(name))
            mr.migrate_merge_request_approvers(id, old_id)
            results["merge_request_approvers"] = True
        else:
            b.log.warn("Merge requests are disabled for project {}".format(name))
    except Exception, e:
        b.log.error("Failed to migrate merge request approvers for {}".format(name))
        b.log.error(e)
        results["merge_request_approvers"] = False

    # Protected Branches
    # TODO: Should this be commented out? Is in Master pre merge
    # b.log.info("Updating protected branches")
    # branches.migrate_protected_branches(id, project["id"])

    # Awards
    users_map = {}
    try:
        # Issue, MR and snippet awards
        all_awards = awards.are_enabled(old_id)
        if all_awards[0] or all_awards[1] or all_awards[2]:
            b.log.info("Migrating awards for {}".format(name))
            awards.migrate_awards(id, old_id, users_map)
            results["awards"] = {
                "issues": all_awards[0],
                "merge_requests": all_awards[1],
                "snippets": all_awards[2]
            }
        else:
            b.log.warn("Awards (job/MR/snippet) are disabled for project {}".format(name))
    except Exception, e:
        b.log.error("Failed to migrate awards for {}".format(name))
        b.log.error(e)
        results["awards"] = False

    # # Pipeline Schedules
    # b.log.info("Migrating pipeline schedules for %s" % name)
    # schedules.migrate_pipeline_schedules(id, old_id, users_map)

    # Deleting any impersonation tokens used by the awards migration
    try:
        users.delete_saved_impersonation_tokens(users_map)
    except Exception, e:
        b.log.error(e)

    # Deploy Keys (project only)
    try:
        keys = deploy_keys.list_project_deploy_keys(old_id)
        if keys:
            b.log.info("Migrating project deploy keys for {}".format(name))
            deploy_keys.migrate_deploy_keys(id, old_id, keys)
            results["deploy_keys"] = True
    except Exception, e:
        b.log.error("Failed to migrate project {0} deploy keys, with error:\n{}".format(name, e))
        results["deploy_keys"] = False

    # Container Registries
    try:
        registry = registries.are_enabled(id, old_id)
        if registry[0] and registry[1]:
            b.log.info("Migrating container registries for {}".format(name))
            registries.migrate_registries(id, project["id"])
            results["container_registry"] = True
        else:
            instance = "source" if not registry[0] else "destination" if not registry[1] else "source and destination"
            b.log.warn("Container registry is disabled for {} instance".format(instance))
    except Exception, e:
        b.log.error("Failed to migrate container registries for {}".format(name))
        b.log.error(e)
        results["container_registry"] = False

    return results

def migrate_given_export(project_json):
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
    b.log.debug("Searching for existing project {}".format(name))
    try:
        project_exists, project_id = projects.find_project_by_path(
            b.config.destination_host, b.config.destination_token, full_parent_namespace, namespace, name)
        if project_id:
            import_check = ie.get_import_status(
                b.config.destination_host, b.config.destination_token, project_id).json()
            b.log.info("Project {0} import status: {1}".format(name, import_check["import_status"]))
        if not project_exists:
            b.log.info("Importing project {}".format(name))
            import_id = ie.import_project(project_json)
            if import_id is not None:
                # Archived projects cannot be exported
                if archived:
                    b.log.info("Unarchiving source project {}".format(name))
                    projects.projects_api.unarchive_project(
                        b.config.source_host, b.config.source_token, source_id)
                b.log.info("Migrating {} project info".format(name))
                post_import_results = migrate_single_project_info(project_json, import_id)
                results[path] = post_import_results
    except requests.exceptions.RequestException, e:
        b.log.error(e)
    except KeyError, e:
        b.log.error(e)
        raise KeyError("Something broke in migrate_given_export ({})".format(name))
    except OverflowError, e:
        b.log.error(e)
    finally:
        if archived:
            b.log.info("Archiving back source project {}".format(name))
            projects.projects_api.archive_project(
                b.config.source_host, b.config.source_token, source_id)
    return results


def init_pool(l):
    global lock
    lock = l


def start_multi_thead(function, iterable):
    l = Lock()
    pool = ThreadPool(initializer=init_pool, initargs=(l,),
                      processes=b.config.threads)
    pool.map(function, iterable)
    pool.close()
    pool.join()


def migrate(threads=None, skip_users = False):
    if threads is not None:
        b.config.threads = threads

    if b.config.external_source != False:
        with open("%s" % b.config.repo_list, "r") as f:
            repo_list = json.load(f)
        # bitbucket.handle_bitbucket_migration({
        #     "name": "repo_1",
        #     "web_repo_url": "http://gmiller@bbhost:7990/scm/tp1/repo_1.git",
        #     "group": "test_project_1",
        #     "project_users": [
        #         {
        #             "displayName": "Migrate 1",
        #             "name": "Migrate 1",
        #             "username": "migrate_1",
        #             "email": "migrate1@abc.com",
        #             "permission": "PROJECT_WRITE"
        #         }],
        #     "repo_users": [
        #         {
        #             "displayName": "Migrate 2",
        #             "name": "Migrate 2",
        #             "username": "migrate_2",
        #             "email": "migrate2@abc.com",
        #             "permission": "PROJECT_READ"
        #         }
        #     ]
        # })
        start_multi_thead(bitbucket.handle_bitbucket_migration, repo_list)

    else:
        with open("%s/data/staged_groups.json" % b.app_path, "r") as f:
            groups_file = json.load(f)

        if not skip_users:
            b.log.info("Migrating user info")
            new_users = users.migrate_user_info()

            with open("%s/data/new_user_ids.txt" % b.app_path, "w") as f:
                for new_user in new_users:
                    f.write("%s\n" % new_user)

            if new_users is not None and new_users:
                users.update_user_info(new_users)
            else:
                users.update_user_info(new_users, overwrite=False)

        if groups_file is not None and groups_file:
            b.log.info("Migrating group info")
            groups.migrate_group_info()
        else:
            b.log.info("No groups to migrate")

        staged_projects = get_staged_projects()
        if staged_projects is not None and staged_projects:
            b.log.info("Migrating project info")
            pool = ThreadPool(b.config.threads)
            results = pool.map(handle_migrating_file, staged_projects)
            pool.close()
            pool.join()

            b.log.info("Importing projects")
            import_pool = ThreadPool(b.config.threads)
            results = import_pool.map(migrate_given_export, staged_projects)
            b.log.info("### Results ###\n%s" % json.dumps(results, indent=4))
            import_pool.close()
            import_pool.join()

            # migrate_project_info()
        else:
            b.log.info("No projects to migrate")


def kick_off_import():
    staged_projects = get_staged_projects()
    if staged_projects is not None and staged_projects:
        b.log.info("Importing projects")
        pool = ThreadPool(b.config.threads)
        results = pool.map(migrate_given_export, staged_projects)
        b.log.info("### Results ###\n%s" % json.dumps(results, indent=4))
        pool.close()
        pool.join()

        # migrate_project_info()
    else:
        b.log.info("No projects to migrate")


def handle_migrating_file(f):
    name = f["name"]
    id = f["id"]
    namespace = f["namespace"]
    try:
        if b.config.parent_id is not None and f["project_type"] != "user":
            parent_namespace = groups.groups_api.get_group(
                b.config.parent_id, b.config.destination_host, b.config.destination_token).json()
            namespace = "%s/%s" % (parent_namespace["path"], f["namespace"])
        else:
            namespace = f["namespace"]
        if b.config.location == "filesystem":
            b.log.info("Migrating project {} through filesystem".format(name))
            ie.export_import_thru_filesystem(id, name, namespace)
            # migrate_project_info()

        elif b.config.location.lower() == "filesystem-aws":
            b.log.info("Migrating project {} through filesystem-AWS".format(name))
            ie.export_import_thru_fs_aws(id, name, namespace)

        elif (b.config.location).lower() == "aws":
            b.log.info("Migrating project {} through AWS".format(name))
            exported = ie.export_import_thru_aws(id, name, namespace, full_parent_namespace)
            print("\n" + name + "\n" + namespace + "\n" + full_parent_namespace)
            filename = "%s_%s.tar.gz" % (namespace, name)
            try:
                project_export.update_project_export_members(name, namespace, filename)
            except Exception, e:
                b.log.error("Failed to update {0} project export, with error:\n{1}".format(filename, e))
            return exported
            # TODO: Needed?
            # migrate_given_export(f)
    except IOError, e:
        b.log.error(e)


def find_unimported_projects():
    unimported_projects = []
    with open("%s/data/project_json.json" % b.app_path, "r") as f:
        files = json.load(f)
    if files is not None and files:
        for project_json in files:
            try:
                b.log.debug("Searching for existing %s" % project_json["name"])
                project_exists = False
                for proj in projects.projects_api.search_for_project(b.config.destination_host, b.config.destination_token,
                                                        project_json['name']):
                    if proj["name"] == project_json["name"]:
                        if project_json["namespace"]["full_path"].lower() == proj["path_with_namespace"].lower():
                            project_exists = True
                            break
                if not project_exists:
                    b.log.info("Recording %s" % project_json["name"])
                    unimported_projects.append(
                        "%s/%s" % (project_json["namespace"], project_json["name"]))
            except IOError, e:
                b.log.error(e)

    if unimported_projects is not None and unimported_projects:
        with open("%s/data/unimported_projects.txt" % b.app_path, "w") as f:
            for project in unimported_projects:
                f.writelines(project + "\n")
        print "Found %d unimported projects" % len(unimported_projects)


def remove_all_mirrors():
    # if os.path.isfile("%s/data/new_ids.txt" % b.app_path):
    #     ids = []
    #     with open("%s/data/new_ids.txt" % b.app_path, "r") as f:
    #         for line in f:
    #             ids.append(int(line.split("\n")[0]))
    # else:
    ids = get_new_ids()
    for i in ids:
        mirror.remove_mirror(i)


def get_new_ids():
    ids = []
    staged_projects = get_staged_projects()
    if staged_projects is not None and staged_projects:
        for project_json in staged_projects:
            try:
                b.log.debug("Searching for existing %s" % project_json["name"])
                for proj in projects.projects_api.search_for_project(b.config.destination_host, b.config.destination_token,
                                                        project_json['name']):
                    if proj["name"] == project_json["name"]:

                        if "%s" % project_json["namespace"].lower() in proj["path_with_namespace"].lower():
                            print project_json["namespace"]
                            print proj["namespace"]["name"]
                            if project_json["namespace"].lower() == proj["namespace"]["name"].lower():
                                print "adding %s/%s" % (
                                    project_json["namespace"], project_json["name"])
                                # b.log.info("Migrating variables for %s" % proj["name"])
                                ids.append(proj["id"])
                                break
            except IOError, e:
                b.log.error(e)
        return ids


def enable_mirror():
    ids = get_new_ids()
    staged_projects = get_staged_projects()
    if staged_projects is not None and staged_projects:
        for i in enumerate(staged_projects):
            id = ids[i]
            project = staged_projects[i]
            mirror.mirror_repo(project, id)


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
            print "%s, %s" % (
                project["path_with_namespace"], project["visibility"])
            count += 1
            data = {
                "visibility": "private"
            }
            change = api.generate_put_request(
                b.config.destination_host, b.config.destination_token, "projects/%d?visibility=private" % int(i), data=None)
            print change

    print count


def set_default_branch():
    for project in api.list_all(b.config.destination_host, b.config.destination_token, "projects"):
        if project.get("default_branch", None) != "master":
            id = project["id"]
            name = project["name"]
            print "Setting default branch to master for project %s" % name
            resp = api.generate_put_request(
                b.config.destination_host, b.config.destination_token, "projects/%d?default_branch=master" % id, data=None)
            print "Status: %d" % resp.status_code


def update_diverging_branch():
    for project in api.list_all(b.config.destination_host, b.config.destination_token, "projects"):
        if project.get("mirror_overwrites_diverged_branches", None) != True:
            id = project["id"]
            name = project["name"]
            print "Setting mirror_overwrites_diverged_branches to true for project %s" % name
            resp = api.generate_put_request(b.config.destination_host, b.config.destination_token,
                                            "projects/%d?mirror_overwrites_diverged_branches=true" % id, data=None)
            print "Status: %d" % resp.status_code


def get_total_migrated_count():
    group_projects = api.get_count(
        b.config.destination_host, b.config.destination_token, "groups/%d/projects" % b.config.parent_id)
    subgroup_count = 0
    for group in api.list_all(b.config.destination_host, b.config.destination_token, "groups/%d/subgroups" % b.config.parent_id):
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


def stage_unimported_projects():
    ids = []
    with open("%s/data/unimported_projects.txt" % b.app_path, "r") as f:
        projects = f.read()
    with open("%s/data/project_json.json" % b.app_path, "r") as f:
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
        stage_projects(ids)


def generate_instance_map():
    for project in api.list_all(b.config.destination_host, b.config.destination_token, "projects"):
        if project.get("import_url", None) is not None:
            import_url = sub('//.+:.+@', '//', project["import_url"])
            with open("new_repomap.txt", "ab") as f:
                f.write("%s\t%s\n" % (import_url, project["id"]))


def count_unarchived_projects():
    unarchived_projects = []
    for project in api.list_all(b.config.source_host, b.config.source_token, "projects"):
        if project.get("archived", None) is not None:
            if not project["archived"]:
                unarchived_projects.append(project["name_with_namespace"])

    b.log.info("Unarchived projects ({0}):\n{1}".format(unarchived_projects, len(unarchived_projects)))


def archive_staged_projects(dry_run=False):
    staged_projects = get_staged_projects()
    b.log.info("Project count is: %s", len(staged_projects))
    try:
        for project in staged_projects:
            id = project["id"]
            b.log.info("Archiving project %s (ID: %s)" % (project["name"], id))
            if not dry_run:
                projects.projects_api.archive_project(b.config.source_host, b.config.source_token, id)
    except requests.exceptions.RequestException, e:
        b.log.error("Failed to archive staged projects, with error:\n%s" % e)


def unarchive_staged_projects(dry_run=False):
    staged_projects = get_staged_projects()
    b.log.info("Project count is: %s", len(staged_projects))
    try:
        for project in staged_projects:
            id = project["id"]
            b.log.info("Unarchiving project %s (ID: %s)" % (project["name"], id))
            if not dry_run:
                projects.projects_api.unarchive_project(b.config.source_host, b.config.source_token, id)
    except requests.exceptions.RequestException, e:
        b.log.error("Failed to unarchive staged projects, with error:\n%s" % e)


def get_staged_projects():
    with open("%s/data/stage.json" % b.app_path, "r") as f:
        return json.load(f)


def find_empty_repos():
    empty_repos = []
    for project in api.list_all(b.config.destination_host, b.config.destination_token, "projects?statistics=true"):
        if project.get("statistics", None) is not None:
            if project["statistics"]["repository_size"] == 0:
                b.log.info("Empty repo found")
                for proj in api.list_all(b.config.source_host, b.config.source_token, "projects?statistics=true"):
                    if proj["name"] == project["name"] and project["namespace"]["path"] in proj["namespace"]["path"]:
                        b.log.info("Found project")
                        if proj.get("statistics", None) is not None:
                            if proj["statistics"]["repository_size"] == 0:
                                b.log.info(
                                    "Project is empty in source instance. Ignoring")
                            else:
                                empty_repos.append(
                                    project["name_with_namespace"])

    print empty_repos
    print len(empty_repos)
