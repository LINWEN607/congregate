import json
from time import sleep
from requests.exceptions import RequestException

from congregate.helpers.base_class import BaseClass
from congregate.helpers.mdbc import MongoConnector
from congregate.helpers.misc_utils import get_timedelta, safe_json_response, strip_protocol
from congregate.helpers.list_utils import remove_dupes
from congregate.helpers.migrate_utils import get_full_path_with_parent_namespace, is_top_level_group, get_staged_groups, find_user_by_email_comparison_without_id
from congregate.helpers.json_utils import json_pretty, write_json_to_file
from congregate.migration.gitlab.variables import VariablesClient
from congregate.migration.gitlab.badges import BadgesClient
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.api.namespaces import NamespacesApi


class GroupsClient(BaseClass):
    def __init__(self):
        self.vars = VariablesClient()
        self.groups_api = GroupsApi()
        self.badges = BadgesClient()
        self.namespaces_api = NamespacesApi()
        self.group_id_mapping = {}
        super().__init__()

    def traverse_groups(self, host, token, group):
        mongo = MongoConnector()
        if group_id := group.get("id", None):
            keys_to_ignore = [
                "web_url",
                "full_name",
                "ldap_cn",
                "ldap_access"
            ]
            for k in keys_to_ignore:
                group.pop(k, None)
            group["members"] = [m for m in self.groups_api.get_all_group_members(
                group_id, host, token) if m["id"] != 1]
            group["projects"] = list(self.groups_api.get_all_group_projects(
                group_id, host, token, with_shared=False))
            for subgroup in self.groups_api.get_all_subgroups(
                    group_id, host, token):
                self.log.debug("traversing into a subgroup")
                self.traverse_groups(
                    host, token, subgroup)
            mongo.insert_data(
                f"groups-{strip_protocol(host)}", group)

        mongo.close_connection()

    def retrieve_group_info(
            self, host, token, location="source", processes=None):
        prefix = ""
        if location != "source":
            prefix = location

        if self.config.src_parent_group_path:
            self.multi.start_multi_process_stream_with_args(self.traverse_groups,
                                                 self.groups_api.get_all_subgroups(
                                                     self.config.src_parent_id, host, token), host, token, processes=processes)
            self.traverse_groups(host, token, safe_json_response(self.groups_api.get_group(
                self.config.src_parent_id, host, token)))
        else:
            self.multi.start_multi_process_stream_with_args(self.traverse_groups,
                                                 self.groups_api.get_all_groups(
                                                     host, token), host, token, processes=processes)

    def remove_import_user(self, gid):
        try:
            self.log.info("Removing import user (ID: {0}) from group (ID: {1})"
                          .format(self.config.import_user_id, gid))
            self.groups_api.remove_member(
                gid,
                self.config.import_user_id,
                self.config.destination_host,
                self.config.destination_token
            )
        except RequestException as re:
            self.log.error(
                "Failed to remove import user (ID: {0}) from group (ID: {1}), with error:\n{2}".format(self.config.import_user_id, gid, re))

    def append_groups(self, groups):
        with open("{}/data/groups.json".format(self.app_path), "r") as f:
            group_file = json.load(f)
        rewritten_groups = {}
        for i, _ in enumerate(group_file):
            new_obj = group_file[i]
            group_name = group_file[i]["id"]
            rewritten_groups[group_name] = new_obj
        staged_groups = []
        for group in filter(None, groups):
            self.traverse_staging(int(group), rewritten_groups, staged_groups)

        with open("%s/data/staged_groups.json" % self.app_path, "w") as f:
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
        staged_groups = get_staged_groups()
        for sg in staged_groups:
            # SaaS destination instances have a parent group
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
            if g.get("name", None) is None:
                self.log.warning("name is missing")
            if g.get("namespace", None) is None:
                self.log.warning("namespace is missing")
            if g.get("project_type", None) is None:
                self.log.warning("project_type is missing")
            if g.get("default_branch", None) is None:
                self.log.warning("default_branch is missing")
            if g.get("visibility", None) is None:
                self.log.warning("visibility is missing")
            if g.get("http_url_to_repo", None) is None:
                self.log.warning("http_url_to_repo is missing")
            if g.get("shared_runners_enabled", None) is None:
                self.log.warning("shared_runners_enabled is missing")
            if g.get("members", None) is None:
                self.log.warning("members is missing")
            if g.get("id", None) is None:
                self.log.warning("id is missing")
            if g.get("description", None) is None:
                self.log.warning("description is missing")

    def find_group_by_path(self, host, token, full_name_with_parent_namespace):
        """
        Search for an existing group by the full_path
        """
        group = self.search_for_group_pr_namespace_by_full_name_with_parent_namespace(
            host, token, full_name_with_parent_namespace, True)
        if group is None:
            # As a sanity check, do namespaces, as well
            namespace = self.search_for_group_pr_namespace_by_full_name_with_parent_namespace(
                host, token, full_name_with_parent_namespace, False)
            if namespace is not None:
                self.log.info("Group {} exists (namespace search)".format(
                    full_name_with_parent_namespace))
                return namespace
        else:
            self.log.info("Group {} exists (group search)".format(
                full_name_with_parent_namespace))
            return group
        return None

    def find_group_id_by_path(self, host, token,
                              full_name_with_parent_namespace):
        group = self.find_group_by_path(
            host, token, full_name_with_parent_namespace)
        if group is not None:
            return group.get("id", None)
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
            return resp.json()
        return None

    def add_members_to_destination_group(self, host, token, group_id, members):
        result = {}
        self.log.info(
            f"Adding members to Group ID {group_id}:\n{json_pretty(members)}")
        for member in members:
            if member.get("email", None):
                user_id_req = find_user_by_email_comparison_without_id(
                    member["email"])
                member["user_id"] = user_id_req.get(
                    "id", None) if user_id_req else None
                result[member["email"]] = False
                if member.get("user_id"):
                    resp = safe_json_response(
                        self.groups_api.add_member_to_group(group_id, host, token, member))
                    if resp:
                        result[member["email"]] = True
        return result

    def wait_for_parent_group_creation(self, group):
        timeout = 0
        wait_time = self.config.export_import_status_check_time
        ppath = group["full_path"].rsplit("/", 1)[0]
        name = group["name"]
        pnamespace = self.namespaces_api.get_namespace_by_full_path(
            ppath, self.config.destination_host, self.config.destination_token)
        while pnamespace.status_code != 200:
            self.log.info(
                f"Waiting {self.config.export_import_status_check_time} seconds to create parent group {ppath} for group {name}")
            timeout += wait_time
            sleep(wait_time)
            if timeout > wait_time * 10:
                self.log.error(
                    f"Time limit exceeded waiting for parent group {ppath} to create for group {name}")
                return None
            pnamespace = self.namespaces_api.get_namespace_by_full_path(
                ppath, self.config.destination_host, self.config.destination_token)
        return pnamespace
