from datetime import datetime
from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import is_dot_com
from congregate.migration.gitlab.groups import GroupsClient as groupsClient
from congregate.migration.gitlab.users import UsersApi as usersApi


b = BaseClass()
groups = groupsClient()
users_api = usersApi()


def get_failed_export_from_results(results):
    return [str(x["filename"]).lower() for x in results
            if x.get("exported", None) is not None
            and x.get("filename", None) is not None
            and not x["exported"]]


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
    if b.config.parent_id is not None and p["project_type"] != "user":
        return "{0}/{1}".format(b.config.parent_group_path, p["namespace"])
    return p["namespace"]


def is_user_project(p):
    """
    Determine if a passed staged_project object (json) is a user project or not

        :param p: The JSON object representing a GitLab project
        :return: True if a user project, else False
    """
    return p.get("project_type", None) is not None and p["project_type"] == "user"


def get_user_project_namespace(p):
    """
    Determine if user project should be imported under the import_user (.com or self-managed root) or member namespace (self-managed)

        :param p: The JSON object representing a GitLab project
        :param: namespace:
        :return: Destination user project namespace
    """
    if is_dot_com(b.config.destination_host) or p["namespace"] == "root":
        b.log.info("Assigning user project {0} to import user id (ID: {1})".format(
            p["path_with_namespace"], b.config.import_user_id))
        return users_api.get_user(
            b.config.import_user_id, b.config.destination_host, b.config.destination_token).json()["username"]
    else:
        return p["namespace"]

def get_timedelta(timestamp):
    """
    Get timedelta between provided timestampe and current time

        :param timestamp: A timestamp string
        :return: timedelta between provided timestamp and datetime.now() in hours
    """
    created_at = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%SZ')
    now = datetime.now()
    return (now - created_at).days * 24

