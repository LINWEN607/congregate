import json
from requests.exceptions import RequestException
from gitlab_ps_utils.misc_utils import get_timedelta, safe_json_response, strip_netloc
from gitlab_ps_utils.list_utils import remove_dupes
from gitlab_ps_utils.json_utils import json_pretty

from celery import shared_task
from congregate.helpers.base_class import BaseClass
from congregate.helpers.congregate_mdbc import CongregateMongoConnector, mongo_connection
from congregate.helpers.migrate_utils import get_full_path_with_parent_namespace, is_top_level_group, get_staged_groups, \
    find_user_by_email_comparison_without_id
from congregate.migration.gitlab.variables import VariablesClient
from congregate.migration.gitlab import constants
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.api.namespaces import NamespacesApi


class GroupsClient(BaseClass):
    def __init__(self):
        self.vars = VariablesClient()
        self.groups_api = GroupsApi()
        self.projects_api = ProjectsApi()
        self.namespaces_api = NamespacesApi()
        self.skip_group_members = False
        self.skip_project_members = False
        self.unique_groups = set()
        super().__init__()

    def traverse_groups(self, host, token, group):
        gid = group.get("id")
        if gid and gid not in self.unique_groups:
            mongo = CongregateMongoConnector()
            for k in constants.GROUP_KEYS_TO_IGNORE:
                group.pop(k, None)
            self.unique_groups.add(gid)

            # Save all group members as part of group metadata
            group["members"] = [] if self.skip_group_members else list(
                self.groups_api.get_all_group_members(gid, host, token))

            # Save all group projects ID references as part of group metadata
            # Only list direct projects to avoid overhead
            group["projects"] = []
            for project in self.groups_api.get_all_group_projects(gid, host, token, include_subgroups=False, with_shared=False):
                pid = project.get("id")
                group["projects"].append(pid)
                for k in constants.PROJECT_KEYS_TO_IGNORE:
                    project.pop(k, None)
                # Avoids having to list all parent group projects i.e. listing only projects
                project["members"] = [] if self.skip_project_members else list(
                    self.projects_api.get_members(pid, host, token))
                mongo.insert_data(f"projects-{strip_netloc(host)}", project)

            # Save all descendant groups ID references as part of group metadata
            group["desc_groups"] = []
            for g in self.groups_api.get_all_descendant_groups(gid, host, token):
                group["desc_groups"].append(g.get("id"))

            # Traverse subgroups
            for subgroup in self.groups_api.get_all_subgroups(
                    gid, host, token):
                self.log.debug("Traversing into subgroup")
                self.traverse_groups(
                    host, token, subgroup)
            mongo.insert_data(f"groups-{strip_netloc(host)}", group)
            mongo.close_connection()

    def retrieve_group_info(self, host, token, location="source", processes=None):
        prefix = location if location != "source" else ""

        if self.config.direct_transfer:
            if self.config.src_parent_group_path:
                traverse_groups_task.delay(host, token, safe_json_response(self.groups_api.get_group(
                    self.config.src_parent_id, host, token)))
            else:
                for group in self.groups_api.get_all_groups(
                        host, token):
                    traverse_groups_task.delay(host, token, group)
        else:
            if self.config.src_parent_group_path:
                self.multi.start_multi_process_stream_with_args(self.traverse_groups,
                                                                self.groups_api.get_all_subgroups(
                                                                    self.config.src_parent_id, host, token), host, token, processes=processes)
                self.traverse_groups(host, token, safe_json_response(self.groups_api.get_group(
                    self.config.src_parent_id, host, token)))
            else:
                self.multi.start_multi_process_stream_with_args(self.traverse_groups, self.groups_api.get_all_groups(
                    host, token), host, token, processes=processes)

    def append_groups(self, groups):
        with open(f"{self.app_path}/data/groups.json", "r") as f:
            group_file = json.load(f)
        rewritten_groups = {}
        for i, _ in enumerate(group_file):
            new_obj = group_file[i]
            group_name = group_file[i]["id"]
            rewritten_groups[group_name] = new_obj
        staged_groups = []
        for group in filter(None, groups):
            self.traverse_staging(int(group), rewritten_groups, staged_groups)

        with open(f"{self.app_path}/data/staged_groups.json", "w") as f:
            json.dump(remove_dupes(staged_groups), f, indent=4)

    def traverse_staging(self, gid, group_dict, staged_groups):
        if group_dict.get(gid, None):
            g = group_dict[gid]
            self.log.info("Staging {0} {1} (ID: {2})".format(
                "top-level group" if is_top_level_group(g) else "sub-group", g["full_path"], g["id"]))
            staged_groups.append(g)

    def is_group_non_empty(self, group):
        # Recursively look for any nested projects
        if group["projects"]:
            return True
        else:
            subgroups = self.groups_api.get_all_subgroups(
                group["id"],
                self.config.destination_host,
                self.config.destination_token)
            for sg in subgroups:
                resp = self.groups_api.get_group(
                    sg["id"],
                    self.config.destination_host,
                    self.config.destination_token)
                return self.is_group_non_empty(resp.json())

    def delete_groups(self, dry_run=True, skip_projects=False):
        for sg in get_staged_groups():
            # GitLab.com destination instances have a parent group
            dest_full_path = get_full_path_with_parent_namespace(
                sg["full_path"])
            self.log.info("Removing group {}".format(dest_full_path))
            resp = self.groups_api.get_group_by_full_path(
                dest_full_path,
                self.config.destination_host,
                self.config.destination_token)
            if resp is not None:
                if resp.status_code != 200:
                    self.log.info("Group {0} does not exist (status: {1})".format(
                        dest_full_path, resp.status_code))
                elif skip_projects and self.is_group_non_empty(resp.json()):
                    self.log.info(
                        "SKIP: Non-empty group {}".format(dest_full_path))
                elif not dry_run:
                    group = resp.json()
                    try:
                        if group.get("created_at", None):
                            if get_timedelta(
                                    group["created_at"]) < self.config.max_asset_expiration_time:
                                self.groups_api.delete_group(
                                    group["id"],
                                    self.config.destination_host,
                                    self.config.destination_token)
                            else:
                                self.log.info("Ignoring {0}. Group existed before {1} hours".format(
                                    group["full_path"], self.config.max_asset_expiration_time))
                    except RequestException as re:
                        self.log.error(
                            "Failed to remove group\n{0}\nwith error:\n{1}".format(json_pretty(sg), re))
            else:
                self.log.error(
                    "Failed to GET group {} by full_path".format(dest_full_path))

    def validate_staged_groups_schema(self):
        staged_groups = get_staged_groups()
        for g in staged_groups:
            self.log.info(g)
            if g.get("name") is None:
                self.log.warning("name is missing")
            if g.get("namespace") is None:
                self.log.warning("namespace is missing")
            if g.get("project_type") is None:
                self.log.warning("project_type is missing")
            if g.get("default_branch") is None:
                self.log.warning("default_branch is missing")
            if g.get("visibility") is None:
                self.log.warning("visibility is missing")
            if g.get("http_url_to_repo") is None:
                self.log.warning("http_url_to_repo is missing")
            if g.get("shared_runners_enabled") is None:
                self.log.warning("shared_runners_enabled is missing")
            if g.get("members") is None:
                self.log.warning("members is missing")
            if g.get("id") is None:
                self.log.warning("id is missing")
            if g.get("description") is None:
                self.log.warning("description is missing")

    def find_group_by_path(self, host, token, full_name_with_parent_namespace):
        """
        Search for an existing group by the full_path
        """
        self.log.info(
            f"Searching on destination for group {full_name_with_parent_namespace}")
        group = self.search_for_group_pr_namespace_by_full_name_with_parent_namespace(
            host, token, full_name_with_parent_namespace, True)
        if group is None:
            # As a sanity check, do namespaces, as well
            namespace = self.search_for_group_pr_namespace_by_full_name_with_parent_namespace(
                host, token, full_name_with_parent_namespace, False)
            if namespace is not None:
                self.log.info(
                    f"Group {full_name_with_parent_namespace} exists (namespace search)")
                return namespace
        else:
            self.log.info(
                f"Group {full_name_with_parent_namespace} exists (group search)")
            return group
        return {}

    def find_group_id_by_path(self, host, token,
                              full_name_with_parent_namespace):
        group = self.find_group_by_path(
            host, token, full_name_with_parent_namespace)
        if group is not None:
            return group.get("id")
        return None

    def search_for_group_pr_namespace_by_full_name_with_parent_namespace(
            self, host, token, full_name_with_parent_namespace, is_group):
        resp = None
        if is_group:
            resp = self.groups_api.get_group_by_full_path(
                full_path=full_name_with_parent_namespace, host=host, token=token)
        else:
            resp = self.namespaces_api.get_namespace_by_full_path(
                full_path=full_name_with_parent_namespace, host=host, token=token)
        if resp.status_code == 200:
            return safe_json_response(resp)
        return None

    def add_members_to_destination_group(self, host, token, group_id, members):
        result = {}
        self.log.info(
            f"Adding {len(members)} member{'s' if len(members) > 1 else ''} to Group ID {group_id}")
        for member in members:
            if email := member.get("email"):
                user_id_req = find_user_by_email_comparison_without_id(email)
                member["user_id"] = user_id_req.get(
                    "id") if user_id_req else None
                result[email] = False
                if member.get("user_id"):
                    if safe_json_response(self.groups_api.add_member_to_group(group_id, host, token, member)):
                        result[email] = True
                    else:
                        self.log.error(
                            f"Failed to add user '{email}' to group {group_id}")
                else:
                    self.log.warning(
                        f"Failed to find user '{email}' on destination")
        return result

    def find_and_stage_group_bulk_entities(self, groups):
        entities, result = [], []
        namespace = self.config.dstn_parent_group_path or ""
        for g in groups:
            full_path = g["full_path"]
            full_path_with_parent_namespace = get_full_path_with_parent_namespace(
                full_path)
            dst_grp = self.find_group_by_path(
                self.config.destination_host, self.config.destination_token, full_path_with_parent_namespace)
            dst_gid = dst_grp.get("id") if dst_grp else None
            if dst_gid:
                self.log.info(
                    f"Group {full_path} (ID: {dst_gid}) already exists on destination")
                result.append({full_path_with_parent_namespace: dst_gid})
            else:
                result.append({full_path_with_parent_namespace: False})
                entities.append({
                    "source_full_path": full_path,
                    "source_type": "group_entity",
                    "destination_name": g["name"],
                    "destination_namespace": namespace})
        return entities, result


