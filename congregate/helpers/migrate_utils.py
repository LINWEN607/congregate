import sys
import os
import errno
import json
from pathlib import Path
from shutil import copy
from time import time
from datetime import timedelta, datetime
from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import is_error_message_present, get_dry_log, strip_protocol
from congregate.helpers.utils import is_dot_com, get_congregate_path
from congregate.helpers.json_utils import read_json_file_into_object, write_json_to_file
from congregate.helpers.dict_utils import dig
from congregate.migration.gitlab.api.users import UsersApi

b = BaseClass()
users_api = UsersApi()


def get_failed_export_from_results(res):
    """
    Filter out groups or projects that either failed to export or have been found on destination.

        :param res: List of group or project exported filenames and their (boolean) status
        :return: List of group or project filenames
    """
    return [k for r in res for k, v in r.items() if not v]


def get_staged_projects():
    return read_json_file_into_object(
        f"{b.app_path}/data/staged_projects.json")


def get_staged_projects_without_failed_export(staged_projects, failed_export):
    """
    Filter out projects that failed to export from the staged projects

        :param staged_projects: The current list of staged projects
        :param failed_export: A list of project export filenames
        :return: A new staged_projects list removing those that failed export
    """
    return [p for p in staged_projects if get_project_filename(
        p) not in failed_export]


def get_staged_groups():
    return read_json_file_into_object(f"{b.app_path}/data/staged_groups.json")


def get_staged_groups_without_failed_export(staged_groups, failed_export):
    """
    Filter out groups that failed to export from the staged groups

        :param staged_groups: The current list of staged groups
        :param failed_export: A list of group export filenames
        :return: A new staged_grups list removing those that failed export
    """
    return [g for g in staged_groups if get_export_filename_from_namespace_and_name(
        g["full_path"]) not in failed_export]


def get_staged_users():
    return read_json_file_into_object(f"{b.app_path}/data/staged_users.json")


def get_project_filename(p):
    """
    Filename can be namespace and project-type dependent

        :param p: The JSON object representing a GitLab project
        :return: Project filename or empty string
    """
    if p.get("name", None) is not None and p.get(
            "namespace", None) is not None:
        return get_export_filename_from_namespace_and_name(
            p["namespace"], p["name"])
    return ""


def get_export_filename_from_namespace_and_name(namespace, name=""):
    """
    Determine exported filename for project or group (wihout name)

        :param namespace: Project or group namespace
        :param name: Project name
        :return: Exported filename
    """
    return "{0}{1}.tar.gz".format(
        namespace, "/" + name if name else "").replace("/", "_").lower()


def get_project_namespace(p):
    """
    If this is a user project, the namespace == username

        :param p: The JSON object representing a GitLab project
        :return: Destination group project namespace
    """
    p_type = p["project_type"] if p.get(
        "project_type", None) else dig(p, 'namespace', 'kind')
    p_namespace = dig(p, 'namespace', 'full_path') if isinstance(
        p.get("namespace", None), dict) else p["namespace"]

    if p_type != "user":
        if b.config.src_parent_id and b.config.src_parent_group_path:
            single_group_name = b.config.src_parent_group_path.split("/")[-1]
            p_namespace = "{0}{1}".format(single_group_name,
                                          p_namespace.split(b.config.src_parent_group_path)[-1])

        if b.config.dstn_parent_id is not None:
            return "{0}/{1}".format(b.config.dstn_parent_group_path,
                                    p_namespace)
    return p_namespace


def get_full_path_with_parent_namespace(full_path):
    """
    Determine the full path with parent namespace of a group on destination

        :param full_path: The full path of a group
        :return: Destination instance group full path with parent namespace
    """
    if b.config.src_parent_id and b.config.src_parent_group_path:
        full_path = b.config.src_parent_group_path.split("/")[-1]
    if b.config.dstn_parent_id and b.config.dstn_parent_group_path:
        return "{0}/{1}".format(b.config.dstn_parent_group_path, full_path)
    return full_path


def is_user_project(p):
    """
    Determine if a passed staged_project object (json) is a user project or not

        :param p: The JSON object representing a GitLab project
        :return: True if user project, else False
    """
    p_type = p["project_type"] if p.get(
        "project_type", None) else dig(p, 'namespace', 'kind')
    return p_type == "user"


def get_staged_user_projects(staged_projects):
    """
    Determine if there are user projects staged for migrating to a group

        :param p: The JSON object representing staged projects
        :return: List of user projects staged for migrating to a group
    """
    if is_dot_com(b.config.destination_host) or b.config.dstn_parent_id:
        return [sp["path_with_namespace"]
                for sp in staged_projects if is_user_project(sp)]
    return []


def get_user_project_namespace(p):
    """
    Determine if user project should be imported under the import_user (.com or self-managed root) or member namespace (self-managed)

        :param p: The JSON object representing a GitLab project
        :param: namespace:
        :return: Destination user project namespace
    """
    p_namespace = dig(p, 'namespace', 'full_path') if isinstance(
        p.get("namespace", None), dict) else p["namespace"]
    if is_dot_com(b.config.destination_host) or p_namespace == "root":
        b.log.info("User project {0} is assigned to import user id (ID: {1})".format(
            p["path_with_namespace"], b.config.import_user_id))
        return users_api.get_user(
            b.config.import_user_id, b.config.destination_host, b.config.destination_token).json()["username"]
    else:
        # Retrieve user username based on email to determine correct
        # destination user namespace
        if p["members"] and p["members"][0].get("email", None) is not None:
            user = find_user_by_email_comparison_without_id(
                p["members"][0]["email"])
            if user:
                return user["username"]
    return p_namespace


