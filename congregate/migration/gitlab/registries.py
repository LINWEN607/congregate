from requests.exceptions import RequestException

from docker import from_env
from docker.errors import APIError, TLSParameterError
from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import is_error_message_present
from congregate.migration.gitlab.api.users import UsersApi
from congregate.migration.gitlab.api.projects import ProjectsApi


class RegistryClient(BaseClass):
    def __init__(self):
        self.users = UsersApi()
        self.projects_api = ProjectsApi()
        super(RegistryClient, self).__init__()

    def are_enabled(self, new_id, old_id):
        src = self.is_enabled(self.config.source_host,
                              self.config.source_token, old_id)
        dest = self.is_enabled(self.config.destination_host,
                               self.config.destination_token, new_id)
        return (src, dest)

    def is_enabled(self, host, token, pid):
        project = self.projects_api.get_project(pid, host, token).json()
        return project.get("container_registry_enabled", False)

    def migrate_registries(self, old_id, new_id, name):
        try:
            reg = self.are_enabled(new_id, old_id)
            if reg[0] and reg[1]:
                return self.migrate(old_id, name)
            else:
                self.log.warning("Container registry is disabled for project {0} on {1} instance".format(
                    name, "source" if not reg[0] else "destination" if not reg[1] else "source and destination"))
        except Exception as e:
            self.log.error(
                "Failed to migrate container registries for project {0}, with error:\n{1}".format(name, e))
            return False

    def migrate(self, old_id, name):
        try:
            # Login to source registry
            src_client = self.__login_to_registry(
                self.config.source_host, self.config.source_token, self.config.source_registry)
            resp = self.projects_api.get_all_project_registry_repositories(
                old_id, self.config.source_host, self.config.source_token)
            regs = iter(resp)
            self.log.info(
                "Migrating project {0} (ID: {1}) container registries".format(name, old_id))
            for reg in regs:
                if is_error_message_present(reg) or not reg:
                    self.log.error(
                        "Failed to fetch container registries ({0}) for project {1}".format(reg, name))
                    return False
                tags = self.projects_api.get_all_project_registry_repositories_tags(
                    old_id, reg["id"], self.config.source_host, self.config.source_token)
                if list(tags):
                    reg_loc = reg["location"]
                    self.log.info("Pulling images from project {0} (ID: {1}) registry {2}".format(
                        name, old_id, reg_loc))
                    images = src_client.images.pull(reg_loc)
                    # 2nd argument - passing the suffix for multi path registries
                    self.__import_registries(images, reg_loc.split("/", 1)[1])
            return True
        except TypeError as te:
            self.log.error("Project {0} (ID: {1}) registries {2} {3}".format(
                name, old_id, resp, te))
            return False
        except APIError as ae:
            self.log.error(
                "Failed to export registry, with error:\n{}".format(ae))
            return False
        except RequestException as re:
            self.log.error(
                "Failed to migrate container registries for project {0}, with error:\n{1}".format(name, re))
            return False

    def __import_registries(self, images, sufix):
        try:
            # Login to destination registry
            dest_client = self.__login_to_registry(
                self.config.destination_host,
                self.config.destination_token,
                self.config.destination_registry)
            new_reg = self.generate_destination_registry_url(sufix).lower()
            for image in images:
                for tag in image.tags:
                    # TODO: use a key value instead
                    tag_name = tag.replace(
                        self.config.source_registry, "").split(":")[-1]
                    if image.tag(new_reg, tag_name):
                        self.log.debug("Created tag %s" % tag_name)
            self.log.info("Migrating images to registry %s" % new_reg)
            for line in dest_client.images.push(new_reg, stream=True, decode=True):
                print(line)
            self.log.info("Removing locally stored source images")
            for image in images:
                dest_client.images.remove(image.id, force=True)
        except (APIError) as err:
            self.log.error("Failed to import registry, with error:\n%s" % err)

    def __login_to_registry(self, host, token, registry):
        try:
            client = from_env()
            client.login(username=self.users.get_current_user(host, token)["username"],
                         password=token,
                         registry=registry)
            return client
        except (APIError, TLSParameterError) as err:
            self.log.error(
                "Failed to login to docker registry %s, with error:\n%s" % (registry, err))

    def generate_destination_registry_url(self, suffix):
        if self.config.dstn_parent_group_path is not None:
            return "%s/%s/%s" % (self.config.destination_registry, self.config.dstn_parent_group_path, suffix)
        return "%s/%s" % (self.config.destination_registry, suffix)
