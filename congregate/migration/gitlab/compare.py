
from congregate.helpers.base_class import BaseClass
from congregate.helpers import api, misc_utils
from congregate.migration.gitlab.groups import GroupsClient
from congregate.migration.gitlab.users import UsersClient
from requests.exceptions import RequestException
import json
from os import path


class CompareClient(BaseClass):
    def __init__(self):
        self.groups = GroupsClient()
        self.users = UsersClient()
        self.unknown_users = {}
        super(CompareClient, self).__init__()

    def create_group_migration_results(self, staged=False):
        """
            Creates group migration comparison data

            Returns dict containing comparison and dict containing unknown users
        """
        prefix = ""
        file_path = '%s/data/destination.json' % self.app_path
        tlg = False
        if self.config.parent_id is not None:
            tlg = True
            prefix = self.groups.get_group(self.config.parent_id, self.config.parent_host, self.config.parent_token).json()["full_path"] + "/"
            file_path = '%s/data/destination%dgroups.json' % (self.app_path, self.config.parent_id)
        
        destination_groups = self.load_group_data(file_path, self.config.parent_host, self.config.parent_token, location="destination", top_level_group=tlg)
        source_groups = self.load_group_data('%s/data/groups.json' % self.app_path, self.config.child_host, self.config.child_token)
        
        shared_key = "full_path"
        rewritten_destination_groups = misc_utils.rewrite_list_into_dict(destination_groups, shared_key)
        rewritten_source_groups = misc_utils.rewrite_list_into_dict(source_groups, shared_key, prefix=prefix)

        results = {
            "Total groups in source instance": len(source_groups),
            "Total groups in destination instance": len(destination_groups)
        }

        results["results"] = self.compare_groups(rewritten_source_groups, rewritten_destination_groups)

        return results, self.unknown_users

    def load_group_data(self, file_path, host, token, location=None, top_level_group=None):
        if path.exists(file_path):
            with open(file_path, "r") as f:
                return json.load(f)
        else:
            return self.groups.retrieve_group_info(host, token)

    def compare_groups(self, source_groups, destination_groups):
        """
            Compares the path and members of a group

            Returns dict containing the results of the comparison
        """
        results = {}
        for group_path, group_data in source_groups.iteritems():
            comparison = {}
            if destination_groups.get(group_path, None) is not None:
                dest_group_data = destination_groups[group_path]
                comparison["members"] = self.compare_members(group_data["members"], dest_group_data["members"])
                comparison["path"] = self.compare_group_location(group_data["full_path"], dest_group_data["path"])
                results[group_path] = comparison
            else:
                results[group_path] = {
                    "status": "Failed to migrate"
                }
            
        return results

    def compare_group_location(self, source_path, destination_path):
        """
            Compares the source and destination path of a group

            Returns dict containing the difference of group locations
            OR
            Retruns True if locations match
        """
        if self.config.parent_id is not None:
            tlg = self.groups.get_group(self.config.parent_id, self.config.parent_host, self.config.parent_token).json()
            source_path = "%s/%s" % (tlg["full_path"], source_path)
        
        if source_path != destination_path:
            return {
                "expected": source_path,
                "actual": destination_path
            }
        
        return True

    def compare_members(self, source_members, destination_members):
        """
            Compares the source and destination path of a group

            Returns dict containing the difference of group members
        """
        results = {
            "source_member_count": len(source_members),
            "destination_member_count": len(destination_members)
        }

        if len(source_members) != len(destination_members):
            results["member_counts_match"] = False
        else:
            results["member_counts_match"] = True

        rewritten_source_members = misc_utils.rewrite_list_into_dict(source_members, "username")
        rewritten_destination_members = misc_utils.rewrite_list_into_dict(destination_members, "username")

        diff =  { k : rewritten_destination_members[k] for k in set(rewritten_destination_members) - set(rewritten_source_members) }
        results["unknown added members"] = diff
        for k in diff:
            self.unknown_users[k] = diff[k]

        diff =  { k : rewritten_source_members[k] for k in set(rewritten_source_members) - set(rewritten_destination_members) }
        results["missing members"] = diff

        # diff = []
        # for k, v in rewritten_destination_members.items():

        #     if k in rewritten_source_members:
        #         unknown_user = self.users.get_user(v["id"], self.config.parent_host, self.config.parent_token)
        #         diff.append(
        #             {
        #                 "unknown user": unknown_user,
        #                 "original user": rewritten_source_members[k]
        #             }
        #         )
        
        # results["member_differences"] = diff
        return results

    def compare_staged_users(self):
        with open("%s/data/staged_groups.json" % self.app_path, "r") as f:
            groups = json.load(f)

        with open("%s/data/stage.json" % self.app_path, "r") as f:
            projects = json.load(f)

        snapshot = {}

        snapshot["projects"] = self.generate_user_snapshot_map(projects)
        snapshot["groups"] = self.generate_user_snapshot_map(groups)

        return snapshot

    def generate_user_snapshot_map(self, data):
        users_map = {}
        for d in data:
            for member in d["members"]:
                user = self.users.get_user(member["id"], self.config.parent_host, self.config.parent_token).json()
                users_map[member["id"]] = {
                    "username": member["username"],
                    "email": user["email"]
                }
                if len(user["identities"]) > 0:
                    users_map["extern_uid"] = user["identities"][0].get("extern_uid")
        return users_map

    def generate_diff(self, expected, actual):
        if expected != actual:
            return {
                "expected": expected,
                "actual": actual
            }
        return True