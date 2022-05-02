from configparser import ConfigParser, NoOptionError

import json
import sys
import os
import requests

from gitlab_ps_utils.misc_utils import safe_json_response, is_error_message_present
from gitlab_ps_utils.string_utils import obfuscate, deobfuscate
from gitlab_ps_utils.json_utils import json_pretty
from docker import from_env
from docker.errors import APIError, TLSParameterError

from congregate.helpers.utils import get_congregate_path
from congregate.helpers.configuration_validator import ConfigurationValidator
from congregate.migration.gitlab.api.users import UsersApi
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.api.instance import InstanceApi
from congregate.migration.gitlab.registries import RegistryClient
from congregate.aws import AwsClient

users = UsersApi()
groups = GroupsApi()
instance = InstanceApi()
aws = AwsClient()
reg_client = RegistryClient()
app_path = get_congregate_path()
config_path = f"{app_path}/data/congregate.conf"

"""
    CLI for configuring congregate
"""


def generate_config():
    """
        CLI for generating congregate.conf
    """
    config = ConfigParser(allow_no_value=True)
    # Generic destination instance configuration
    config.add_section("DESTINATION")
    config.set("DESTINATION", "dstn_hostname",
               input("Destination instance Host: "))
    config.set("DESTINATION", "dstn_access_token",
               obfuscate("Destination instance GitLab access token (Settings -> Access Tokens): "))
    migration_user = safe_json_response(users.get_current_user(config.get("DESTINATION", "dstn_hostname"),
                                                               deobfuscate(config.get("DESTINATION", "dstn_access_token"))))
    if migration_user.get("id"):
        config.set("DESTINATION", "import_user_id", str(migration_user["id"]))
    else:
        config.set("DESTINATION", "import_user_id", "")
        print(
            f"WARNING: Destination user not found. Please enter 'import_user_id' manually (in {config_path})")
    shared_runners_enabled = input(
        "Enable shared runners on destination instance (Default: 'No')? ")
    config.set("DESTINATION", "shared_runners_enabled",
               "True" if shared_runners_enabled.lower() in ["yes", "y"] else "False")
    project_suffix = input(
        "Append suffix to project found on destination instance (Default: 'No')? ")
    config.set("DESTINATION", "project_suffix",
               "True" if project_suffix.lower() in ["yes", "y"] else "False")
    max_import_retries = input(
        "Max no. of project import retries (Default: '3'): ")
    config.set("DESTINATION", "max_import_retries",
               max_import_retries if max_import_retries else "3")

    # Parent group destination instance configuration
    dstn_group = input(
        "Are you migrating to a parent group, e.g. gitlab.com (Default: 'No')? ")
    if dstn_group.lower() in ["yes", "y"]:
        config.set("DESTINATION", "dstn_parent_group_id", input(
            "Parent group ID (Group -> Settings -> General): "))
        group = safe_json_response(groups.get_group(
            config.getint("DESTINATION", "dstn_parent_group_id"),
            config.get("DESTINATION", "dstn_hostname"),
            deobfuscate(config.get("DESTINATION", "dstn_access_token"))))
        if group and group.get("full_path"):
            config.set("DESTINATION", "dstn_parent_group_path",
                       group["full_path"])
        else:
            config.set("DESTINATION", "dstn_parent_group_path", "")
            print(
                f"WARNING: Destination group not found. Please enter 'dstn_parent_group_id' and 'dstn_parent_group_path' manually (in {config_path})")
        config.set("DESTINATION", "group_sso_provider",
                   input("Migrating to a group with SAML SSO enabled? Input SSO provider (auth0, adfs, etc.): "))
        if config.get("DESTINATION", "group_sso_provider"):
            sso_pattern = get_sso_provider_pattern()
            config.set("DESTINATION", "group_sso_provider_pattern",
                       sso_pattern)
            if sso_pattern.lower() == "hash":
                config.set("DESTINATION", "group_sso_provider_map_file",
                           input("Absolute path to hash map file?"))

    # Misc destination instance configuration
    username_suffix = input(
        "To avoid username collision, please input a suffix to append to the username. \
        This will create a username of '<username>_<suffix>' (Default: 'migrated'): ")
    config.set("DESTINATION", "username_suffix", username_suffix or "migrated")
    mirror = input(
        "Planning a soft cut-over migration by mirroring repos to keep both instances running (Default: 'No')? ")
    if mirror.lower() in ["yes", "y"]:
        if migration_user.get("username"):
            config.set("DESTINATION", "mirror_username",
                       migration_user["username"])
        else:
            config.set("DESTINATION", "mirror_username", "")
            print(
                f"WARNING: Destination (mirror) user not found. Please enter 'mirror_username' manually (in {config_path})")
    else:
        config.set("DESTINATION", "mirror_username", "")
    config.set("DESTINATION", "max_asset_expiration_time", "24")

    # Source instance configuration
    config.add_section("SOURCE")
    ext_src = input(
        "Migrating from an external (non-GitLab) instance (Default: 'No')? ")
    if ext_src.lower() in ["yes", "y"]:
        src = input(
            "Source (1. Bitbucket Server, 2. GitHub (Cloud or Enterprise)? ")
        if src.lower() in ["1", "1.", "bitbucket server"]:
            config.set("SOURCE", "src_type", "Bitbucket Server")
            config.set("SOURCE", "src_username", input("Username: "))
        elif src.lower() in ["2", "2.", "github"]:
            config.set("SOURCE", "src_type", "GitHub")
        else:
            print(f"Source type {src} is currently not supported")
            sys.exit(os.EX_CONFIG)
        config.set("SOURCE", "src_hostname", input(
            f"Source instance ({config.get('SOURCE', 'src_type')}) URL: "))
        config.set("SOURCE", "src_access_token", obfuscate(
            f"Source instance ({config.get('SOURCE', 'src_type')}) Personal Access Token: "))
    else:
        # Non-external source instance configuration
        config.set("SOURCE", "src_type", "GitLab")
        src_type = config.get("SOURCE", "src_type")
        config.set("SOURCE", "src_hostname", input("Source instance URL: "))
        config.set("SOURCE", "src_access_token", obfuscate(
            f"Source instance ({src_type}) Personal Access Token: "))
        lic = safe_json_response(instance.get_current_license(
            config.get("SOURCE", "src_hostname"),
            deobfuscate(config.get("SOURCE", "src_access_token"))))
        if lic and is_error_message_present(lic):
            print(
                f"Insufficient token permission to GET license plan, setting default (core/free):\n{lic}")
        config.set("SOURCE", "src_tier", lic.get(
            "plan", "core") if lic else "core")
        source_group = input(
            "Are you migrating from a parent group to a new instance, e.g. gitlab.com to self-managed (Default: 'No')? ")
        if source_group.lower() in ["yes", "y"]:
            config.set("SOURCE", "src_parent_group_id", input(
                "Source group ID (Group -> Settings -> General): "))
            src_group = safe_json_response(
                groups.get_group(
                    config.getint("SOURCE", "src_parent_group_id"),
                    config.get("SOURCE", "src_hostname"),
                    deobfuscate(config.get("SOURCE", "src_access_token"))))
            if src_group and src_group.get("full_path"):
                config.set("SOURCE", "src_parent_group_path",
                           src_group["full_path"])
            else:
                config.set("SOURCE", "src_parent_group_path", "")
                print(
                    f"WARNING: Source group not found. Please enter 'src_parent_group_id' and 'src_parent_group_path' manually (in {config_path})")
        export_import_timeout = input(
            "Timeout (in seconds) for group or project export or import (Default: '3600'): ")
        config.set("SOURCE", "export_import_timeout",
                   export_import_timeout or "3600")

        # GitLab source/destination instance registry configuration
        migrating_registries = input(
            "Are you migrating any container registries (Default: 'No')? ")
        if migrating_registries.lower() in ["yes", "y"]:
            config.set("SOURCE", "src_registry_url", input(
                "Source instance Container Registry URL: "))
            test_registries(deobfuscate(config.get("SOURCE", "src_access_token")), config.get(
                "SOURCE", "src_registry_url"), migration_user)
            config.set("DESTINATION", "dstn_registry_url", input(
                "Destination instance Container Registry URL: "))
            test_registries(deobfuscate(config.get("DESTINATION", "dstn_access_token")), config.get(
                "DESTINATION", "dstn_registry_url"), migration_user)

        # GitLab project export/update configuration
        config.add_section("EXPORT")
        location = input(
            "Staging location for exported projects and groups, AWS (projects only) or filesystem (Default)?: ")
        if location.lower() == "aws":
            config.set("EXPORT", "location", "aws")
            config.set("EXPORT", "s3_name", input("AWS S3 bucket name: "))
            region = input("AWS S3 bucket region (Default: 'us-east-1'): ")
            config.set("EXPORT", "s3_region",
                       region if region else "us-east-1")
            config.set("EXPORT", "s3_access_key_id",
                       obfuscate("AWS S3 bucket access key ID: "))
            config.set("EXPORT", "s3_secret_access_key",
                       obfuscate("AWS S3 bucket secret access key: "))
            try:
                print("Setting entered AWS Access Key ID and Secret Access Key...")
                aws.set_access_key_id(deobfuscate(
                    config.get("EXPORT", "s3_access_key_id")))
                aws.set_secret_access_key(deobfuscate(
                    config.get("EXPORT", "s3_secret_access_key")))
            except NoOptionError as noe:
                print(f"Failed to get AWS S3 key, with error:\n{noe}")
                sys.exit(os.EX_CONFIG)
            except Exception as e:
                print(f"Failed to set AWS S3 key, with error:\n{e}")
                sys.exit(os.EX_CONFIG)
        else:
            config.set("EXPORT", "location", "filesystem")

        abs_path = input(
            f"ABSOLUTE path for exporting/updating projects (Default: {os.getcwd()})? ")
        config.set("EXPORT", "filesystem_path",
                   abs_path if abs_path and abs_path.startswith("/") else os.getcwd())

    # CI Source configuration
    ci_src = input("Migrating from a CI Source (Default: 'No')? ")
    if ci_src.lower() in ["yes", "y"]:
        config.add_section("CI_SOURCE")
        ci_src_option = input(
            "CI Source (1. Jenkins, 2. TeamCity 3. Jenkins and TeamCity)? ")
        if ci_src_option.lower() in ["1", "1.", "jenkins"]:
            config.set("CI_SOURCE", "ci_src_type", "Jenkins")
            config.set("CI_SOURCE", "ci_src_hostname", input(
                f"CI Source instance ({config.get('CI_SOURCE', 'ci_src_type')}) URL: "))
            config.set("CI_SOURCE", "ci_src_username",
                       input("CI Source Username: "))
            config.set("CI_SOURCE", "ci_src_access_token", obfuscate(
                f"CI Source instance ({config.get('CI_SOURCE', 'ci_src_type')}) Personal Access Token: "))
        elif ci_src_option.lower() in ["2", "2.", "teamcity"]:
            config.set("CI_SOURCE", "ci_src_type", "TeamCity")
            config.set("CI_SOURCE", "ci_src_hostname", input(
                f"CI Source instance ({config.get('CI_SOURCE', 'ci_src_type')}) URL: "))
            config.set("CI_SOURCE", "ci_src_username",
                       input("CI Source Username: "))
            config.set("CI_SOURCE", "ci_src_access_token", obfuscate(
                f"CI Source instance ({config.get('CI_SOURCE', 'ci_src_type')}) Personal Access Token: "))
        elif ci_src_option.lower() in ["3", "3.", "jenkins and teamcity"]:
            # Jenkins Config
            config.add_section("JENKINS_CI_SOURCE")
            config.set("JENKINS_CI_SOURCE", "jenkins_ci_src_type", "Jenkins")
            config.set("JENKINS_CI_SOURCE", "jenkins_ci_src_hostname", input(
                f"Jenkins CI Source instance ({config.get('JENKINS_CI_SOURCE', 'jenkins_ci_src_type')}) URL: "))
            config.set("JENKINS_CI_SOURCE", "jenkins_ci_src_username",
                       input("Jenkins CI Source Username: "))
            config.set("JENKINS_CI_SOURCE", "jenkins_ci_src_access_token", obfuscate(
                f"Jenkins CI Source instance ({config.get('JENKINS_CI_SOURCE', 'jenkins_ci_src_type')}) Personal Access Token: "))
            # Teamcity Config
            config.add_section("TEAMCITY_CI_SOURCE")
            config.set("TEAMCITY_CI_SOURCE", "tc_ci_src_type", "TeamCity")
            config.set("TEAMCITY_CI_SOURCE", "tc_ci_src_hostname", input(
                f"Teamcity CI Source instance ({config.get('TEAMCITY_CI_SOURCE', 'tc_ci_src_type')}) URL: "))
            config.set("TEAMCITY_CI_SOURCE", "tc_ci_src_username",
                       input("Teamcity CI Source Username: "))
            config.set("TEAMCITY_CI_SOURCE", "tc_ci_src_access_token", obfuscate(
                f"Teamcity CI Source instance ({config.get('TEAMCITY_CI_SOURCE', 'tc_ci_src_type')}) Personal Access Token: "))
        else:
            print(f"CI Source type {ci_src_option} is currently not supported")

    # User specific configuration
    config.add_section("USER")
    keep_inactive_users = input(
        "Keep inactive users (blocked, ldap_blocked, deactivated, banned) in staged users/groups/projects (Default: 'Yes')? ")
    config.set("USER", "keep_inactive_users",
               "False" if keep_inactive_users.lower() in ["no", "n"] else "True")
    reset_pwd = input(
        "Should users receive password reset emails (Default: 'No')? ")
    config.set("USER", "reset_pwd", "True" if reset_pwd.lower()
               in ["yes", "y"] else "False")
    force_rand_pwd = input(
        "Should users be created with a randomized password (Default: 'Yes')? ")
    config.set("USER", "force_rand_pwd",
               "False" if force_rand_pwd.lower() in ["no", "n"] else "True")

    # Generic App configuration
    config.add_section("APP")
    export_import_status_check_time = input(
        "Check time (in seconds) for group or project export or import status (Default: '10'): ")
    config.set("APP", "export_import_status_check_time",
               export_import_status_check_time or "10")
    wave_spreadsheet = input(
        "(Optional) Spreadsheet containing wave information (yes or no): ")
    if wave_spreadsheet.lower() in ["yes", "y"]:
        wave_spreadsheet_path = input("Absolute path to spreadsheet: ")
        config.set("APP", "wave_spreadsheet_path", wave_spreadsheet_path)
        if wave_columns_to_include := input(
                "Provide a list of comma separate values denoting the columns you want to retain: "):
            config.set("APP", "wave_spreadsheet_columns",
                       f"[{wave_columns_to_include}]")
            # This will just put in the default mapping. Will require manual intervention
            # for further customization
            d = {x.strip(): x.strip()
                 for x in wave_columns_to_include.split(",")}
            config.set(
                "APP",
                "wave_spreadsheet_column_mapping",
                json.dumps(d)
            )
    slack = input(
        "Send alerts (logs) to Slack via Incoming WebHooks (Default: 'No')? ")
    if slack.lower() in ["yes", "y"]:
        config.set("APP", "slack_url", input(
            "Slack Incoming WebHooks URL: "))
        test_slack(config.get("APP", "slack_url"))

    mongo = input(
        "External mongodb host? (Default: 'No')? ")
    if mongo.lower() in ["yes", "y"]:
        config.set("APP", "mongo_host", input(
            "Mongo host (excluding port): "))
    else:
        config.set("APP", "mongo_host", "localhost")
        config.set("APP", "mongo_port", "27017")

    # Default implied config
    config.set("APP", "ui_port", "8000")
    config.set("APP", "processes", "4")
    config.set("APP", "ssl_verify", "True")

    write_to_file(config)


