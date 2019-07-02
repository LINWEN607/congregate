from helpers.base_class import BaseClass
from migration.gitlab.users import UsersClient
from aws import AwsClient
import tarfile
import os
import json
import shutil

class ProjectExportClient(BaseClass):
    KEYS = ["author_id", "created_by_id", "user_id", "updated_by_id"]
    def __init__(self):
        self.users = UsersClient()
        self.aws = AwsClient()
        self.users_map = {}
        super(ProjectExportClient, self).__init__()

    def update_project_export_members(self, name, namespace, filename):
        file_path = self.aws.copy_from_s3(name, namespace, filename)
        extract_path = "%s/downloads/%s_%s" % (self.config.filesystem_path, name, namespace)
        files = None
        with tarfile.open(file_path, "r:gz") as tar:
            tar.extractall(path=extract_path)
            files = tar.getnames()
        with tarfile.open(file_path, "w:gz") as tar:
            self.__rewrite_project_json(extract_path)
            os.chdir(extract_path)
            for f in files:
                tar.add(f)
        
        os.chdir(self.app_path)

        shutil.rmtree(extract_path)

    def __rewrite_project_json(self, path):
        with open("%s/project.json" % path, "r") as f:
            data = json.load(f)
        
        #build user map
        for d in data["project_members"]:
            new_user = self.users.find_user_by_email_comparison(d["user_id"])
            if new_user is not None:
                d["user"]["id"] = new_user["id"]
                self.users_map[d["user_id"]] = new_user["id"]
            else:
                d["user"]["id"] = self.config.parent_user_id
                self.users_map[d["user_id"]] = self.config.parent_user_id
            d["user"]['username'] = "This is invalid"

        self.update_project_members(data["project_members"])
        self.update_authors_and_events(data["issues"])
        self.update_authors_and_events(data["merge_requests"])
        
        with open("%s/project.json" % path, "w") as f:
            json.dump(data, f, indent=4)

    def traverse_json(self, data):
        for k, v in enumerate(data):
            if k in self.KEYS:
                v = self.users_map[v]

    def update_authors_and_events(self, data):
        for d in data:
            old_id = d["author_id"]
            new_id = self.users_map[old_id]
            d["author_id"] = new_id
            for e in d["events"]:
                self.traverse_json(e)

    def update_project_members(self, data):
        for d in data:
            old_created_by_id = d["created_by_id"]
            if old_created_by_id is not None:
                new_created_by_id = self.users_map[old_created_by_id]
                d["created_by_id"] = new_created_by_id
            old_user_id = d["user_id"]
            if old_user_id is not None:
                new_user_id = self.users_map[old_user_id]
                d["user_id"] = new_user_id

    