"""
Congregate - GitLab instance migration utility

Copyright (c) 2020 - GitLab
"""

import os

from configparser import ConfigParser, ParsingError

from congregate.helpers.misc_utils import get_congregate_path, deobfuscate


class Config(object):
    def __init__(self, path=None):
        app_path = get_congregate_path()
        config_path = "{}/{}".format(
            app_path, path) if path else "{}/data/congregate.conf".format(app_path)
        self.config = ConfigParser()
        if not os.path.exists(config_path):
            print("WARNING: No configuration found. Configuring empty file {}".format(
                config_path))
            with open(config_path, "w") as f:
                self.config.write(f)
        try:
            self.config.read(config_path)
        except ParsingError as pe:
            print("Failed to parse configuration, with error:\n{}".format(pe))
            raise SystemExit()

    def option_exists(self, section, option):
        return self.config.has_option(
            section, option) and self.config.get(section, option)

    def prop(self, section, option, default=None, obfuscated=False):
        if self.option_exists(section, option):
            if not obfuscated:
                return self.config.get(section, option)
            return deobfuscate(self.config.get(section, option))
        return default

    def prop_int(self, section, option, default=None):
        if self.option_exists(section, option):
            return self.config.getint(section, option)
        return default

    def prop_bool(self, section, option, default=None):
        if self.option_exists(section, option):
            return self.config.getboolean(section, option)
        return default

    def as_obj(self):
        """
        Return entire config object (setter)
        """
        return self.config

    def as_dict(self):
        """
        Return entire config as dictionary (copy)
        """
        d = dict(self.config._sections)
        for k in d:
            d[k] = dict(self.config._defaults, **d[k])
            d[k].pop('__name__', None)
        return d

# DESTINATION
    @property
    def destination_host(self):
        return self.prop("DESTINATION", "dstn_hostname")

    @property
    def destination_token(self):
        return self.prop("DESTINATION", "dstn_access_token", None, True)

    @property
    def destination_registry(self):
        return self.prop("DESTINATION", "dstn_registry_url")

    @property
    def import_user_id(self):
        return self.prop_int("DESTINATION", "import_user_id")

    @property
    def shared_runners_enabled(self):
        return self.prop_bool("DESTINATION", "shared_runners_enabled", True)

    @property
    def append_project_suffix_on_existing_found(self):
        """
        This setting determines if, in the instance of an existing project being found at the destination with the
        same name as the source project, if we should append a value and create the project, or just fail the import.
        :return:    The value from the append_project_suffix configuration value, or `False` by default. Note:
                    The `False` return will execute the default behavior and cause the import to fail if an existing
                    project is found
        """
        return self.prop_bool("DESTINATION", "project_suffix", False)

    @property
    def max_import_retries(self):
        """
        Project import retry count.
        :return: The set config value or 3 as default.
        """
        return self.prop_int("DESTINATION", "max_import_retries", 3)

    @property
    def dstn_parent_id(self):
        return self.prop_int("DESTINATION", "dstn_parent_group_id")

    @property
    def dstn_parent_group_path(self):
        return self.prop("DESTINATION", "dstn_parent_group_path")

    @property
    def src_parent_id(self):
        return self.prop_int("SOURCE", "src_parent_group_id")

    @property
    def src_parent_group_path(self):
        return self.prop("SOURCE", "src_parent_group_path")

    @property
    def group_sso_provider(self):
        return self.prop("DESTINATION", "group_sso_provider")

    @property
    def group_sso_provider_pattern(self):
        return self.prop("DESTINATION", "group_sso_provider_pattern")

    @property
    def username_suffix(self):
        return self.prop("DESTINATION", "username_suffix")

    @property
    def mirror_username(self):
        return self.prop("DESTINATION", "mirror_username")

    @property
    def max_asset_expiration_time(self):
        """
        The maximum number of hours to rollback users, groups, and projects
        :return: The set config value or 24 hours as default
        """
        return self.prop_int("DESTINATION", "max_asset_expiration_time", 24)

# SOURCE
    @property
    def source_type(self):
        return self.prop("SOURCE", "src_type")

    @property
    def source_host(self):
        return self.prop("SOURCE", "src_hostname")

    @property
    def source_username(self):
        return self.prop("SOURCE", "username")

    @property
    def source_token(self):
        return self.prop("SOURCE", "src_access_token", None, True)

    @property
    def repo_list(self):
        return self.prop("SOURCE", "repo_path")

    @property
    def source_registry(self):
        return self.prop("SOURCE", "src_registry_url")

    @property
    def max_export_wait_time(self):
        """
        The maximum amount of time to wait for exports. Accumulated in congregate.helpers.conf.ig#importexport_wait
        increments
        :return: The set config value of 3600 seconds (one hour) as default
        """
        return self.prop_int("SOURCE", "max_export_wait_time", 3600)

# EXPORT
    @property
    def location(self):
        return self.prop("EXPORT", "location")

    @property
    def bucket_name(self):
        return self.prop("EXPORT", "s3_name")

    @property
    def s3_region(self):
        return self.prop("EXPORT", "s3_region")

    @property
    def s3_access_key(self):
        return self.prop("EXPORT", "s3_access_key_id", None, True)

    @property
    def s3_secret_key(self):
        return self.prop("EXPORT", "s3_secret_access_key", None, True)

    @property
    def filesystem_path(self):
        return self.prop("EXPORT", "filesystem_path")

# USER
    @property
    def keep_blocked_users(self):
        """
        Determines if we should keep blocked users.
        :return: The set config value or False as default.
        """
        return self.prop_bool("USER", "keep_blocked_users", False)

    @property
    def reset_password(self):
        """
        Whether or not we should send the reset password link on user creation. Note: The API defaults to false
        :return: The set config value or True as default.
        """
        return self.prop_bool("USER", "reset_pwd", True)

    @property
    def force_random_password(self):
        """
        This API flag for user creation is not well-documented, but can be used in combination with password and
        reset_password to generate a random password at create
        :return: The set config value or False as default.
        """
        return self.prop_bool("USER", "force_rand_pwd", False)

# APP
    @property
    def importexport_wait(self):
        """
        This key-value (in seconds) concerns the import/export status wait time.
        Depending whether we are migrating during peak hours or not we should be able to adjust it.
        In general it should be increased when using multiple processes i.e. when the API cannot handle all the requests.
        :return: The set config value or 10 (seconds) as default.
        """
        return self.prop_int("APP", "export_import_wait_time", 10)

    @property
    def slack_url(self):
        """
        Presents the Slack Incoming Webhooks URL for sending alerts (logs) to a dedicated GitLab internal private channel.
        Optionally used during customer migrations, mainly to gitlab.com, but also an option for migrations to self-managed.
        """
        return self.prop("APP", "slack_url")

    @property
    def ui_port(self):
        """
        The port used to serve up the flask/VueJS UI. Defaults to 8000
        """
        return self.prop_int("APP", "ui_port", 8000)


# HIDDEN PROPERTIES
    # Used only by "map-users" command

    @property
    def user_map(self):
        return self.prop("USER", "user_map_csv")

    # Used only by disabled migration mode "filesystem-aws"
    @property
    def allow_presigned_url(self):
        return self.prop_bool("EXPORT", "allow_presigned_url", False)
