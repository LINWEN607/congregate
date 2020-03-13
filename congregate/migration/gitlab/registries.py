from docker import from_env
from docker.errors import APIError, TLSParameterError
from congregate.helpers.base_class import BaseClass
from congregate.helpers import api
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
            registry = self.are_enabled(new_id, old_id)
            if registry[0] and registry[1]:
                self.log.info(
                    "Migrating project {0} (ID: {1}) container registries".format(name, old_id))
                self.migrate(old_id, name)
                return True
            else:
                instance = "source" if not registry[0] else "destination" if not registry[1] else "source and destination"
                self.log.warning(
                    "Container registry is disabled for project {0} on {1} instance".format(name, instance))
        except Exception as e:
            self.log.error(
                "Failed to migrate project {0} (ID: {1}) container registries, with error:\n{2}".format(name, old_id, e))
            return False

    def migrate(self, old_id, name):
        try:
            # Login to source registry
            src_client = self.__login_to_registry(
                self.config.source_host, self.config.source_token, self.config.source_registry)
            response = self.projects_api.get_all_project_registry_repositories(
                old_id, self.config.source_host, self.config.source_token)
            registries = iter(response)
            for registry in registries:
                tags = self.projects_api.get_all_project_registry_repositories_tags(
                    old_id, registry["id"], self.config.source_host, self.config.source_token)
                if list(tags):
                    reg = registry["location"]
                    self.log.info("Pulling images from project {0} (ID: {1}) registry {2}".format(
                        name, old_id, reg))
                    images = src_client.images.pull(reg)
                    # 2nd argument - passing the suffix for multi path registries
                    self.__import_registries(images, reg.split("/", 1)[1])
        except TypeError as te:
            self.log.error("Project {0} (ID: {1}) registries {2} {3}".format(
                name, old_id, response, te))
        except (APIError) as err:
            self.log.error("Failed to export registry, with error:\n%s" % err)

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
                print line
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
        if self.config.parent_group_path is not None:
            return "%s/%s/%s" % (self.config.destination_registry, self.config.parent_group_path, suffix)
        return "%s/%s" % (self.config.destination_registry, suffix)
