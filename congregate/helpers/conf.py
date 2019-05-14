"""
Congregate - GitLab instance migration utility 

Copyright (c) 2018 - GitLab
"""

import os
import json
from cli import config as config_cli


class ig:
    def __init__(self):
        app_path = os.getenv("CONGREGATE_PATH")
        if not os.path.isfile('%s/data/config.json' % app_path):
            config_cli.generate_config()
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
        return self.config.get("parent_instance_host", None)

    @property
    def parent_token(self):
        return self.config.get("parent_instance_token", None)

    @property
    def child_host(self):
        return self.config.get("child_instance_host", None)

    @property
    def child_token(self):
        return self.config.get("child_instance_token", None)

    @property
    def location(self):
        return self.config.get("location", None)

    @property
    def bucket_name(self):
        return self.config.get("bucket_name", None)

    @property
    def s3_region(self):
        return self.config.get("s3_region", None)

    @property
    def s3_access_key(self):
        return self.config.get("access_key", None)

    @property
    def s3_secret_key(self):
        return self.config.get("secret_key", None)

    @property
    def filesystem_path(self):
        return self.config.get("path", None)

    @property
    def parent_id(self):
        return self.config.get("parent_id", None)

    @property
    def child_username(self):
        return self.config.get("child_username", None)

    @property
    def parent_user_id(self):
        return self.config.get("parent_user_id", None)

    @property
    def mirror_username(self):
        return self.config.get("mirror_username", None)

    @property
    def external_user_name(self):
        return self.config.get("external_user_name", None)

    @property
    def external_user_password(self):
        return self.config.get("external_user_password", None)

    @property
    def external_source(self):
        return self.config.get("external_source", None)

    @property
    def repo_list(self):
        return self.config.get("repo_list_path", None)

    @property
    def user_map(self):
        return self.config.get("user_map_csv", None)

    @property
    def allow_presigned_url(self):
        return self.config.get("allow_presigned_url", None)

    @property
    def threads(self):
        return self.config.get("number_of_threads", None)

    @property
    def make_visibility_private(self):
        return self.config.get("make_visibility_private", None)

    @threads.setter
    def threads(self, value):
        self.threads = value
