"""
Congregate - GitLab instance migration utility 

Copyright (c) 2018 - GitLab
"""


import os
import sys
import json

class ig:
    def __init__(self):
        app_path = os.getenv("CONGREGATE_PATH")
        with open('%s/data/config.json' % app_path) as f:
            self.config = json.load(f)["config"]
    
    @property
    def props(self):
        """
            Return entire config object
        """
        return self.config
    
    @property
    def parent_host(self):
        return self.config["parent_instance_host"]

    @property
    def parent_token(self):
        return self.config["parent_instance_token"]

    @property
    def child_host(self):
        return self.config["child_instance_host"]

    @property
    def child_token(self):
        return self.config["child_instance_token"]

    @property
    def location(self):
        return self.config["location"]  

    @property
    def bucket_name(self):
        return self.config["bucket_name"]

    @property
    def s3_access_key(self):
        return self.config["access_key"]

    @property
    def s3_secret_key(self):
        return self.config["secret_key"]

    @property
    def filesystem_path(self):
        return self.config["path"]

    @property
    def parent_id(self):
        return self.config.get("parent_id", None)
    
    @property
    def child_username(self):
        return self.config["child_username"]

    @property
    def parent_user_id(self):
        return self.config.get("parent_user_id", None)
    
    @property
    def mirror_username(self):
        return self.config.get("mirror_username", None)