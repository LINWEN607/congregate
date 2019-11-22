import json
from os import path
from requests.exceptions import RequestException

from congregate.helpers.base_class import BaseClass
from congregate.helpers import api, misc_utils
from congregate.migration.gitlab.variables import VariablesClient as vars_client
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.helpers.exceptions import ConfigurationException


class GroupsClient(BaseClass):
    def __init__(self):
        self.vars = vars_client()
        self.groups_api = GroupsApi()
        self.group_id_mapping = {}
        super(GroupsClient, self).__init__()

    def get_staged_groups(self):
        with open("{}/data/staged_groups.json".format(self.app_path), "r") as f:
            return json.load(f)

    def find_parent_group_path(self):
        '''
            Gate used to find an existing and valid parent group path

            :raises: ConfigurationException
        '''
        try:
            if self.config.parent_id is not None:
                return self.groups_api.get_group(self.config.parent_id, self.config.destination_host,
                                                 self.config.destination_token).json()["full_path"]
            else:
                return ""
        except ConfigurationException, e:
            self.log.error(e)
            exit(1)

    def traverse_groups(self, base_groups, transient_list, host, token, parent_group=None):
        if parent_group is not None:
            parent_group["child_ids"] = []
        for group in base_groups:
            group.pop("web_url")
            group.pop("full_name")
            try:
                group.pop("ldap_cn")
                group.pop("ldap_access")
            except KeyError:
                pass
            group_id = group["id"]
            members = list(self.groups_api.get_all_group_members(group_id, host, token))
            group["members"] = members
            transient_list.append(group)
            if parent_group is not None:
                parent_group["child_ids"].append(group["id"])
            for subgroup in self.groups_api.get_all_subgroups(group_id, host, token):
                if len(subgroup) > 0:
                    parent_group = transient_list[-1]
                    self.log.debug("traversing into a subgroup")
                    self.traverse_groups(
                        [subgroup], transient_list, host, token, parent_group)
            parent_group = None

    def retrieve_group_info(self, host, token, location="source", top_level_group=False, quiet=False):
        prefix = ""
        if location != "source":
            prefix = location

        if not top_level_group:
            groups = list(self.groups_api.get_all_groups(
                host, token))
        else:
            if self.config.parent_id is not None:
                groups = [self.groups_api.get_group(self.config.parent_id, self.config.destination_host,
                                                    self.config.destination_token).json()]
                prefix += str(self.config.parent_id)
                print groups
            else:
                self.log.info("No parent ID found")
                return None

        transient_list = []
        self.traverse_groups(groups, transient_list,
                             host, token)

        self.create_groups_json(transient_list, prefix=prefix)
        if not quiet:
            self.log.info(
                "Retrieved %d groups. Check groups.json to see all retrieved groups" % len(groups))

        return transient_list

    def create_groups_json(self, groups, prefix=""):
        file_path = '%s/data/%sgroups.json' % (self.app_path, prefix)
        with open(file_path, "w") as f:
            json.dump(groups, f, indent=4)
        return file_path

    def migrate_group_info(self, dry_run):
        if not path.isfile("%s/data/groups.json" % self.app_path):
            self.retrieve_group_info(self.config.source_host, self.config.source_token)
        staged_groups = self.get_staged_groups()
        rewritten_groups = {}
        for i in range(len(staged_groups)):
            new_obj = staged_groups[i]
            group_id = staged_groups[i]["id"]
            rewritten_groups[group_id] = new_obj

        self.group_id_mapping = {}
        parent_id = self.config.parent_id

        if not dry_run:
            # Update parent group notification level
            if parent_id:
                current_level = self.get_current_group_notifications(parent_id)
                self.update_group_notifications(parent_id)
                self.traverse_and_migrate(staged_groups, rewritten_groups, dry_run)
                self.reset_group_notifications(parent_id, current_level)
            else:
                self.traverse_and_migrate(staged_groups, rewritten_groups, dry_run)

            # Migrate group badges
            self.migrate_group_badges()
        else:
            self.traverse_and_migrate(staged_groups, rewritten_groups, dry_run)

    def migrate_group_badges(self):
        for old_id, new_id in self.group_id_mapping.items():
            badges = self.groups_api.get_all_group_badges(self.config.source_host, self.config.source_token, old_id)
            if badges:
                badges = list(badges)
                if badges:
                    self.log.info("Migrating source group ID {0} badges".format(old_id))
                    self.add_badges(new_id, self.find_parent_group_path(), badges)
                else:
                    self.log.info("Group {} has no group badges".format(old_id))
            else:
                self.log.warn("Failed to retrieve group badges for {0}, with response:\n{1}".format(old_id, badges))

    def traverse_and_migrate(self, groups, rewritten_groups, dry_run=False):
        count = 0
        dest_groups = []
        for group in groups:
            parent_id = None
            self.log.info("Migrating %s %d/%d" %
                          (group["name"], count, len(group)))
            if group.get("id", None) is not None:
                # NOTE: Is this still needed?
                # if rewritten_groups is not None:
                #     has_children = "child_ids" in rewritten_groups.get(group["id"], None)
                group_id = group["id"]
                # group.pop("id")
                members = group["members"]

                if self.config.make_visibility_private is not None:
                    if self.config.make_visibility_private is True:
                        group["visibility"] = "private"

                if group.get("parent_namespace", None) is not None:
                    self.log.info("Retrieved parent namespace of {0}".format(group["parent_namespace"]))
                    found = False
                    if rewritten_groups.get(group["parent_id"], None) is not None:
                        parent_id = rewritten_groups[group["parent_id"]]["id"]
                    elif group.get("old_parent_id", None) is not None:
                        if rewritten_groups.get(group["old_parent_id"], None) is not None:
                            parent_id = rewritten_groups[group["old_parent_id"]]["id"]

                    # search = api.search(self.config.destination_host, self.config.destination_token, "groups", group["parent_namespace"])
                    if parent_id is not None:
                        if rewritten_groups[parent_id].get("new_parent_id", None) is not None:
                            group["parent_id"] = rewritten_groups[parent_id]["new_parent_id"]
                            found = True
                        else:
                            for s in self.groups_api.search_for_group(
                                group["parent_namespace"],
                                self.config.destination_host,
                                self.config.destination_token):
                                if rewritten_groups.get(parent_id, None) is not None:
                                    if s["full_path"].lower() == rewritten_groups[group["id"]][
                                        "full_parent_namespace"].lower():
                                        rewritten_groups[parent_id]["new_parent_id"] = s["id"]
                                        group["parent_id"] = s["id"]
                                        found = True
                                        break
                        if found is False:
                            self.traverse_and_migrate(
                                [rewritten_groups[parent_id]], rewritten_groups, dry_run)
                            # search = api.search(self.config.destination_host, self.config.destination_token, "groups", group["parent_namespace"])
                            for s in self.groups_api.search_for_group(
                                group["parent_namespace"],
                                self.config.destination_host,
                                self.config.destination_token):
                                if rewritten_groups.get(parent_id, None) is not None:
                                    if s["full_path"].lower() == rewritten_groups[parent_id]["full_path"].lower():
                                        group["parent_id"] = s["id"]
                                        found = True
                                        break
                    else:
                        if self.config.parent_id is not None:
                            group["parent_id"] = self.config.parent_id
                        else:
                            group["parent_id"] = None
                    # group.pop("parent_namespace")
                else:
                    if self.config.parent_id is not None:
                        group["parent_id"] = self.config.parent_id
                    else:
                        self.log.info("Parent namespace is empty")

                # group.pop("full_path")

                new_group_id = None
                if group_id in rewritten_groups:
                    try:
                        group_without_id = group.copy()
                        group_without_id.pop("id")
                        group_without_id.pop("full_path")
                        group_without_id.pop("members")
                        full_parent_namespace = ""
                        if group_without_id.get("parent_namespace", None) is not None:
                            self.log.info("Popping parent namespace of {0}".format(group_without_id["parent_namespace"]))
                            group_without_id.pop("parent_namespace")
                        if group_without_id.get("full_parent_namespace", None) is not None:
                            full_parent_namespace = group_without_id["full_parent_namespace"]
                            self.log.info("Popping full parent namespace of {0}".format(full_parent_namespace))
                            group_without_id.pop("full_parent_namespace")

                        response = None
                        if not dry_run:
                            self.log.info("Creating group with JSON {0}".format(group_without_id))
                            response = self.groups_api.create_group(
                                self.config.destination_host,
                                self.config.destination_token,
                                group_without_id
                            ).json()
                        else:
                            group_without_id.setdefault("members", []).append(self.add_members(members, new_group_id, dry_run))
                            dest_groups.append(group_without_id)

                        if isinstance(response, dict):
                            if response.get("message", None) is not None:
                                if "Failed to save group" in response["message"]:
                                    self.log.info(
                                        "Group already exists. Searching for group ID")
                                    # new_group = api.search(self.config.destination_host, self.config.destination_token, 'groups', group['path'])

                                    # if new_group is not None and len(new_group) > 0:
                                    found_group = False
                                    if group["parent_id"] is not None:
                                        for ng in self.groups_api.get_all_subgroups(
                                                group["parent_id"],
                                                self.config.destination_host,
                                                self.config.destination_token):
                                            if ng["full_path"] == full_parent_namespace:
                                                new_group_id = ng["id"]
                                                print new_group_id
                                                self.log.info("Group found")
                                                found_group = True
                                                break
                                            if found_group is True:
                                                break
                                    else:
                                        for ng in self.groups_api.search_for_group(
                                                group["name"],
                                                self.config.destination_host,
                                                self.config.destination_token
                                        ):
                                            if ng["full_path"] == full_parent_namespace:
                                                new_group_id = ng["id"]
                                                print new_group_id
                                                self.log.info("Group found")
                                                found_group = True
                                                break
                                            if found_group is True:
                                                break

                                else:
                                    self.log.info("Failed to save group")
                            else:
                                new_group_id = response["id"]
                        elif isinstance(response, list):
                            new_group_id = response[0]["id"]
                    except RequestException, e:
                        self.log.info("Group already exists")
                    if new_group_id is None:
                        new_group = api.search(
                            self.config.destination_host, self.config.destination_token, 'groups', group['path'])
                        if new_group is not None and len(new_group) > 0:
                            for ng in new_group:
                                if ng["name"] == group["name"]:
                                    if ng["parent_id"] == group["parent_id"] == self.config.parent_id:
                                        new_group_id = ng["id"]
                                        self.log.info("New group {0} found".format(new_group_id))
                                        break

                    if new_group_id:
                        #   177
                        current_level = self.get_current_group_notifications(new_group_id)
                        if not current_level:
                            self.log.error(
                                "Skipping adding users for new group id {0}, notification level could not be determined".format(
                                    new_group_id))
                            continue

                        # Update group notifications based
                        put_response = self.update_group_notifications(new_group_id)
                        if not put_response:
                            self.log.error(
                                "Skipping adding users for new group id {0}, notification level could not be updated ({1})".format(
                                    new_group_id,
                                    put_response.status_code)
                            )
                            continue

                        self.group_id_mapping[group_id] = new_group_id

                        self.vars.migrate_variables(
                            new_group_id, group_id, "group")

                        self.add_members(members, new_group_id, dry_run)

                        self.remove_import_user(new_group_id)

                        self.reset_group_notifications(new_group_id, current_level)

                        # NOTE: Is this still needed?
                        # if has_children:
                        #     subgroup = []
                        #     self.log.info(group["child_ids"])
                        #     for sub in group["child_ids"]:
                        #         # rewritten_groups.pop(group_id, None)
                        #         self.log.info(rewritten_groups.get(sub))
                        #         self.log.info(rewritten_groups.keys())
                        #         if rewritten_groups.get(sub) is not None:
                        #             sub_group = rewritten_groups.get(sub)
                        #             sub_group["old_parent_id"] = sub_group["parent_id"]
                        #             sub_group["parent_id"] = new_group_id
                        #             subgroup.append(sub_group)
                        #     self.log.info(subgroup)
                        #     traverse_and_migrate(subgroup, rewritten_groups)
                        # rewritten_groups.pop(group_id, None)
            else:
                print "Leaving recursion"
            count += 1
        if dry_run:
            self.log.info("Outputing various GROUP migration data to dry_run_group_migration.json")
            misc_utils.migration_dry_run(
                "group", {
                    "parent_id": self.config.parent_id,
                    "dest_groups": dest_groups,
                    "rewritten_groups": rewritten_groups})

    def add_members(self, members, group_id, dry_run=False):
        new_members = []
        for member in members:
            # If we do not keep_blocked_users skip adding
            if member.get("state", None) is not None \
                    and str(member["state"]).lower() == "blocked" \
                    and not self.config.keep_blocked_users:
                self.log.info("Skipping blocked group member {}".format(member))
                continue
            new_member = {
                "user_id": member["id"],
                "access_level": int(member["access_level"])
            }
            new_members.append(new_member)
            if not dry_run:
                try:
                    self.log.info("Adding member {0} to new group ID {1}".format(member, group_id))
                    self.groups_api.add_member_to_group(
                        group_id,
                        self.config.destination_host,
                        self.config.destination_token,
                        new_member)
                except RequestException, e:
                    self.log.error("Failed to add member {0} to new group ID {1}, with error:\n{2}"
                        .format(member, group_id, e))
        return new_members

    def remove_import_user(self, group_id):
        try:
            self.log.info("Removing import (root) user from group")
            self.groups_api.remove_member(
                group_id,
                int(self.config.import_user_id),
                self.config.destination_host,
                self.config.destination_token
            )
        except RequestException, e:
            self.log.error("Failed to remove import (root) user from group, with error:\n{}".format(e))

    def get_current_group_notifications(self, new_group_id):
        """
        Retrieve the current notification level for a group
        :param new_group_id: The group id to get the notification for
        :return: The string representation of the notification level, or None
        """
        #  177
        try:
            get_response = self.groups_api.get_notification_level(
                self.config.destination_host,
                self.config.destination_token,
                new_group_id
            )
            if get_response is not None and get_response.status_code == 200 and get_response.json().get("level", None):
                self.log.info("Retrieved notification settings for group {}".format(new_group_id))
                return get_response.json()["level"]
            else:
                self.log.error("Could not get group {} notification settings".format(new_group_id))
        except Exception as e:
            self.log.error("Exception in get_current_group_notifications of {} ".format(e))

        return None

    def update_group_notifications(self, new_group_id):
        """
        Update notification level for a group
        :param new_group_id: The group id to update notifications for
        :return: The put_response object or None on error
        """
        # 177 - Update group to turn off notifications while we add users
        try:
            level = self.config.notification_level.lower()
            put_response = self.groups_api.update_notification_level(
                self.config.destination_host,
                self.config.destination_token,
                new_group_id,
                level
            )
            if put_response is not None and put_response.status_code == 200:
                self.log.info("Updated group {0} notification level to {1}".format(new_group_id, level))
                return put_response
            else:
                self.log.error("Failed to update group {0} notification level to {1}, due to:\n{2}"
                    .format(new_group_id, level, put_response))
        except Exception as e:
            self.log.error("Exception in update_group_notifications of {0} ".format(e))

        return None

    def reset_group_notifications(self, new_group_id, level):
        """
        Reset notifications for a group
        :param new_group_id: The group id to disable notifications for
        :param level The level to set the notifications for the group to. Generally the level retrieved with a call to
                get_current_group_notifications
        :return: The put_response object or None on error
        """
        # 177 - Update group to turn off notifications while we add users
        try:
            put_response = self.groups_api.update_notification_level(
                self.config.destination_host,
                self.config.destination_token,
                new_group_id,
                level
            )
            if put_response is not None and put_response.status_code == 200:
                self.log.info("Reset group {0} notification level to {1}".format(new_group_id, level))
                return put_response
            else:
                self.log.error("Failed to reset group {0} notification level to {1}, due to:\n{2}"
                    .format(new_group_id, level, put_response))
        except Exception as e:
            self.log.error("Exception in reset_group_notifications of {0} ".format(e))

        return None

    def update_members(self):
        staged_groups = self.get_staged_groups()
        for group in staged_groups:
            # TODO: Change this to a search check. This assumes the instance doesn't contain various nested groups with the same name
            new_group_id = api.generate_get_request(
                self.config.destination_host, self.config.destination_token, 'groups',
                params={'search': group['name']}).json()

            members = group["members"]
            for member in members:
                new_member = {
                    "user_id": member["id"],
                    "access_level": int(member["access_level"])
                }

                try:
                    self.groups_api.add_member_to_group(
                        new_group_id,
                        self.config.destination_host,
                        self.config.destination_token,
                        new_member)
                except RequestException, e:
                    self.log.error(e)

    def append_groups(self, groups):
        with open("%s/data/groups.json" % self.app_path, "r") as f:
            group_file = json.load(f)
        rewritten_groups = {}
        for i in range(len(group_file)):
            new_obj = group_file[i]
            group_name = group_file[i]["id"]
            rewritten_groups[group_name] = new_obj
        staged_groups = []
        if len(groups) > 0:
            if len(groups[0]) > 0:
                for group in groups:
                    self.traverse_staging(
                        int(group), rewritten_groups, staged_groups)
                    self.log.info("Staging group [%d/%d]" %
                                  (len(staged_groups), len(groups)))

        with open("%s/data/staged_groups.json" % self.app_path, "w") as f:
            json.dump(misc_utils.remove_dupes(staged_groups), f, indent=4)

    def is_group_non_empty(self, group):
        if group["projects"]:
            return True
        subgroups = self.groups_api.get_all_subgroups(
            group["id"],
            self.config.destination_host,
            self.config.destination_token)
        for sg in subgroups:
            resp = self.groups_api.get_group(
                sg["id"],
                self.config.destination_host,
                self.config.destination_token)
            self.is_group_non_empty(resp.json())

    def delete_groups(self, dry_run=False, skip_projects=False):
        staged_groups = self.get_staged_groups()
        for g in staged_groups:
            # SaaS destination instances have a parent group
            if self.config.parent_group_path:
                dest_full_path = "{0}/{1}".format(self.config.parent_group_path, g["full_path"])
            else:
                dest_full_path = g["full_path"]
            resp = self.groups_api.get_group_by_full_path(
                dest_full_path,
                self.config.destination_host,
                self.config.destination_token)
            if resp.status_code != 200:
                self.log.info("Group {0} does not exist (status: {1})".format(dest_full_path, resp.status_code))
            elif skip_projects and self.is_group_non_empty(resp.json()):
                self.log.info("Skipping non empty group {}".format(dest_full_path))
            elif not dry_run:
                self.log.info("Removing group {}".format(dest_full_path))
                try:
                    self.groups_api.delete_group(
                        resp.json()["id"],
                        self.config.destination_host,
                        self.config.destination_token)
                except RequestException, e:
                    self.log.error("Failed to remove group {0}\nwith error:\n{1}".format(g, e))

    def traverse_staging(self, id, group_dict, staged_groups):
        if group_dict.get(id, None) is not None:
            g = group_dict[id]
            if g["parent_id"] is None:
                if self.config.parent_id is not None:
                    parent_group = self.groups_api.get_group(
                        self.config.parent_id, self.config.destination_host, self.config.destination_token).json()
                    g["full_parent_namespace"] = parent_group["full_path"]
                    g["parent_namespace"] = parent_group["path"]
                    g["parent_id"] = self.config.parent_id
            else:
                parent_group = group_dict.get(g["parent_id"])
                if parent_group is not None:
                    parent_group_resp = self.groups_api.get_group(
                        parent_group["id"], self.config.source_host, self.config.source_token).json()
                    if self.config.parent_id is not None:
                        tlg = self.groups_api.get_group(
                            self.config.parent_id, self.config.destination_host, self.config.destination_token).json()
                        g["full_parent_namespace"] = "%s/%s" % (
                            tlg["full_path"], parent_group["full_path"])
                        g["parent_namespace"] = parent_group["path"]
                    else:
                        g["full_parent_namespace"] = "%s/%s" % (
                            parent_group_resp["full_path"], parent_group["full_path"])
                        g["parent_namespace"] = parent_group["path"]
                    if parent_group.get("parent_id", None) is not None:
                        self.traverse_staging(
                            parent_group["id"], group_dict, staged_groups)
                    else:
                        staged_groups.append(parent_group)
            staged_groups.append(g)

    def find_all_internal_projects(self):
        groups_to_change = []
        # with open("%s/data/groups.json" % self.app_path, "r") as f:
        #     groups = json.load(f)
        # count = 0
        # for group in groups:
        #     if group["visibility"] != "private":
        #         self.log.info("%s has %s visibility" % (group["name"], group["visibility"]))
        #         count += 1
        #         groups_to_change.append(group)

        # self.log.info("There are %d non-private groups" % count)

        transient_list = []

        parent_group = [self.groups_api.get_group(
            self.config.parent_id, self.config.destination_host, self.config.destination_token).json()]

        print parent_group

        self.traverse_groups(parent_group, transient_list,
                             self.config.destination_host, self.config.destination_token)

        count = 0

        for group in transient_list:
            print "%s, %s" % (group["name"], group["visibility"])
            if group["visibility"] != "private":
                self.log.info("%s has %s visibility" %
                              (group["name"], group["visibility"]))
                count += 1
                groups_to_change.append(group)

        return groups_to_change

    def make_all_internal_groups_private(self):
        groups = self.find_all_internal_projects()
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

    def add_badges(self, new_id, namespace, badges):
        try:
            for badge in badges:
                # split after hostname and retrieve only reamining path
                link_url_suffix = badge["link_url"].split("/", 3)[3]
                image_url_suffix = badge["image_url"].split("/", 3)[3]
                data = {
                    "link_url": "{0}/{1}/{2}".format(self.config.destination_host, namespace, link_url_suffix),
                    "image_url": "{0}/{1}/{2}".format(self.config.destination_host, namespace, image_url_suffix)
                }
                self.groups_api.add_group_badge(self.config.destination_host,
                                                self.config.destination_token,
                                                new_id,
                                                data=data)
        except RequestException, e:
            self.log.error("Failed to add group ID {0} badge {1}, with error:\n{2}".format(new_id, badge, e))

    def validate_staged_groups_schema(self):
        staged_groups = self.get_staged_groups()
        for g in staged_groups:
            self.log.info(g)
            if g.get("name", None) is None:
                self.log.warn("name is missing")
            if g.get("namespace", None) is None:
                self.log.warn("namespace is missing")
            if g.get("project_type", None) is None:
                self.log.warn("project_type is missing")
            if g.get("default_branch", None) is None:
                self.log.warn("default_branch is missing")
            if g.get("visibility", None) is None:
                self.log.warn("visibility is missing")
            if g.get("http_url_to_repo", None) is None:
                self.log.warn("http_url_to_repo is missing")
            if g.get("shared_runners_enabled", None) is None:
                self.log.warn("shared_runners_enabled is missing")
            if g.get("members", None) is None:
                self.log.warn("members is missing")
            if g.get("id", None) is None:
                self.log.warn("id is missing")
            if g.get("description", None) is None:
                self.log.warn("description is missing")
