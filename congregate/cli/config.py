from base64 import b64encode, b64decode
import getpass
from os import getcwd, path, mkdir, makedirs
from ConfigParser import SafeConfigParser as ConfigParser, NoOptionError

import binascii
import json
import requests

from docker import from_env
from docker.errors import APIError, TLSParameterError

from congregate.helpers.misc_utils import get_congregate_path, obfuscate, deobfuscate
from congregate.helpers.configuration_validator import ConfigurationValidator
from congregate.migration.gitlab.api.users import UsersApi
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.registries import RegistryClient
from congregate.aws import AwsClient


users = UsersApi()
groups = GroupsApi()
aws = AwsClient()
reg_client = RegistryClient()
app_path = get_congregate_path()
config_path = "{}/data/congregate.conf".format(app_path)

"""
    CLI for configuring congregate
"""


def generate_config():
    """
        CLI for generating congregate.conf
    """
    config = ConfigParser(allow_no_value=True)
    # Generic destination instance settings
    config.add_section("DESTINATION")
    config.set("DESTINATION", "dstn_hostname",
               raw_input("Destination instance Host: "))
    config.set("DESTINATION", "dstn_access_token",
               obfuscate("Destination instance GitLab access token (Settings -> Access Tokens): "))
    migration_user = users.get_current_user(config.get("DESTINATION", "dstn_hostname"),
                                            deobfuscate(config.get("DESTINATION", "dstn_access_token")))
    if migration_user.get("id", None) is not None:
        config.set("DESTINATION", "import_user_id", str(migration_user["id"]))
    else:
        config.set("DESTINATION", "import_user_id", "")
        print("WARNING: Destination user not found. Please enter 'import_user_id' manually (in {})".format(
            config_path))
    shared_runners_enabled = raw_input(
        "Enable shared runners on destination instance? (Default: Yes): ")
    config.set("DESTINATION", "shared_runners_enabled",
               "False" if shared_runners_enabled.lower() in ["no", "n"] else "True")
    project_suffix = raw_input(
        "Append suffix to project found on destination instance? (Default: No): ")
    config.set("DESTINATION", "project_suffix",
               "True" if project_suffix.lower() in ["yes", "y"] else "False")
    max_import_retries = raw_input(
        "Max no. of project import retries (Default: 3): ")
    config.set("DESTINATION", "max_import_retries",
               max_import_retries if max_import_retries else "3")

    dstn_group = raw_input(
        "Are you migrating to a parent group, e.g. gitlab.com? (Default: No) ")
    if dstn_group.lower() in ["yes", "y"]:
        config.set("DESTINATION", "dstn_parent_group_id", raw_input(
            "Parent group ID (Group -> Settings -> General): "))
        group = groups.get_group(config.getint("DESTINATION", "dstn_parent_group_id"), config.get(
            "DESTINATION", "dstn_hostname"), deobfuscate(config.get("DESTINATION", "dstn_access_token"))).json()
        if group.get("full_path", None) is not None:
            config.set("DESTINATION", "dstn_parent_group_path",
                       group["full_path"])
        else:
            config.set("DESTINATION", "dstn_parent_group_path", "")
            print("WARNING: Destination group not found. Please enter 'dstn_parent_group_id' and 'dstn_parent_group_path' manually (in {})".format(
                config_path))
        config.set("DESTINATION", "group_sso_provider",
                    raw_input("Migrating to a group with SAML SSO enabled? Input SSO provider (auth0, adfs, etc.): "))
        if config.get("DESTINATION", "group_sso_provider"):
            config.set("DESTINATION", "group_sso_provider_pattern", get_sso_provider_pattern())

    username_suffix = raw_input(
        "To avoid username collision, please input suffix to append to username: ")
    config.set("DESTINATION", "username_suffix",
               username_suffix if username_suffix != "_" else "")
    mirror = raw_input(
        "Planning a soft cut-over migration by mirroring repos to keep both instances running? (Default: No): ")
    if mirror.lower() in ["yes", "y"]:
        if migration_user.get("username", None) is not None:
            config.set("DESTINATION", "mirror_username",
                       migration_user["username"])
        else:
            config.set("DESTINATION", "mirror_username", "")
            print("WARNING: Destination (mirror) user not found. Please enter 'mirror_username' manually (in {})".format(
                config_path))
    else:
        config.set("DESTINATION", "mirror_username", "")

    config.set("DESTINATION", "max_asset_expiration_time", "24")

    ext_src = raw_input(
        "Migrating from an external (non-GitLab) instance? (Default: No) ")
    if ext_src.lower() in ["yes", "y"]:
        # External source instance settings
        config.add_section("EXT_SRC")
        src = raw_input(
            "Source (1. Bitbucket Server, 2. GitHub, 3. Bitbucket Cloud, 4. Subversion)? ")
        if src.lower() in ["1", "1.", "bitbucket server"]:
            config.add_section("SOURCE")
            config.set("SOURCE", "src_type", "Bitbucket Server")
            config.set("EXT_SRC", "url", raw_input("URL: "))
            config.set("EXT_SRC", "username", raw_input("Username: "))
            config.set("EXT_SRC", "token", obfuscate("Password/Personal Access Token: "))
            repo_path = raw_input(
                "Absolute path to JSON file containing repo information: ")
            config.set("EXT_SRC", "repo_path", "{0}{1}"
                       .format("" if repo_path.startswith("/") else path.join(app_path, ""), repo_path))
        else:
            print("Source type {} is currently not supported".format(src))
    else:
        # Non-external source instance settings
        config.add_section("SOURCE")
        config.set("SOURCE", "src_type", "gitlab")
        config.set("SOURCE", "src_hostname",
                   raw_input("Source instance Host: "))
        config.set("SOURCE", "src_access_token", obfuscate(
            "Source instance GitLab access token  (Settings -> Access tokens): "))
        source_group = raw_input(
            "Are you migrating from a parent group to a new instance, e.g. gitlab.com to self-managed? (Default: No) ")
        if source_group.lower() in ["yes", "y"]:
            config.set("SOURCE", "src_parent_group_id", raw_input(
                "Source group ID (Group -> Settings -> General): "))
            src_group = groups.get_group(config.getint("SOURCE", "src_parent_group_id"), config.get(
                "SOURCE", "src_hostname"), deobfuscate(config.get("SOURCE", "src_access_token"))).json()
            if src_group.get("full_path", None) is not None:
                config.set("SOURCE", "src_parent_group_path",
                           src_group["full_path"])
            else:
                config.set("SOURCE", "src_parent_group_path", "")
                print("WARNING: Source group not found. Please enter 'src_parent_group_id' and 'src_parent_group_path' manually (in {})".format(
                    config_path))

        migrating_registries = raw_input(
            "Are you migrating any container registries? (Default: No) ")
        if migrating_registries.lower() in ["yes", "y"]:
            config.set("SOURCE", "src_registry_url", raw_input(
                "Source instance Container Registry URL: "))
            test_registries(deobfuscate(config.get("SOURCE", "src_access_token")), config.get(
                "SOURCE", "src_registry_url"), migration_user)
            config.set("DESTINATION", "dstn_registry_url", raw_input(
                "Destination instance Container Registry URL: "))
            test_registries(deobfuscate(config.get("DESTINATION", "dstn_access_token")), config.get(
                "DESTINATION", "dstn_registry_url"), migration_user)
        max_export_wait_time = raw_input(
            "Max wait time (in seconds) for project export status (Default: 3600): ")
        config.set("SOURCE", "max_export_wait_time",
                   max_export_wait_time if max_export_wait_time else "3600")

        # Project export/update settings
        config.add_section("EXPORT")
        location = raw_input(
            "Staging location for exported projects and groups, AWS (projects only) or filesystem (default)?: ")
        if location.lower() == "aws":
            config.set("EXPORT", "location", "aws")
            config.set("EXPORT", "s3_name", raw_input("AWS S3 bucket name: "))
            region = raw_input("AWS S3 bucket region (Default: us-east-1): ")
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
            except NoOptionError, noe:
                print("Failed to get AWS S3 key, with error:\n{}".format(noe))
            except Exception, e:
                print("Failed to set AWS S3 key, with error:\n{}".format(e))
        else:
            config.set("EXPORT", "location", "filesystem")

        abs_path = raw_input(
            "ABSOLUTE path for exporting/updating projects? (Default: {}): ".format(getcwd()))
        config.set("EXPORT", "filesystem_path",
                   abs_path if abs_path and abs_path.startswith("/") else getcwd())

    # User specific settings
    config.add_section("USER")
    keep_blocker_users = raw_input(
        "Keep blocked users in staged users/groups/projects? (Default: No): ")
    config.set("USER", "keep_blocked_users",
               "True" if keep_blocker_users.lower() in ["yes", "y"] else "False")
    reset_pwd = raw_input(
        "Should users receive password reset emails? (Default: Yes): ")
    config.set("USER", "reset_pwd", "False" if reset_pwd.lower()
               in ["no", "n"] else "True")
    force_rand_pwd = raw_input(
        "Should users be created with a randomized password? (Default: No): ")
    config.set("USER", "force_rand_pwd",
               "True" if force_rand_pwd.lower() in ["yes", "y"] else "False")

    # Generic App settings
    config.add_section("APP")
    export_import_wait_time = raw_input(
        "Wait time (in seconds) for project export/import status (Default: 10): ")
    config.set("APP", "export_import_wait_time",
               export_import_wait_time if export_import_wait_time else "10")
    slack = raw_input(
        "Sending alerts (logs) to Slack (via Incoming WebHooks)? (Default: No): ")
    if slack.lower() in ["yes", "y"]:
        config.set("APP", "slack_url", raw_input(
            "Slack Incoming WebHooks URL: "))
        test_slack(config.get("APP", "slack_url"))

    write_to_file(config)


