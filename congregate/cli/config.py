from os import getcwd, path, mkdir, makedirs
from ConfigParser import SafeConfigParser as ConfigParser, NoOptionError

from congregate.helpers.misc_utils import get_congregate_path, obfuscate, deobfuscate
from congregate.helpers.configuration_validator import ConfigurationValidator
from congregate.migration.gitlab.api.users import UsersApi
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.aws import AwsClient


users = UsersApi()
groups = GroupsApi()
aws = AwsClient()
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
               obfuscate("Destination instance Access token: "))
    migration_user = users.get_current_user(config.get("DESTINATION", "dstn_hostname"),
                                            deobfuscate(config.get("DESTINATION", "dstn_access_token")))
    if migration_user.get("id", None) is not None:
        config.set("DESTINATION", "import_user_id", str(migration_user["id"]))
    else:
        config.set("DESTINATION", "import_user_id", "")
        print("WARNING: Destination user not found. Please enter 'import_user_id' manually (in {})".format(
            config_path))
    shared_runners_enabled = raw_input(
        "Enable shared runners on destination instance (default: True): ")
    config.set("DESTINATION", "shared_runners_enabled",
               "False" if shared_runners_enabled and shared_runners_enabled.lower() == "false" else "True")
    project_suffix = raw_input(
        "Append suffix to project found on destination instance (default: False): ")
    config.set("DESTINATION", "project_suffix",
               "True" if project_suffix and project_suffix.lower() == "true" else "False")
    max_import_retries = raw_input(
        "Max no. of project import retries (default: 3): ")
    config.set("DESTINATION", "max_import_retries",
               max_import_retries if max_import_retries else "3")

    # External source instance settings
    ext_src_url = raw_input(
        "Migrating from an external (non-GitLab) instance? Input external source URL: ")
    if ext_src_url and not "gitlab" in ext_src_url.lower():
        config.add_section("EXT_SRC")
        config.set("EXT_SRC", "url", ext_src_url)
        print("NOTE: External source migration is currently limited to mirroring through http/https. A master username and password is required to set up mirroring in each shell project.")
        config.set("EXT_SRC", "username", raw_input("Username: "))
        config.set("EXT_SRC", "password", obfuscate("Password: "))
        repo_path = raw_input(
            "Absolute path to JSON file containing repo information: ")
        config.set("EXT_SRC", "repo_path", "{0}{1}"
                   .format("" if repo_path.startswith("/") else path.join(app_path, ""), repo_path))

    if not config.has_section("EXT_SRC"):
        # Non-external source instance settings
        config.add_section("SOURCE")
        config.set("SOURCE", "src_hostname",
                   raw_input("Source instance Host: "))
        config.set("SOURCE", "src_access_token", obfuscate(
            "Source instance Access token: "))
        config.set("SOURCE", "src_registry_url", raw_input(
            "Source instance Container Registry URL: "))
        max_export_wait_time = raw_input(
            "Max wait time (in seconds) for project export status (default: 3600): ")
        config.set("SOURCE", "max_export_wait_time",
                   max_export_wait_time if max_export_wait_time else "3600")

        # Non-external destination instance settings
        config.set("DESTINATION", "dstn_registry_url", raw_input(
            "Destination instance Container Registry URL: "))
        config.set("DESTINATION", "parent_group_id",
                   raw_input("Migrating to a parent group (e.g. gitlab.com)? Parent group ID (Group -> Settings -> General): "))

        if config.has_option("DESTINATION", "parent_group_id") and config.get("DESTINATION", "parent_group_id"):
            group = groups.get_group(config.getint("DESTINATION", "parent_group_id"),
                                     config.get("DESTINATION",
                                                "dstn_hostname"),
                                     deobfuscate(config.get("DESTINATION", "dstn_access_token"))).json()
            if group.get("full_path", None) is not None:
                config.set("DESTINATION", "parent_group_path",
                           group["full_path"])
            else:
                config.set("DESTINATION", "parent_group_path", "")
                print("WARNING: Destination group not found. Please enter 'parent_group_id' and 'parent_group_path' manually (in {})".format(
                    config_path))
            config.set("DESTINATION", "group_sso_provider",
                       raw_input("Migrating to a group with SAML SSO enabled? Input SSO provider (auth0, adfs, etc.): "))

        username_suffix = raw_input(
            "To avoid username collision, please input suffix to append: ")
        config.set("DESTINATION", "username_suffix",
                   username_suffix if username_suffix != "_" else "")
        mirror = raw_input(
            "Planning a soft cut-over migration by mirroring repos to keep both instances running? Yes or No (default): ")
        if mirror and mirror.lower() != "no":
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
        
        # Project export/update settings
        config.add_section("EXPORT")
        location = raw_input(
            "Staging location for exported projects and groups, AWS (projects only) or filesystem (default): ")
        if location.lower() == "aws":
            config.set("EXPORT", "location", "aws")
            config.set("EXPORT", "s3_name", raw_input("AWS S3 bucket name: "))
            region = raw_input("AWS S3 bucket region (default: us-east-1): ")
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
            "ABSOLUTE path for exporting/updating projects (default: {}): ".format(getcwd()))
        config.set("EXPORT", "filesystem_path",
                   abs_path if abs_path and abs_path.startswith("/") else getcwd())

    # User specific settings
    config.add_section("USER")
    keep_blocker_users = raw_input(
        "Keep blocked users in staged users/groups/projects (default: False): ")
    config.set("USER", "keep_blocked_users",
               "True" if keep_blocker_users and keep_blocker_users.lower() == "true" else "False")
    reset_pwd = raw_input(
        "Users receive password reset emails (default: True): ")
    config.set("USER", "reset_pwd",
               "False" if reset_pwd and reset_pwd.lower() == "false" else "True")
    force_rand_pwd = raw_input(
        "Users are created with a randomized password (default: False): ")
    config.set("USER", "force_rand_pwd",
               "True" if force_rand_pwd and force_rand_pwd.lower() == "true" else "False")

    # Generic App settings
    config.add_section("APP")
    no_of_threads = raw_input("Number of threads (default: 2, max: 4): ")
    config.set("APP", "no_of_threads", no_of_threads if no_of_threads and int(
        no_of_threads) < 5 else "2")
    export_import_wait_time = raw_input(
        "Wait time (in seconds) for project export/import status (default: 30): ")
    config.set("APP", "export_import_wait_time",
               export_import_wait_time if export_import_wait_time else "30")

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
