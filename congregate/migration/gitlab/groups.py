from helpers.base_class import BaseClass
from helpers import api, misc_utils
from migration.gitlab.variables import gl_variables_client as vars_client
from requests.exceptions import RequestException
import json
from os import path

class GroupsClient(BaseClass):
    def __init__(self):
        self.vars = vars_client()
        super(GroupsClient, self).__init__()

    def get_group(self, id, host, token):
        return api.generate_get_request(host, token, "groups/%d" % id)

    def search_for_group(self, name, host, token):
        yield api.list_all(host, token, "groups?search=%s" % name)

    def create_group(self, host, token, data):
        return api.generate_post_request(host, token, "groups", json.dumps(data))

    def add_member_to_group(self, id, host, token, member):
        return api.generate_post_request(host, token, "groups/%d/members" % id, json.dumps(member))

    def get_all_groups(self, host, token):
        yield api.list_all(host, token, "groups")

    def get_all_group_members(self, id, host, token):
        yield api.list_all(host, token, "groups/%s/members" % id)

    def get_all_subgroups(self, id, host, token):
        yield api.list_all(host, token, "groups/%s/subgroups" % id)

    def traverse_groups(self, base_groups, transient_list,  host, token, parent_group=None):
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
            members = list(self.get_all_group_members(host, token, str(group["id"])))
            group["members"] = members
            transient_list.append(group)
            subgroups = list(self.get_all_subgroups(id, host, token))
            if parent_group is not None:
                parent_group["child_ids"].append(group["id"])
            if len(subgroups) > 0:
                parent_group = transient_list[-1]
                self.l.logger.info("traversing into a subgroup")
                self.traverse_groups(subgroups, transient_list, host, token, parent_group)
            else:
                self.l.logger.info("No subgroups found")
            parent_group = None
                
    def retrieve_group_info(self, quiet=False):
        groups = list(self.get_all_groups(self.config.child_host, self.config.child_token))
        transient_list = []

        self.traverse_groups(groups, transient_list, self.config.child_host, self.config.child_token)

        with open('%s/data/groups.json' % self.app_path, "w") as f:
            json.dump(groups, f, indent=4)
        
        if not quiet:
            self.l.logger.info("Retrieved %d groups. Check groups.json to see all retrieved groups" % len(groups))

    def migrate_group_info(self):
        if not path.isfile("%s/data/groups.json" % self.app_path):
            self.retrieve_group_info()
        with open("%s/data/staged_groups.json" % self.app_path, "r") as f:
            groups = json.load(f)

        rewritten_groups = {}
        for i in range(len(groups)):
            new_obj = groups[i]
            group_name = groups[i]["id"]
            rewritten_groups[group_name] = new_obj
        self.traverse_and_migrate(groups, rewritten_groups)
        
    def traverse_and_migrate(self, groups, rewritten_groups, parent_id=None):
        count = 0
        for group in groups:
            self.l.logger.info("Migrating %s %d/%d" % (group["name"], count, len(group)))
            if group.get("id", None) is not None:
                if rewritten_groups is not None:
                    has_children = "child_ids" in rewritten_groups.get(group["id"], None)
                group_id = group["id"]
                # group.pop("id")
                members = group["members"]
                
                if self.config.make_visibility_private is not None:
                    if self.config.make_visibility_private is True:
                        group["visibility"] = "private"

                if group.get("parent_namespace", None) is not None:
                    found = False
                    if rewritten_groups.get(group["parent_id"], None) is not None:
                        parent_id = rewritten_groups[group["parent_id"]]["id"]
                    elif group.get("old_parent_id", None) is not None:
                        if rewritten_groups.get(group["old_parent_id"], None) is not None:
                            parent_id = rewritten_groups[group["old_parent_id"]]["id"]
                    
                    #search = api.search(self.config.parent_host, self.config.parent_token, "groups", group["parent_namespace"])
                    if parent_id is not None:
                        if rewritten_groups[parent_id].get("new_parent_id", None) is not None:
                            group["parent_id"] = rewritten_groups[parent_id]["new_parent_id"]
                            found = True
                        else:
                            for s in api.list_all(self.config.parent_host, self.config.parent_token, "groups?search=%s" % group["parent_namespace"]):
                                if rewritten_groups.get(parent_id, None) is not None:
                                    if s["full_path"].lower() == rewritten_groups[group["id"]]["full_parent_namespace"].lower():
                                        rewritten_groups[parent_id]["new_parent_id"] = s["id"]
                                        group["parent_id"] = s["id"]
                                        found = True
                                        break
                        if found is False:
                            self.traverse_and_migrate([rewritten_groups[parent_id]], rewritten_groups)
                            #search = api.search(self.config.parent_host, self.config.parent_token, "groups", group["parent_namespace"])
                            for s in api.list_all(self.config.parent_host, self.config.parent_token, "groups?search=%s" % group["parent_namespace"]):
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
                        self.l.logger.info("Parent namespace is empty")

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
                            group_without_id.pop("parent_namespace")
                            self.l.logger.info("Popping parent group")
                        if group_without_id.get("full_parent_namespace", None) is not None:
                            full_parent_namespace = group_without_id["full_parent_namespace"]
                            group_without_id.pop("full_parent_namespace")
                            self.l.logger.info("Popping parent namespace")
                        response = self.create_group(self.config.parent_host, self.config.parent_token, group_without_id).json()
                        if isinstance(response, dict):
                            if response.get("message", None) is not None:
                                if "Failed to save group" in response["message"]:
                                    self.l.logger.info("Group already exists. Searching for group ID")
                                    #new_group = api.search(self.config.parent_host, self.config.parent_token, 'groups', group['path'])

                                    #if new_group is not None and len(new_group) > 0:
                                    found_group = False
                                    for ng in api.list_all(self.config.parent_host, self.config.parent_token, "groups/%d/subgroups" % group["parent_id"]):
                                        if ng["full_path"] == full_parent_namespace:
                                            new_group_id = ng["id"]
                                            print new_group_id
                                            self.l.logger.info("Group found")
                                            found_group = True
                                            break
                                        if found_group is True:
                                            break

                                else:
                                    self.l.logger.info("Failed to save group")
                            else:
                                new_group_id = response["id"]
                        elif isinstance(response, list):
                            new_group_id = response[0]["id"]
                    except RequestException, e:
                        self.l.logger.info("Group already exists")
                    if new_group_id is None:
                        new_group = api.search(self.config.parent_host, self.config.parent_token, 'groups', group['path'])
                        if new_group is not None and len(new_group) > 0:
                            for ng in new_group:
                                if ng["name"] == group["name"]:
                                    if ng["parent_id"] == group["parent_id"] and group["parent_id"] == self.config.parent_id:
                                        new_group_id = ng["id"]
                                        self.l.logger.info("New group found")
                                        break
                    if new_group_id:
                        root_user_present = False
                        for member in members:
                            if member["id"] == self.config.parent_user_id:
                                root_user_present = True
                            new_member = {
                                "user_id": member["id"],
                                "access_level": int(member["access_level"])
                            }

                            try:
                                response = api.generate_post_request(self.config.parent_host, self.config.parent_token, "groups/%d/members" % new_group_id, json.dumps(new_member))
                            except RequestException, e:
                                self.l.logger.error(e)

                        self.vars.migrate_variables(new_group_id, group_id, "group")

                        if not root_user_present:
                            self.l.logger.info("removing root user from group")
                            response = api.generate_delete_request(self.config.parent_host, self.config.parent_token, "groups/%d/members/%d" % (new_group_id, int(self.config.parent_user_id)))
                            print response

                        # if has_children:
                        #     subgroup = []
                        #     self.l.logger.info(group["child_ids"])
                        #     for sub in group["child_ids"]:
                        #         # rewritten_groups.pop(group_id, None)
                        #         self.l.logger.info(rewritten_groups.get(sub))
                        #         self.l.logger.info(rewritten_groups.keys())
                        #         if rewritten_groups.get(sub) is not None:
                        #             sub_group = rewritten_groups.get(sub)
                        #             sub_group["old_parent_id"] = sub_group["parent_id"]
                        #             sub_group["parent_id"] = new_group_id
                        #             subgroup.append(sub_group)
                        #     self.l.logger.info(subgroup)
                        #     traverse_and_migrate(subgroup, rewritten_groups)
                        # rewritten_groups.pop(group_id, None)
            else:
                print "Leaving recursion"

            count += 1 

    def update_members(self):
        with open("%s/data/staged_groups.json" % self.app_path, "r") as f:
            groups = json.load(f)
        for group in groups:
            # TODO: Change this to a search check. This assumes the instance doesn't contain various nested groups with the same name
            new_group_id = api.generate_get_request(self.config.parent_host, self.config.parent_token, 'groups', params={'search': group['name']}).json()
            print new_group_id
            members = group["members"]
            for member in members:
                if member["id"] == self.config.parent_user_id:
                    root_user_present = True
                new_member = {
                    "user_id": member["id"],
                    "access_level": int(member["access_level"])
                }

                try:
                    api.generate_post_request(self.config.parent_host, self.config.parent_token, "groups/%d/members" % new_group_id, json.dumps(new_member))
                except RequestException, e:
                    self.l.logger.error(e)

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
                    self.traverse_staging(int(group), rewritten_groups, staged_groups)
                    self.l.logger.info("Staging group [%d/%d]" % (len(staged_groups), len(groups)))
                    
        with open("%s/data/staged_groups.json" % self.app_path, "w") as f:
            json.dump(misc_utils.remove_dupes(staged_groups), f, indent=4)

    def traverse_staging(self, id, group_dict, staged_groups):
        if group_dict.get(id, None) is not None:
            g = group_dict[id]
            if g["parent_id"] is None:
                if self.config.parent_id is not None:
                    parent_group = self.get_group(self.config.parent_id, self.config.parent_host, self.config.parent_token).json()
                    g["full_parent_namespace"] = parent_group["full_path"]
                    g["parent_namespace"] = parent_group["path"]
                    g["parent_id"] = self.config.parent_id
            else:
                parent_group = group_dict.get(g["parent_id"])
                if parent_group is not None:
                    parent_group_resp = self.get_group(parent_group["id"], self.config.child_host, self.config.child_token).json()
                    g["full_parent_namespace"] = "%s/%s" % (parent_group_resp["full_path"], parent_group["full_path"])
                    g["parent_namespace"] = parent_group["path"]
                    if parent_group.get("parent_id", None) is not None:
                        self.traverse_staging(parent_group["id"], group_dict, staged_groups)
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
        #         self.l.logger.info("%s has %s visibility" % (group["name"], group["visibility"]))
        #         count += 1
        #         groups_to_change.append(group)

        # self.l.logger.info("There are %d non-private groups" % count)

        transient_list = []

        parent_group = [self.get_group(self.config.parent_id, self.config.parent_host, self.config.parent_token).json()]

        print parent_group

        self.traverse_groups(parent_group, transient_list, self.config.parent_host, self.config.parent_token)

        count = 0

        for group in transient_list:
            print "%s, %s" % (group["name"], group["visibility"])
            if group["visibility"] != "private":
                self.l.logger.info("%s has %s visibility" % (group["name"], group["visibility"]))
                count += 1
                groups_to_change.append(group)

        return groups_to_change

    def make_all_internal_groups_private(self):
        groups = self.find_all_internal_projects()
        ids = []
        for group in groups:
            try:
                self.l.logger.debug("Searching for existing %s" % group["name"])
                for proj in self.search_for_group(self.config.parent_host, self.config.parent_token, group['name']):
                    if proj["name"] == group["name"]:
                        if "%s" % group["path"].lower() in proj["full_path"].lower():
                            #self.l.logger.info("Migrating variables for %s" % proj["name"])
                            ids.append(proj["id"])
                            print "%s: %s" % (proj["full_path"], proj["visibility"])
                            break
            except IOError, e:
                self.l.logger.error(e)
        print ids