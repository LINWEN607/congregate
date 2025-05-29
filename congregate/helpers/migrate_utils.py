import sys
import os
import signal
import errno
import json

from string import punctuation
from re import sub
from collections import Counter
from pathlib import Path
from shutil import copy
from time import time
from datetime import timedelta, datetime
from requests import Response
from gitlab_ps_utils.misc_utils import is_error_message_present, get_dry_log, safe_json_response, strip_netloc
from gitlab_ps_utils.json_utils import read_json_file_into_object, write_json_to_file
from gitlab_ps_utils.dict_utils import dig
from congregate.helpers.base_class import BaseClass
from congregate.helpers.utils import is_dot_com, get_congregate_path
from congregate.migration.gitlab.api.users import UsersApi
from congregate.migration.gitlab.api.instance import InstanceApi
from congregate.migration.meta.constants import TOP_LEVEL_RESERVED_NAMES, SUBGROUP_RESERVED_NAMES, PROJECT_RESERVED_NAMES

b = BaseClass()
users_api = UsersApi()
instance_api = InstanceApi()

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


def get_project_id_mapping():
    return read_json_file_into_object(
        f"{b.app_path}/data/project_id_mapping.json")


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
        :return: A new staged_groups list removing those that failed export
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


def get_export_filename_from_namespace_and_name(namespace, name="", airgap=False):
    """
    Determine exported filename for project or group (without name)

        :param namespace: Project or group namespace
        :param name: Project name
        :return: Exported filename
    """
    return f"{namespace}{'/' + name if name else ''}{'_artifact' if airgap else ''}.tar.gz".replace("/", "_").lower()


def get_project_dest_namespace(p, mirror=False, group_path=None):
    """
    If this is a user project, the namespace == username

        :param p (dict): The JSON object representing a GitLab project
        :param mirror (bool): Whether we are mirroring a repo on destination
        :return: Destination group project namespace
    """
    p_namespace = dig(p, 'namespace', 'full_path') if isinstance(
        p.get("namespace"), dict) else p.get("namespace")

    if not is_user_project(p) and group_path and not mirror:
        return group_path
    if not is_user_project(p) and b.config.dstn_parent_id and not mirror:
        return f"{b.config.dstn_parent_group_path}/{p_namespace}"
    return p_namespace


def get_full_path_with_parent_namespace(full_path):
    """
    Determine the full path with parent namespace of a group on destination

        :param full_path: The full path of a group
        :return: Destination instance group full path with parent namespace
    """
    if b.config.dstn_parent_id and b.config.dstn_parent_group_path:
        return f"{b.config.dstn_parent_group_path}/{full_path}"
    return full_path


def is_user_project(p):
    """
    Determine if a passed staged_project object (json) is a user project or not

        :param p: The JSON object representing a GitLab project
        :return: True if user project, else False
    """
    p_type = p["project_type"] if p.get(
        "project_type") else dig(p, 'namespace', 'kind')
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


def check_for_staged_user_projects(staged_projects):
    """
    Check if user projects are in the list of staged_projects. If they are, log a warning and return the list of namespaces, else return None

        :param staged_projects: The JSON array of staged projects
        :return: True if user projects are found in staged_projects, else False
    """
    if user_projects := get_staged_user_projects(staged_projects):
        b.log.warning("USER projects staged (Count : {}):\n{}".format(
            len(user_projects), "\n".join(u for u in user_projects)))
    return user_projects


def get_user_project_namespace(p):
    """
    Determine if user project should be imported under the import_user (self-managed root) or member namespace (self-managed)

        :param p: The JSON object representing a GitLab project
        :param: namespace:
        :return: Destination user project namespace
    """
    p_namespace = dig(p, 'namespace', 'full_path') if isinstance(
        p.get("namespace"), dict) else p["namespace"]
    if is_dot_com(b.config.destination_host) or p_namespace == "root":
        b.log.info(
            f"User project {p['path_with_namespace']} is assigned to import user (ID: {b.config.import_user_id})")
        user = safe_json_response(users_api.get_user(
            b.config.import_user_id, b.config.destination_host, b.config.destination_token))
        if user:
            return user.get("username")
    # Retrieve user username based on user_mapping_field to determine correct
    # destination user namespace
    field = b.config.user_mapping_field
    if field == "email" and p.get("members") and p["members"][0]:
        user = find_user_by_email_comparison_without_id(
            p["members"][0][field])
        if user:
            return user.get("username")
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
            if not isinstance(user, dict):
                b.log.error(f"Failed to find user by email '{email}':\n{user}")
                return None
            if user and user.get(
                    "email") and user["email"].lower() == email.lower():
                b.log.info(
                    f"Found user by matching primary email {email}")
                return user
            # Allow secondary emails in user search (as of 13.7)
            if user and user.get("email"):
                b.log.warning(
                    f"Found user by secondary email {email}, with primary set to {user['email']}")
                return user
            # When using non-admin token for migrations from non-gitlab sources
            if user and user.get("id") and b.config.source_type != "gitlab":
                b.log.warning(f"Found user by public email {email}")
                return user
            b.log.error(
                f"Could NOT find user by primary email {email}")
    else:
        b.log.error(f"User email NOT provided ({email}). Skipping")
    return None