def write_to_file(config):
    """
        Helper method to write congregate config to congregate.conf

        :param: data: (dict) config object
    """
    if not os.path.isdir(f"{app_path}/data"):
        os.mkdir(f"{app_path}/data")
        os.mkdir(f"{app_path}/data/logs")
        os.mkdir(f"{app_path}/data/results")
    if config.has_option("EXPORT", "filesystem_path") and config.get(
            "EXPORT", "filesystem_path"):
        down_dir = config.get("EXPORT", "filesystem_path")
        sub_dir = "downloads"
        if not os.path.isdir("{0}/{1}".format(down_dir, sub_dir)):
            print(
                f"Filesystem path {down_dir} sub-folder 'downloads' does not exist. Creating it...")
            f_path = os.path.join(down_dir, sub_dir)
            os.makedirs(f_path)
    with open(config_path, "w") as f:
        print(f"Writing configuration to file ({config_path})...")
        config.write(f)


def test_registries(token, registry, user):
    try:
        client = from_env()
        client.login(username=user.get("username"),
                     password=token, registry=registry)
    except (APIError, TLSParameterError) as err:
        print(
            f"Failed to login to docker registry {registry}, with error:\n{err}")
        sys.exit(os.EX_NOPERM)
    except Exception as e:
        print(
            f"Login attempt to docker registry {registry} failed, with error:\n{e}")
        sys.exit(os.EX_UNAVAILABLE)