@shared_task(name='traverse-groups')
@mongo_connection
def traverse_groups_task(host, token, group, mongo=None):
    gc = GroupsClient()
    gid = group.get("id")
    if gid and gid not in gc.unique_groups:
        for k in constants.GROUP_KEYS_TO_IGNORE:
            group.pop(k, None)
        gc.unique_groups.add(gid)

        # Save all group members as part of group metadata
        group["members"] = [] if gc.skip_group_members else list(
            gc.groups_api.get_all_group_members(gid, host, token))

        # Save all group projects ID references as part of group metadata
        # Only list direct projects to avoid overhead
        group["projects"] = []
        for project in gc.groups_api.get_all_group_projects(gid, host, token, include_subgroups=False, with_shared=False):
            pid = project.get("id")
            group["projects"].append(pid)
            for k in constants.PROJECT_KEYS_TO_IGNORE:
                project.pop(k, None)
            # Avoids having to list all parent group projects i.e. listing only projects
            project["members"] = [] if gc.skip_project_members else list(
                gc.projects_api.get_members(pid, host, token))
            mongo.insert_data(f"projects-{strip_netloc(host)}", project)

        # Save all descendant groups ID references as part of group metadata
        group["desc_groups"] = []
        for g in gc.groups_api.get_all_descendant_groups(gid, host, token):
            group["desc_groups"].append(g.get("id"))

        # Traverse subgroups
        for subgroup in gc.groups_api.get_all_subgroups(
                gid, host, token):
            gc.log.debug(
                f"Traversing into subgroup {subgroup.get('full_path')}")
            traverse_groups_task.delay(
                host, token, subgroup)
        mongo.insert_data(f"groups-{strip_netloc(host)}", group)