def search_for_user_by_user_mapping_field(field, user, host, token):
    if field == "email":
        user_search = users_api.search_for_user_by_email(
            host, token, user.get(field))
    elif field == "username" and not is_dot_com(b.config.destination_host):
        user_search = users_api.search_for_user_by_username(
            host, token, user.get(field))
    else:
        b.log.error(
            f"Invalid (or insecure, for gitlab.com) user mapping field configured: '{field}'")
        return {}
    for u in user_search:
        if u.get(field, "").lower() == user.get(field, "").lower():
            return u
    return {}


def get_dst_path_with_namespace(p, mirror=False, group_path=None):
    """
    Determine project path with namespace on destination

        :param p (dict): The JSON object representing a GitLab project
        :param mirror (bool): Whether we are mirroring a repo on destination
        :return: Destination project path with namespace
    """
    return f"{get_user_project_namespace(p) if is_user_project(p) else get_project_dest_namespace(p, mirror, group_path)}/{p.get('path')}"


def get_target_namespace(project):
    if target_namespace := project.get("target_namespace"):
        if (strip_netloc(target_namespace).lower() == project.get(
                'namespace', '').lower()) or project.get("override_dstn_ns"):
            return target_namespace
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
            is_error, v = is_error_message_present(v)
            if is_error or v == False:
                c += 1
            repo_present = dig(v, 'repository')
            if repo_present == False:
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
    return not g.get("parent_id") or g.get(
        "id") == b.config.src_parent_id


def is_loc_supported(loc):
    if loc.lower() not in ["filesystem", "aws"]:
        b.log.error(f"Unsupported export location: {loc}")
        sys.exit(os.EX_CONFIG)


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
        log.info(f"Total time: {timedelta(seconds=time() - start)}")


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


def get_target_project_path(project):
    if target_namespace := get_target_namespace(project):
        target_project_path = f"{target_namespace}/{project.get('path')}"
    else:
        target_project_path = get_dst_path_with_namespace(project)
    return target_project_path


def sanitize_name(name, full_path, is_group=False, is_subgroup=False):
    """
    Validate and sanitize group and project names to satisfy the following criteria:
    Name can only contain letters, digits, emojis, '_', '.', dash, space, parenthesis (groups only).
    It must start with letter, digit, emoji or '_'.
    Also checks for reserved GitLab names. If the name is reserved, rename or log an error.
    Example:
        " !  _-:: This.is-how/WE do\n&it#? - šđžčć_  ? " -> "This.is-how WE do it - šđžčć"
    """
    # Remove leading and trailing special characters and spaces
    stripped = name.strip(punctuation + " ")

    if not stripped and name == "-":
        # If the original string was solely a dash, restore it
        stripped = "-"

    # Validate naming convention in docstring and sanitize name
    valid = " ".join(sub(
        r"[^\U00010000-\U0010ffff\w\_\-\.\(\) ]" if is_group else r"[^\U00010000-\U0010ffff\w\_\-\. ]", " ", stripped).split())
    if name != valid:
        b.log.warning(
            f"Renaming invalid {'group' if is_group else 'project'} name '{name}' -> '{valid}' ({full_path})")
        if is_group:
            b.log.error(
                f"Sub-group '{name}' ({full_path}) requires a rename on source or direct import")

    if not is_group:
        # This is a project
        if valid.lower() in PROJECT_RESERVED_NAMES:
            new_name = f"{valid}-renamed"
            b.log.warning(
                f"Project name '{valid}' is reserved; renaming to '{new_name}' ({full_path})."
            )
            valid = new_name
    else:
        # This is a group. Check if top-level or subgroup
        if is_subgroup:
            if valid.lower() in SUBGROUP_RESERVED_NAMES:
                new_name = f"{valid}-renamed"
                b.log.warning(
                    f"Subgroup name '{valid}' is reserved; renaming to '{new_name}' ({full_path})."
                )
                valid = new_name
        else:
            # top-level group
            if valid.lower() in TOP_LEVEL_RESERVED_NAMES:
                new_name = f"{valid}-renamed"
                b.log.warning(
                    f"Top-level group name '{valid}' is reserved; renaming to '{new_name}' ({full_path})."
                )
                valid = new_name
    return valid


