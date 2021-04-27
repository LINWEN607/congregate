"""
Congregate - GitLab instance migration utility

Copyright (c) 2021 - GitLab
"""

import os
import json
from re import sub, split
from configparser import ConfigParser, ParsingError

from congregate.helpers.utils import get_congregate_path
from congregate.helpers.string_utils import deobfuscate


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
            raise SystemExit() from pe

    def option_exists(self, section, option):
        return self.config.has_option(
            section, option) and self.config.get(section, option)

    def prop(self, section, option, default=None, obfuscated=False):
        if self.option_exists(section, option):
            if not obfuscated:
                return self.config.get(section, option)
            return deobfuscate(self.config.get(section, option))
        return default

    def prop_lower(self, section, option, default=None):
        if self.option_exists(section, option):
            return self.config.get(section, option).lower()
        return default

    def prop_int(self, section, option, default=None):
        """
            Returns configuration property string casted to an int
        """
        if self.option_exists(section, option):
            return self.config.getint(section, option)
        return default

    def prop_bool(self, section, option, default=None):
        """
            Returns configuration property string casted to a bool
        """
        if self.option_exists(section, option):
            return self.config.getboolean(section, option)
        return default

    def prop_list(self, section, option, default=None):
        """
            Returns configuration property string as a list.

            For example, a configuration property stored as '[hello, world, how, are you]'
            will be returned as ["hello", "world", "how", "are", "you"]
        """
        if self.option_exists(section, option):
            return split(r', |,', sub(r'\[|\]|\"\"\"', '', self.config.get(section, option)))
        return default

    def prop_dict(self, section, option, default=None):
        """
            Returns configuration property JSON string as a dictionary
        """
        if self.option_exists(section, option):
            return json.loads(self.config.get(section, option))
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
        return self.prop("DESTINATION", "dstn_access_token", default=None, obfuscated=True)

    @property
    def destination_registry(self):
        return self.prop("DESTINATION", "dstn_registry_url")

    @property
    def reporting(self):
        return self.prop_dict("DESTINATION", "reporting", default={})

    @property
    def import_user_id(self):
        return self.prop_int("DESTINATION", "import_user_id")

    @property
    def shared_runners_enabled(self):
        return self.prop_bool("DESTINATION", "shared_runners_enabled", default=True)

    @property
    def append_project_suffix_on_existing_found(self):
        """
        This setting determines if, in the instance of an existing project being found at the destination with the
        same name as the source project, if we should append a value and create the project, or just fail the import.
        :return:    The value from the append_project_suffix configuration value, or `False` by default. Note:
                    The `False` return will execute the default behavior and cause the import to fail if an existing
                    project is found
        """
        return self.prop_bool("DESTINATION", "project_suffix", default=False)

    @property
    def max_import_retries(self):
        """
        Project import retry count.
        :return: The set config value or 3 as default.
        """
        return self.prop_int("DESTINATION", "max_import_retries", default=3)

    @property
    def dstn_parent_id(self):
        return self.prop_int("DESTINATION", "dstn_parent_group_id")

    @property
    def dstn_parent_group_path(self):
        return self.prop("DESTINATION", "dstn_parent_group_path")

    @property
    def group_sso_provider(self):
        return self.prop("DESTINATION", "group_sso_provider")

    @property
    def group_sso_provider_pattern(self):
        return self.prop("DESTINATION", "group_sso_provider_pattern")

    @property
    def group_sso_provider_map_file(self):
        return self.prop("DESTINATION", "group_sso_provider_map_file")

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
        return self.prop_int("DESTINATION", "max_asset_expiration_time", default=24)

    @property
    def pmi_project_id(self):
        """
        The project id we should write all our affirmation issues to
        """
        return self.prop_int("DESTINATION", "pmi_project_id")

    # LDAP Info
    def ldap_group_link_provider(self):
        """
        The LDAP server label from the instance configuration. 
        In gitlab.rb: gitlab_rails['ldap_servers'].label
        On the UI: Visible in the LDAP synchonizations page for a group
        """
        return self.prop("DESTINATION", "ldap_group_link_provider", default="")

    def ldap_group_link_group_access(self):
        """
        The minimum access to give users via the sync. This maps directly to the values at https://docs.gitlab.com/ee/api/members.html#valid-access-levels
        Defaults to no access
        """
        return self.prop_int("DESTINATION", "ldap_group_link_group_access", default=0)