def find_user_by_email_comparison_without_id(email, src=False):
    """
    Find a user by email address in the destination system
    :param email: the email address to check for
    :param src: Is this the source or destination system? True if source else False. Defaults to False.
    :return: The user entity found or None
    """
    if email:
        host = b.config.source_host if src else b.config.destination_host
        b.log.info(f"Searching for user email {email} on {host}")
        users = users_api.search_for_user_by_email(
            host, b.config.source_token if src else b.config.destination_token, email)
        # Will searching for an explicit email actually return more than one?
        # Probably is just an array of 1
        for user in users:
            if user and user.get(
                    "email", None) and user["email"].lower() == email.lower():
                b.log.info(
                    f"Found user by matching primary email {email}")
                return user
            # Allow secondary emails in user search (as of 13.7)
            elif user and user.get("email", None):
                b.log.warning(
                    f"Found user by email {email}, with primary set to {user['email']}")
            else:
                b.log.error(
                    f"Could NOT find user by primary email {email}")
    else:
        b.log.error("No user email provided. Skipping")
    return None


def get_dst_path_with_namespace(p):
    """
    Determine project path with namespace on destination

        :param p: The JSON object representing a GitLab project
        :return: Destination project path with namespace
    """
    return "{0}/{1}".format(get_user_project_namespace(p)
                            if is_user_project(p) else get_project_namespace(p), p["path"])


def get_target_namespace(project):
    if target_namespace := project.get("target_namespace"):
        if (strip_protocol(target_namespace).lower() == project.get('namespace', '').lower()) or project.get("override_dstn_ns"):
            return target_namespace
        else:
            return f"{target_namespace}/{project.get('namespace')}"
    return None


def get_results(res):
    """
    Calculate number of total and successful export or import results.

        :param res: List of dicts containing export or import results
        :return: Dict of "Total" and "Successful" number of exports or imports
    """
    c = 0
    for r in res:
        for v in r.values():
            error, v = is_error_message_present(v)
            if error or not v:
                c += 1
            repo_present = dig(v, 'repository')
            if repo_present is not None and repo_present is False:
                c += 1
    return {
        "Total": len(res),
        "Successful": len(res) - c
    }


def is_top_level_group(g):
    """
    Determine if group is a top level or sub group.

        :param g: The JSON object representing a GitLab group
        :return: True if top-level-group, else False
    """
    return not g.get("parent_id", None) or g.get(
        "id", None) == b.config.src_parent_id


def is_loc_supported(loc):
    if loc not in ["filesystem", "aws"]:
        sys.exit(f"Unsupported export location: {loc}")


def can_migrate_users(users):
    can = True
    for user in users:
        name = user.get("name", None)
        username = user.get("username", None)
        email = user.get("email", None)
        if any(v is None for v in [name, username, email]):
            b.log.error(
                f"Required user metadata missing:\nName: {name}\nUsername: {username}\nEmail: {email}")
            can = False
    return can


def clean_data(dry_run=True, files=None):
    folders = [
        f"{b.app_path}/data",
        f"{b.app_path}/data/results",
        f"{b.app_path}/data/reg_tuples"
    ] if not files else files

    for f in files if files else folders:
        b.log.info(
            f"{get_dry_log(dry_run)}Removing {f if files else 'residue files in '}{'' if files else f}")
        if not dry_run:
            try:
                if files:
                    os.remove(f)
                else:
                    for ext in ("*.tpls", "*.json", "*.html"):
                        for p in Path(f).glob(ext):
                            p.unlink()
            except OSError as e:
                if e.errno != errno.ENOENT:
                    raise


def add_post_migration_stats(start, log=None):
    """
        Print all POST/PUT/DELETE requests and their total number
        Assuming you've started the migration with an empty congregate.log
        Print total migration time
    """
    reqs = ["POST request to", "PUT request to",
            "DELETE request to", "PATCH request to"]
    reqs_no = 0
    with open(f"{b.app_path}/data/logs/audit.log", "r") as f:
        for line in f:
            if any(req in line for req in reqs):
                reqs_no += 1
        if log:
            log.info(f"Total number of POST/PUT/DELETE requests: {reqs_no}")
    if log:
        log.info("Total time: {}".format(timedelta(seconds=time() - start)))


def write_results_to_file(import_results, result_type="project", log=None):
    end_time = str(datetime.now()).replace(" ", "_")
    file_path = f"{b.app_path}/data/results/{result_type}_migration_results_{end_time}.json"
    write_json_to_file(file_path, import_results, log=log)
    copy(file_path,
         f"{b.app_path}/data/results/{result_type}_migration_results.json")


def check_is_project_or_group_for_logging(is_project):
    return "Project" if is_project else "Group"


def migration_dry_run(data_type, post_data):
    with open(f"{get_congregate_path()}/data/results/dry_run_{data_type}_migration.json", "a") as f:
        json.dump(post_data, f, indent=4)