def sanitize_project_path(path, full_path):
    """
    Validate and sanitize project paths to satisfy the following criteria:
    Project namespace path can contain only letters, digits, '_', '-' and '.'. Cannot start with '-', end in '.git' or end in '.atom'
    Path can contain only letters, digits, '_', '-' and '.'. Cannot start with '-', end in '.git' or end in '.atom'
    Path must not start or end with a special character and must not contain consecutive special characters.
    Example:
        "!_-::This.is;;-how_we--do\n&IT#?-šđžčć_?" -> "This.is-how_we-do-IT"
    """
    # Validate path convention in docstring and sanitize path
    valid = sub(r"[._-][^A-Za-z0-9]+", "-",
                sub(r"[^A-Za-z0-9\_\-\.]+", "-", path)).strip("-_.")
    if path != valid:
        b.log.warning(
            f"Updating invalid project path '{path}' -> '{valid}' ({full_path})")
    return valid


def get_duplicate_paths(data, are_projects=True):
    """
    Legacy GL versions had case insensitive paths, which on newer GL versions are seen as duplicates
    """
    paths = [x.get("path_with_namespace", "").lower() if are_projects else x.get(
        "full_path", "").lower() for x in data]
    return [i for i, c in Counter(paths).items() if c > 1]


def is_gl_version_older_than(set_version, host, token, log):
    """
    Lookup GL instance version and throw custom log based
    """
    version = safe_json_response(instance_api.get_version(host, token))
    # Include minor version digit, e.g. 16.7
    if version and version.get("version") and float(".".join(version["version"].split(".", 2)[:2])) < set_version:
        b.log.info(f"{log} on GitLab version '{version}'")
        return True
    return False


def get_stage_wave_paths(project, group_path=None):
    """
    Construct stage_wave destination namespace and path_with_namespace
    """
    dstn_pwn = get_target_project_path(project)

    # TODO: Make this target namespace lookup requirement configurable
    if target_namespace := get_target_namespace(project):
        tn = target_namespace
    else:
        # Group full path, e.g. a/b/c of a/b/c/d
        tn = get_dst_path_with_namespace(
            project, group_path=group_path).rsplit("/", 1)[0]
    return dstn_pwn, tn


def get_subset_list():
    with open(b.config.list_subset_input_path, "r") as f:
        for line in f.read().splitlines():
            yield line


def check_list_subset_input_file_path():
    subset_path = b.config.list_subset_input_path
    if not os.path.isfile(subset_path):
        b.log.error(
            f"Config 'list_subset_input_path' file path '{subset_path}' does not exist. Please create it")
        sys.exit(os.EX_CONFIG)
    return subset_path


def validate_groups_and_projects(staged, are_projects=False):
    if dupes := get_duplicate_paths(
            staged, are_projects=are_projects):
        b.log.warning("Duplicate {} paths:\n{}".format(
            "project" if are_projects else "group", "\n".join(d for d in dupes)))
    if not are_projects:
        # Temp bug fix: Group names must be 2+ characters long
        if invalid_group_names := [
                g for g in staged if len(g["name"]) < 2]:
            b.log.warning("Invalid group names:\n{}".format(
                "\n".join(i for i in invalid_group_names)))


def toggle_maintenance_mode(
        off=False, msg=None, dest=False, dry_run=True):
    host = b.config.destination_host if dest else b.config.source_host
    if is_dot_com(host):
        b.log.warning(
            f"Not allowed to toggle maintenance mode on {host}")
    else:
        data = {
            "maintenance_mode": not off}
        if not off and msg:
            data["maintenance_mode_message"] = msg.replace("+", " ")
        token = b.config.destination_token if dest else b.config.source_token
        b.log.warning(
            f"{get_dry_log(dry_run)}Turning maintenance mode {'OFF' if off else 'ON'} on {host}")
        if not dry_run:
            instance_api.change_application_settings(
                host, token, data)


def check_download_directory(directory_path):
    """
    Check if the download directory exists.
    """
    return os.path.isdir(directory_path)

def default_response():
    resp = Response()
    resp.status_code = 400
    resp._content = b"Unable to execute import request"
    return resp