def test_slack(url):
    try:
        json_data = json.dumps({"text": "Congregate Slack alerting test",
                                "username": "WebhookBot", "icon_emoji": ":ghost:"})
        resp = requests.post(url, data=json_data.encode('ascii'),
                             headers={'Content-Type': 'application/json'})
        if resp.status_code not in [200, 202]:
            raise Exception(resp)
    except Exception as em:
        print("EXCEPTION: " + str(em))
        sys.exit(os.EX_UNAVAILABLE)


def get_sso_provider_pattern():
    options = {
        1: "email",
        2: "hash",
        3: "extern_uid",
        4: "custom"
    }
    while True:
        try:
            sso_provider_pattern_option = input(
                "Select SSO provider pattern type (1. Email, 2. Hash, 3. UID (pass-through)): ")
            if int(sso_provider_pattern_option) == 1:
                return options.get(1)
            if int(sso_provider_pattern_option) == 2:
                print(
                    "We expect to handle hashes through a JSON that looks like the following:\n{}".format(json_pretty([
                        {
                            "email": "user@email.com",
                            "externalid": "abc123"
                        }
                    ])))
                return options.get(2)
            if int(sso_provider_pattern_option) == 3:
                print(
                    "Not fully implemented yet, assuming the same 'extern_uid' is being mapped")
                return options.get(3)
            if int(sso_provider_pattern_option) == 4:
                print("Not implemented yet")
                return None
            print(f"'{sso_provider_pattern_option}' is not a valid option")
        except ValueError:
            print("Please input a number for your option")
            sys.exit(os.EX_DATAERR)


def update_config(data):
    """
        Update function used by the congregate UI

        :param: data: (dict) Config data provided by user
        :return: No update message if config wasn't changed
    """
    config = ConfigurationValidator()
    config_obj = config.as_obj()
    x = 0
    y = 0

    # Flag to track config changes
    write_new_config = False
    options_list = [d.strip("{}").replace('"', '') for d in data.split(",")]

    # Loop over current config options, per section, and compare with UI input
    # fields
    for section in config_obj.sections():
        options = config_obj.items(section)
        y += len(options)
        for (k1, v1), k in zip(options, options_list[x:y]):
            k2 = k.split(":", 1)[0]
            v2 = k.split(":", 1)[1]

            # Set new option value in case of changes
            if k1 == k2 and v2 != v1:
                write_new_config = True
                print(
                    f"Updating config option {section}/{k1} from {v1} -> {v2}")
                config_obj.set(section, k1, v2)
        x += len(options)

    if write_new_config:
        write_to_file(config_obj)
    else:
        return("No pending config changes")
