import json
from requests.exceptions import RequestException

from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import remove_dupes, get_timedelta, json_pretty, safe_json_response
from congregate.helpers.migrate_utils import get_full_path_with_parent_namespace, is_top_level_group
from congregate.migration.gitlab.variables import VariablesClient
from congregate.migration.gitlab.badges import BadgesClient
from congregate.migration.gitlab.users import UsersClient
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.api.namespaces import NamespacesApi


class GroupsClient(BaseClass):
    def __init__(self):
        self.vars = VariablesClient()
        self.groups_api = GroupsApi()
        self.badges = BadgesClient()
        self.users = UsersClient()
        self.namespaces_api = NamespacesApi()
        self.group_id_mapping = {}
        super(GroupsClient, self).__init__()

    def get_staged_groups(self):
        with open("{}/data/staged_groups.json".format(self.app_path), "r") as f:
            return json.load(f)

    def traverse_groups(self, base_groups, transient_list, host, token, parent_group=None):
        for group in base_groups:
            group.pop("web_url")
            group.pop("full_name")
            try:
                group.pop("ldap_cn")
                group.pop("ldap_access")
            except KeyError as ke:
                self.log.error(
                    "Failed to pop group keys 'ldap_cn' and/or 'ldap_access', with error:\n{}".format(ke))
            group_id = group["id"]
            group["members"] = [m for m in self.groups_api.get_all_group_members(
                group_id, host, token) if m["id"] != 1]
            group["projects"] = list(self.groups_api.get_all_group_projects(
                group_id, host, token, with_shared=False))
            transient_list.append(group)
            for subgroup in self.groups_api.get_all_subgroups(group_id, host, token):
                if len(subgroup) > 0:
                    parent_group = transient_list[-1]
                    self.log.debug("traversing into a subgroup")
                    self.traverse_groups(
                        [subgroup], transient_list, host, token, parent_group)
            parent_group = None

    def retrieve_group_info(self, host, token, location="source", top_level_group=False):
        prefix = ""
        if location != "source":
            prefix = location

        if not top_level_group:
            if self.config.src_parent_group_path:
                groups = list(self.groups_api.get_all_subgroups(
                    self.config.src_parent_id, host, token))
                groups.append(self.groups_api.get_group(
                    self.config.src_parent_id, host, token).json())
            else:
                groups = list(self.groups_api.get_all_groups(
                    host, token))
        else:
            if self.config.dstn_parent_id is not None:
                groups = [self.groups_api.get_group(self.config.dstn_parent_id, self.config.destination_host,
                                                    self.config.destination_token).json()]
                prefix += str(self.config.dstn_parent_id)
            else:
                self.log.info("No parent ID found")
                return None

        transient_list = []
        self.traverse_groups(groups, transient_list, host, token)
        self.create_groups_json(transient_list, prefix=prefix)
        return transient_list

    def create_groups_json(self, groups, prefix=""):
        file_path = '%s/data/%sgroups.json' % (self.app_path, prefix)
        with open(file_path, "w") as f:
            json.dump(remove_dupes(groups), f, indent=4)
        return file_path

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
        staged_groups = self.get_staged_groups()
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
                            if get_timedelta(group["created_at"]) < self.config.max_asset_expiration_time:
                                self.groups_api.delete_group(
                                    group["id"],
                                    self.config.destination_host,
                                    self.config.destination_token)
                            else:
                                self.log.info("Ignoring {0}. Group existed before {1} hours".format(
                                    group["full_path"], self.config.max_asset_expiration_time))
                    except RequestException, re:
                        self.log.error(
                            "Failed to remove group\n{0}\nwith error:\n{1}".format(json_pretty(sg), re))
            else:
                self.log.error(
                    "Failed to GET group {} by full_path".format(dest_full_path))

    def find_all_non_private_groups(self):
        groups_to_change = []
        transient_list = []
        parent_group = [self.groups_api.get_group(
            self.config.dstn_parent_id,
            self.config.destination_host,
            self.config.destination_token).json()]
        self.traverse_groups(
            parent_group,
            transient_list,
            self.config.destination_host,
            self.config.destination_token)
        count = 0

        for group in transient_list:
            print "{0}, {1}".format(group["name"], group["visibility"])
            if group["visibility"] != "private":
                self.log.info("Group {0} has {1} visibility".format(
                    group["name"], group["visibility"]))
                count += 1
                groups_to_change.append(group)
        self.log.info("Non-private groups ({0}):\n{1}".format(
            len(groups_to_change), "\n".join(g for g in groups_to_change)))

        return groups_to_change

    def make_all_internal_groups_private(self):
        groups = self.find_all_non_private_groups()
        ids = []
        for group in groups:
            try:
                self.log.debug("Searching for existing %s" % group["name"])
                for proj in self.groups_api.search_for_group(self.config.destination_host,
                                                             self.config.destination_token, group['name']):
                    if proj["name"] == group["name"]:
                        if "%s" % group["path"].lower() in proj["full_path"].lower():
                            # self.log.info("Migrating variables for %s" % proj["name"])
                            ids.append(proj["id"])
                            print "%s: %s" % (
                                proj["full_path"], proj["visibility"])
                            break
            except IOError, e:
                self.log.error(e)
        print ids

    def validate_staged_groups_schema(self):
        staged_groups = self.get_staged_groups()
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

    def find_group_id_by_path(self, host, token, full_name_with_parent_namespace):
        group = self.find_group_by_path(
            host, token, full_name_with_parent_namespace)
        if group is not None:
            return group.get("id", None)
        return None

    def search_for_group_pr_namespace_by_full_name_with_parent_namespace(self, host, token, full_name_with_parent_namespace, is_group):
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
        for member in members:
            member["user_id"] = self.users.find_user_by_email_comparison_without_id(member["email"])["id"]
            if member.get("user_id"):
                result[member["email"]] = False
                resp = safe_json_response(self.groups_api.add_member_to_group(group_id, host, token, member))
                if resp:
                    result[member["email"]] = True
        return result