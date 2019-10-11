from congregate.helpers import base_module as b
from congregate.migration.gitlab.groups import GroupsClient as groupsClient
groups = groupsClient()


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
    if b.config.parent_id is not None and project["project_type"] != "user":
        parent_namespace = groups.groups_api.get_group(
            b.config.parent_id, b.config.destination_host, b.config.destination_token).json()
        return "{0}/{1}".format(parent_namespace["path"], project["namespace"])
    return project["namespace"]
