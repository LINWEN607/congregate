"""
Congregate - GitLab instance migration utility

Copyright (c) 2018 - GitLab
"""

import os
import json
from congregate.cli import config as config_cli
from congregate.helpers.misc_utils import get_congregate_path


class ig(object):
    def __init__(self):
        app_path = get_congregate_path()
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
    def destination_host(self):
        return self.config.get("destination_instance_host", None)

    @property
    def destination_token(self):
        return self.config.get("destination_instance_token", None)

    @property
    def destination_registry(self):
        return self.config.get("destination_instance_registry", None)

    @property
    def source_host(self):
        return self.config.get("source_instance_host", None)

    @property
    def source_token(self):
        return self.config.get("source_instance_token", None)

    @property
    def source_registry(self):
        return self.config.get("source_instance_registry", None)

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
    def parent_group_path(self):
        return self.config.get("parent_group_path", None)

    @property
    def source_username(self):
        return self.config.get("source_username", None)

    @property
    def import_user_id(self):
        return self.config.get("import_user_id", None)

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

    @property
    def external_source_url(self):
        return self.config.get("external_source_url", None)

    @property
    def group_sso_provider(self):
        return self.config.get("group_sso_provider", None)

    @property
    def username_suffix(self):
        return self.config.get("username_suffix", None)

    @property
    def group_full_path_prefix(self):
        return self.config.get("group_full_path_prefix", None)

    @property
    def shared_runners_enabled(self):
        return self.config.get("shared_runners_enabled", True)

    @property
    def append_project_suffix_on_existing_found(self):
        """
        This setting determines if, in the instance of an existing project being found at the destination with the
        same name as the source project, if we should append a value and create the project, or just fail the import.

        :return:    The value from the append_project_suffix configuration value, or `False` by default. Note:
                    The `False` return will execute the default behavior and cause the import to fail if an existing
                    project is found
        """
        return self.config.get("append_project_suffix_on_existing_found", False)

    @threads.setter
    def threads(self, value):
        self.threads = value
