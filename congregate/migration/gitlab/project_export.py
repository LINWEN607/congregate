from helpers.base_class import BaseClass
from migration.gitlab.users import UsersClient
from aws import AwsClient
import tarfile
import os
import json
import shutil

class ProjectExportClient(BaseClass):
    KEYS = ["author_id", "created_by_id", "user_id", "updated_by_id", "assignee_id", "merged_by_id", "merge_user_id"]
    def __init__(self):
        self.users = UsersClient()
        self.aws = AwsClient()
        self.users_map = {}
        super(ProjectExportClient, self).__init__()

    def update_project_export_members(self, name, namespace, filename):
        file_path = self.aws.copy_from_s3(name, namespace, filename)
        extract_path = "%s/downloads/%s_%s" % (self.config.filesystem_path, name, namespace)
        with tarfile.open(file_path, "r:gz") as tar:
            tar.extractall(path=extract_path)
        os.remove(file_path)
        with tarfile.open(file_path, "w:gz") as tar:            
            self.__rewrite_project_json(extract_path)
            tar.add(extract_path, arcname="")
        
        #self.aws.copy_file_to_s3(filename)
        os.chdir(self.app_path)
        # os.remove(file_path)
        shutil.rmtree(extract_path)

    def __rewrite_project_json(self, path):
        with open("%s/project.json" % path, "r") as f:
            data = json.load(f)
        
        #Build user map
        for d in data["project_members"]:
            new_user = self.users.find_user_by_email_comparison(d["user_id"])
            if new_user is not None:
                d["user"]["id"] = new_user["id"]
                self.users_map[d["user_id"]] = new_user["id"]
            else:
                d["user"]["id"] = self.config.parent_user_id
                self.users_map[d["user_id"]] = self.config.parent_user_id
            d["user"]['username'] = "This is invalid"

        # Update Project Members
        self.__update_project_members(data["project_members"])
        # Update issue metadata
        self.__update_authors_and_events(data["issues"])
        # Update merge request metadata
        self.__update_authors_and_events(data["merge_requests"])
        
        with open("%s/project.json" % path, "w") as f:
            json.dump(data, f, indent=4)

    def __traverse_json(self, data):
        for k, v in data.items():
            if k in self.KEYS:
                if v is not None:
                    data[k] = self.__find_or_create_id(v)
            # else:
            #     if k != "project_members":
            #         if isinstance(data[k], list):
            #             for d in data[k]:
            #                 self.__traverse_json(d)
            #         elif isinstance(data[k], dict):
            #             self.__traverse_json(data[k])
    
    def __update_authors_and_events(self, data):
        for d in data:
            d["author_id"] = self.__find_or_create_id(d["author_id"])
            if d.get("closed_by_id", None) is not None:
                d["closed_by_id"] = self.__find_or_create_id(d["closed_by_id"])
            if d.get("issue_assignees", None) is not None:
                for a in d["issue_assignees"]:
                    self.__traverse_json(a)
            if d.get("events", None) is not None:
                for e in d["events"]:
                    self.__traverse_json(e)
            if d.get("notes", None) is not None:
                for n in d["notes"]:
                    self.__traverse_json(n)
            if d.get("resource_label_events", None) is not None:
                for r in d["resource_label_events"]:
                    self.__traverse_json(r)
            if d.get("metrics", None) is not None:
                self.__traverse_json(d["metrics"])
            
    def __update_project_members(self, data):
        for d in data:
            old_created_by_id = d["created_by_id"]
            if old_created_by_id is not None:
                new_created_by_id = self.__find_or_create_id(old_created_by_id)
                d["created_by_id"] = new_created_by_id
            old_user_id = d["user_id"]
            if old_user_id is not None:
                new_user_id = self.__find_or_create_id(old_user_id)
                d["user_id"] = new_user_id

    def __find_or_create_id(self, key):
        if self.users_map.get(key) is None:
            new_user = self.users.find_user_by_email_comparison(key)
            if new_user is not None:
                self.users_map[key] = new_user["id"]
                return new_user["id"]
            else:
                self.users_map[key] = self.config.parent_user_id
        return self.users_map[key]


    