from congregate.helpers import base_module as b
from congregate.migration.gitlab.groups import GroupsClient as groupsClient
from congregate.migration.gitlab.users import UsersApi as usersApi

groups = groupsClient()
users_api = usersApi()


def get_failed_update_from_results(results):
    return [str(x["filename"]).lower() for x in results
            if x.get("updated", None) is not None
            and x.get("filename", None) is not None
            and not x["updated"]]


def get_staged_projects_without_failed_update(staged_projects, failed_update):
    """
    :param staged_projects: The current list of staged projects
    :param failed_update: A list of project export filenames
    :return: A new staged_projects list removing those that failed update
    """
    return [p for p in staged_projects if get_project_filename(p) not in failed_update]


def get_project_filename(p):
    """
    Filename can be namespace and project-type dependent
    :param p:
    :return:
    """
    if p.get("name", None) is not None and p.get("namespace", None) is not None:
        namespace = str(get_project_namespace(p)).lower()
        return "{0}_{1}.tar.gz".format(namespace.lower(), str(p["name"]).lower())
    return ""


def get_project_namespace(project):
    """
    If this is a user project, the namespace == username
    :param project:
    :return:
    """
    if b.config.parent_id is not None and project["project_type"] != "user":
        parent_namespace = groups.groups_api.get_group(
            b.config.parent_id, b.config.destination_host, b.config.destination_token).json()
        return "{0}/{1}".format(parent_namespace["path"], project["namespace"])
    return project["namespace"]


def get_is_user_project(project):
    """
    Determine if a passed staged_project object (json) is a user project or not
    :param self:
    :param project: The JSON object representing a GitLab project
    :return: True if a user project, else False
    """
    return project.get("project_type", None) is not None and project["project_type"] == "user"


def get_member_id_for_user_project(project):
    """
    This assumes that the user already exists in the destination system and that userid rewrites have occurred.
    Otherwise, you will be trying to use a source id for a destination user
    :param project:
    :return: The destination member id
    """
    try:
        # Determine if the project should be under a single user or group
        for member in project["members"]:
            if project["namespace"] == member["username"]:

                return member["id"]
    except Exception as e:
        b.log.error(
            "Could not find member id for user project {0} with error {1}"
            .format(project, e)
        )
        # We don't do a lot of raise, but it's honestly getting to the point where I want to just fail rather
        # than try and figure out if we should continue or not
        raise e