def write_to_file(config):
    """
        Helper method to write congregate config to congregate.conf

        :param: data: (dict) config object
    """
    if not path.isdir("{}/data".format(app_path)):
        mkdir("{}/data".format(app_path))
    if config.has_option("EXPORT", "filesystem_path") and config.get("EXPORT", "filesystem_path"):
        down_dir = config.get("EXPORT", "filesystem_path")
        sub_dir = "downloads"
        if not path.isdir("{0}/{1}".format(down_dir, sub_dir)):
            print(
                "Filesystem path {} sub-folder 'downloads' does not exist. Creating it...".format(down_dir))
            f_path = path.join(down_dir, sub_dir)
            makedirs(f_path)
    with open(config_path, "w") as f:
        print("Writing configuration to file ({})...".format(config_path))
        config.write(f)


def test_registries(token, registry, user):
    try:
        client = from_env()
        client.login(username=user.get("username", None),
                     password=token, registry=registry)
    except (APIError, TLSParameterError) as err:
        print("Failed to login to docker registry {0}, with error:\n{1}".format(
            registry, err))
        exit()
    except Exception as e:
        print("Login attempt to docker registry {0} failed, with error:\n{1}".format(
            registry, e))
        exit()


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
        exit()

def get_sso_provider_pattern():
    options = {
        1: "email",
        2: "hash",
        3: "custom"
    }
    while True:
        try:
            sso_provider_pattern_option = raw_input("Select SSO provider pattern type (1. Email, 2. Hash, 3. Custom")
            if int(sso_provider_pattern_option) == 1:
                return options.get(1)
            elif int(sso_provider_pattern_option) == 2:
                print "Hashes are currently not easily migrateable. We will input a placeholder, but support will need to correct this after the migration."
                return None
            elif int(sso_provider_pattern_option) == 3:
                print "Not implemented yet"
                return None
            else:
                print "Choose a valid option"
        except ValueError:
            print "Please input a number for your option"

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

    # Loop over current config options, per section, and compare with UI input fields
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
                    "Updating config option {0}/{1} from {2} -> {3}".format(section, k1, v1, v2))
                config_obj.set(section, k1, v2)
        x += len(options)

    if write_new_config:
        write_to_file(config_obj)
    else:
        return("No pending config changes")
