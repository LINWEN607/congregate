from collections import Counter

from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import is_dot_com
from congregate.migration.gitlab.users import UsersApi


b = BaseClass()
users_api = UsersApi()


def get_failed_export_from_results(res):
    """
    Filter out groups or projects that either failed to export or have been found on destination.

        :param res: List of group or project exported filenames and their (boolean) status
        :return: List of group or project filenames
    """
    return [k for r in res for k, v in r.items() if not v]


def get_staged_projects_without_failed_export(staged_projects, failed_export):
    """
    Filter out projects that failed to export from the staged projects

        :param staged_projects: The current list of staged projects
        :param failed_export: A list of project export filenames
        :return: A new staged_projects list removing those that failed export
    """
    return [p for p in staged_projects if get_project_filename(
        p) not in failed_export]


def get_staged_groups_without_failed_export(staged_groups, failed_export):
    """
    Filter out groups that failed to export from the staged groups

        :param staged_groups: The current list of staged groups
        :param failed_export: A list of group export filenames
        :return: A new staged_grups list removing those that failed export
    """
    return [g for g in staged_groups if get_export_filename_from_namespace_and_name(g["full_path"]) not in failed_export]


def get_project_filename(p):
    """
    Filename can be namespace and project-type dependent

        :param p: The JSON object representing a GitLab project
        :return: Project filename or empty string
    """
    if p.get("name", None) is not None and p.get("namespace", None) is not None:
        return get_export_filename_from_namespace_and_name(p["namespace"], p["name"])
    return ""


def get_export_filename_from_namespace_and_name(namespace, name=""):
    """
    Determine exported filename for project or group (wihout name)

        :param namespace: Project or group namespace
        :param name: Project name
        :return: Exported filename
    """
    return "{0}{1}.tar.gz".format(namespace, "/" + name if name else "").replace("/", "_").lower()


def get_project_namespace(p):
    """
    If this is a user project, the namespace == username

        :param p: The JSON object representing a GitLab project
        :return: Destination group project namespace
    """
    p_type = p["project_type"] if p.get(
        "project_type", None) else p["namespace"]["kind"]
    p_namespace = p["namespace"]["full_path"] if isinstance(
        p.get("namespace", None), dict) else p["namespace"]
    if b.config.dest_parent_id is not None and p_type != "user":
        return "{0}/{1}".format(b.config.dest_parent_group_path, p_namespace)
    return p_namespace


def get_full_path_with_parent_namespace(full_path):
    """
    Determine the full path with parent namespace of a group on destination

        :param full_path: The full path of a group
        :return: Destination instance group full path with parent namespace
    """
    if b.config.dest_parent_id and b.config.dest_parent_group_path:
        return "{0}/{1}".format(b.config.dest_parent_group_path, full_path)
    return full_path


def is_user_project(p):
    """
    Determine if a passed staged_project object (json) is a user project or not

        :param p: The JSON object representing a GitLab project
        :return: True if user project, else False
    """
    p_type = p["project_type"] if p.get(
        "project_type", None) else p["namespace"]["kind"]
    return p_type == "user"


def get_user_project_namespace(p):
    """
    Determine if user project should be imported under the import_user (.com or self-managed root) or member namespace (self-managed)

        :param p: The JSON object representing a GitLab project
        :param: namespace:
        :return: Destination user project namespace
    """
    p_namespace = p["namespace"]["full_path"] if isinstance(
        p.get("namespace", None), dict) else p["namespace"]
    if is_dot_com(b.config.destination_host) or p_namespace == "root":
        b.log.info("User project {0} is assigned to import user id (ID: {1})".format(
            p["path_with_namespace"], b.config.import_user_id))
        return users_api.get_user(
            b.config.import_user_id, b.config.destination_host, b.config.destination_token).json()["username"]
    else:
        return p_namespace


def get_dst_path_with_namespace(p):
    """
    Determine project path with namespace on destination

        :param p: The JSON object representing a GitLab project
        :return: Destination project path with namespace
    """
    return "{0}/{1}".format(get_user_project_namespace(p) if is_user_project(p) else get_project_namespace(p), p["path"])


def get_results(res):
    """
    Calculate number of total and successful export or import results.

        :param res: List of dicts containing export or import results
        :return: Dict of "Total" and "Successful" number of exports or imports
    """
    return {
        "Total": len(res),
        "Successful": len(res) - Counter(v for r in res for k, v in r.items() if not v).get(False, 0)
    }


# TODO: Add OR case for migrating from a parent group (future src_parent_id)
def is_top_level_group(g):
    """
    Determine if group is a top level or sub group.

        :param g: The JSON object representing a GitLab group
        :return: True if top-level-group, else False
    """
    return not g.get("parent_id", None)
