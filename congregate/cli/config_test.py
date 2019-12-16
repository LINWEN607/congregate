import base64

from sys import version_info
from getpass import getpass
from ConfigParser import SafeConfigParser as ConfigParser

from congregate.helpers.misc_utils import get_congregate_path
from congregate.migration.gitlab.api.users import UsersApi
from congregate.migration.gitlab.api.groups import GroupsApi


# Alias to use until we migrate to Python 3
if version_info.major == 3:
    pass
elif version_info.major == 2:
    try:
        input = raw_input
    except NameError:
        pass
else:
    print("Unknown Python version - input function not safe")
    exit(1)

users = UsersApi()
groups = GroupsApi()

def configure():
    app_path = get_congregate_path()
    generate_config(app_path)


def obfuscate(prompt):
    return base64.b64encode(getpass(prompt))


def deobfuscate(secret):
    return base64.b64decode(secret)


def generate_config(app_path):
    config = ConfigParser()
    
    # External source instance info
    config.add_section("EXTERNAL")
    external_source = input("Migration source (default: GitLab): ")
    if external_source and external_source.lower() != "gitlab":
        config.set("EXTERNAL", "source", external_source)
        print("NOTE: External migration is currently limited to mirroring through http/https. A master username and password is required to set up mirroring in each shell project.")
        config.set("EXTERNAL", "username", input("Username: "))
        config.set("EXTERNAL", "password", obfuscate("Password: "))
        repos_path = input("Path to JSON file containing repo information: ")
        config.set("EXTERNAL", "repos", "{0}{1}"
            .format(app_path if repos_path.startswith("/") else "", repos_path))
    else:
        config.set("EXTERNAL", "source", str(False))

    # Generic destination instance info
    config.add_section("DESTINATION")
    config.set("DESTINATION", "hostname", input("Destination instance Host: "))
    config.set("DESTINATION", "access_token", obfuscate("Destination instance Access token: "))
    migration_user = users.get_current_user(config.get("DESTINATION", "hostname"),
        deobfuscate(config.get("DESTINATION", "access_token")))
    config.set("DESTINATION", "import_user_id", str(migration_user["id"]))

    # Non-external instance info
    if not config.getboolean("EXTERNAL", "source"):
        config.add_section("SOURCE")
        config.set("SOURCE", "hostname", input("Source instance Host: "))
        config.set("SOURCE", "acess_token", obfuscate("Source instance Access token: "))
        config.set("SOURCE", "registry_url", input("Source instance Container Registry URL: "))
        
        config.set("DESTINATION", "registry_url", input("Destination instance Container Registry URL: "))
        config.set("DESTINATION", "parent_group_id",
            input("Migrating to a parent group (e.g. gitlab.com)? Please input parent group ID (Group -> Settings -> General): "))
        
        if config.get("DESTINATION", "parent_group_id"):
            config.set("DESTINATION", "parent_group_path",
                groups.get_group(config.get("DESTINATION", "parent_group_id"),
                    config.get("DESTINATION", "hostname"),
                    deobfuscate(config.get("DESTINATION", "access_token"))).json()["full_path"])
            print("NOTE: Congregate is going to set all internal groups to private. You can change this setting later.")
            config.set("DESTINATION", "private_groups", str(True))
            config.set("DESTINATION", "group_sso_provider",
                input("Migrating to a group with SAML SSO enabled? Please input SSO provider (auth0, adfs, etc.): "))
            username_suffix = input("To avoid username collision, please input suffix to append: ")
            config.set("DESTINATION", "username_suffix", username_suffix if username_suffix != "_" else "")

        mirror = input("Planning a soft cut-over migration by mirroring repos to keep both instances running? ")
        config.set("DESTINATION", "mirror_username",
            migration_user["username"] if mirror and mirror.lower() != "no" else "")

        config.add_section("EXPORT")
        config.set("EXPORT", "location", input("Input staging location for exported projects [filesystem, aws]? (default: filesystem) "))

    with open("{}/data/congregate.conf".format(app_path), "w") as f:
        config.write(f)