# SOURCE
    def list_multiple_source_config(self, source_options):
        """
            Returns list of multiple SCM source config dictionarty including hostname and token
        """
        return self.prop_dict("MULTIPLE_SOURCE", "sources", default={}).get(source_options, [])

    @property
    def source_type(self):
        return self.prop_lower("SOURCE", "src_type")

    @property
    def source_tier(self):
        return self.prop_lower("SOURCE", "src_tier", default="core")

    @property
    def source_host(self):
        return self.prop("SOURCE", "src_hostname")

    @property
    def source_username(self):
        return self.prop("SOURCE", "src_username")

    @property
    def source_password(self):
        return self.prop("SOURCE", "src_password", default=None, obfuscated=True)

    @property
    def source_token(self):
        return self.prop("SOURCE", "src_access_token", default=None, obfuscated=True)

    @property
    def src_parent_id(self):
        return self.prop_int("SOURCE", "src_parent_group_id")

    @property
    def src_parent_group_path(self):
        return self.prop("SOURCE", "src_parent_group_path")

    # GitHub
    @property
    def src_parent_org(self):
        return self.prop("SOURCE", "src_parent_org")

    @property
    def repo_list(self):
        return self.prop("SOURCE", "repo_path")

    @property
    def source_registry(self):
        return self.prop("SOURCE", "src_registry_url")

    @property
    def export_import_timeout(self):
        """
        The maximum amount of time to wait for a group or project export or import.
        We should adjust it depending on the size of the largest projects we are migrating.
        In general 1h should be sufficient for each export or import process.
        We can always go back and run the project post-migration if it takes longer to import.
        :return: The set config value of 3600 seconds (one hour) as default
        """
        return self.prop_int("SOURCE", "export_import_timeout", default=3600)

# CI_SOURCE
    def list_ci_source_config(self, ci_source_options):
        """
            Returns list of ci source config dictionarty including hostname, username and token
            ci_source_options could be jenkins_ci_source or teamcity_ci_source
        """
        return self.ci_sources.get(ci_source_options, [])

    @property
    def ci_sources(self):
        return self.prop_dict("CI_SOURCE", "sources", default={})

    @property
    def ci_source_type(self):
        return self.prop_lower("CI_SOURCE", "ci_src_type")

    @property
    def ci_source_host(self):
        return self.prop("CI_SOURCE", "ci_src_hostname")

    @property
    def ci_source_username(self):
        return self.prop("CI_SOURCE", "ci_src_username")

    @property
    def ci_source_token(self):
        return self.prop("CI_SOURCE", "ci_src_access_token", default=None, obfuscated=True)

# JENKINS_CI_SOURCE
    @property
    def jenkins_ci_source_type(self):
        return self.prop_lower("JENKINS_CI_SOURCE", "jenkins_ci_src_type")

    @property
    def jenkins_ci_source_host(self):
        return self.prop("JENKINS_CI_SOURCE", "jenkins_ci_src_hostname")

    @property
    def jenkins_ci_source_username(self):
        return self.prop("JENKINS_CI_SOURCE", "jenkins_ci_src_username")

    @property
    def jenkins_ci_source_token(self):
        return self.prop("JENKINS_CI_SOURCE", "jenkins_ci_src_access_token", default=None, obfuscated=True)

# TEAMCITY_CI_SOURCE
    @property
    def tc_ci_source_type(self):
        return self.prop_lower("TEAMCITY_CI_SOURCE", "tc_ci_src_type")

    @property
    def tc_ci_source_host(self):
        return self.prop("TEAMCITY_CI_SOURCE", "tc_ci_src_hostname")

    @property
    def tc_ci_source_username(self):
        return self.prop("TEAMCITY_CI_SOURCE", "tc_ci_src_username")

    @property
    def tc_ci_source_token(self):
        return self.prop("TEAMCITY_CI_SOURCE", "tc_ci_src_access_token", default=None, obfuscated=True)

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
        return self.prop("EXPORT", "s3_access_key_id", default=None, obfuscated=True)

    @property
    def s3_secret_key(self):
        return self.prop("EXPORT", "s3_secret_access_key", default=None, obfuscated=True)

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
        return self.prop_bool("USER", "keep_blocked_users", default=False)

    @property
    def reset_password(self):
        """
        Whether or not we should send the reset password link on user creation. Note: The API defaults to false
        :return: The set config value or True as default.
        """
        return self.prop_bool("USER", "reset_pwd", default=True)

    @property
    def force_random_password(self):
        """
        This API flag for user creation is not well-documented, but can be used in combination with password and
        reset_password to generate a random password at create
        :return: The set config value or False as default.
        """
        return self.prop_bool("USER", "force_rand_pwd", default=False)

# APP
    @property
    def export_import_status_check_time(self):
        """
        The frequency of checking a group or project export or import status.
        Depending whether we are migrating during peak hours or not we should be able to adjust it.
        In general it should be increased when using multiple processes i.e. when the API cannot handle all the requests.
        :return: The set config value or 10 (seconds) as default.
        """
        return self.prop_int("APP", "export_import_status_check_time", default=10)

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
        return self.prop_int("APP", "ui_port", default=8000)

    @property
    def ssl_verify(self):
        return self.prop_bool("APP", "ssl_verify", default=True)

    @property
    def wave_spreadsheet_path(self):
        """
        The absolute path to a spreadsheet containing specific details about migration waves
        """
        return self.prop("APP", "wave_spreadsheet_path")

    @property
    def wave_spreadsheet_columns(self):
        """
        A list of columns to include in the wave spreadsheet transformation
        """
        return self.prop_list("APP", "wave_spreadsheet_columns")

    @property
    def wave_spreadsheet_column_mapping(self):
        """
        A dictionary containing the columns in the spreadsheet mapped to the keys we need for a wave migration.

        Example output:
        {
            "Wave name": "example column 1",
            "Wave date": "migration name",
            "Source Url": "company repo url"
        }
        """
        return self.prop_dict("APP", "wave_spreadsheet_column_mapping")

    @property
    def wave_spreadsheet_column_to_project_property_mapping(self):
        """
        Similar to wave_spreadsheet_column_mapping, this defines how our headers map to properties in the project object 
        for when we generate the stage wave CSV file

        Example output:
        {
            "Source Url": "http_url_to_repo"
        }
        """
        return self.prop_dict("APP", "wave_spreadsheet_column_to_project_property_mapping")

    @property
    def mongo_host(self):
        """
        The explicit host for the mongodb connection. Defaults to None
        """
        return self.prop("APP", "mongo_host", default=None)

    @property
    def mongo_port(self):
        """
        The explicit port for the mongodb connection. Defaults to 27017
        """
        return self.prop_int("APP", "mongo_port", default=27017)

    @property
    def processes(self):
        """
        Number of parallel process to run for specific commands like list, migrate, etc.
        Defaults to 4 as the optimal # to use when child processes are needed.
        """
        return self.prop_int("APP", "processes", default=4)

# HIDDEN PROPERTIES

    # Used only by "map-users" and "map-and-stage-users-by-email-match" command

    @property
    def user_map(self):
        return self.prop("USER", "user_map_csv")

    # Used only by disabled migration mode "filesystem-aws"
    @property
    def allow_presigned_url(self):
        return self.prop_bool("EXPORT", "allow_presigned_url", default=False)

    @property
    def lower_case_group_path(self):
        """
        If all groups need to be converted to lowercase during a migration
        """
        return self.prop_bool("DESTINATION", "lower_case_group_path", default=False)

    @property
    def lower_case_project_path(self):
        """
        If all projects need to be converted to lowercase during a migration
        """
        return self.prop_bool("DESTINATION", "lower_case_project_path", default=False)

    @property
    def users_to_ignore(self):
        """
        A list of users to ignore during a migration. Currently only used in BitBucket Server migrations.
        Defaults to empty list
        """
        return self.prop_list("DESTINATION", "users_to_ignore", default=[])

    @property
    def projects_limit(self):
        """
        Max number of personal projects a GitLab user can create. Value may be enforced on instance level
        """
        return self.prop_int("USER", "projects_limit")

    @property
    def remapping_file_path(self):
        """
        Path to a JSON file for remapping URLs during a GitLab to GitLab import. Notes:
            * The existence of this file path in a congregate.conf is also the flag for enabling this feature
            * Currently, changes are made against one branch, spawned from default, no matter how many file/data sections are configured
            * File is of the form:
                {
                    "filenames": [
                        ".gitlab-ci.yml",
                        "requirements.yml",
                        "ansible/playbooks/requirements.yml",
                        "ansible/molecule/default/requirements.yml"
                    ],
                    "patterns": [
                        {
                            "pattern": "https://git.internal.ca/ansible/roles/global-setup.git",
                            "replace_with": "https://gitlab.com/company/infra/ansible/roles/global-setup.git"
                        },
                        {
                            "pattern": "https://git.internal.ca/ansible/roles/healthcheck.git",
                            "replace_with": "https://gitlab.com/company/infra/ansible/roles/healthcheck.git"
                        },
                        {...}
                    ]
                }      
        which allows for multiple files with multiple changes.
        """
        return self.prop("APP", "remapping_file")
