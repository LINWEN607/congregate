from docker import from_env, client
from docker.errors import APIError, TLSParameterError
from helpers.base_class import BaseClass
from helpers import api
from migration.gitlab.users import UsersClient
from migration.gitlab.projects import ProjectsClient


class RegistryClient(BaseClass):
    def __init__(self):
        self.users = UsersClient()
        self.projects = ProjectsClient()
        super(RegistryClient, self).__init__()

    def enabled(self, new_id, old_id):
        src = self.__enabled(self.config.child_host, self.config.child_token, old_id)
        dest = self.__enabled(self.config.parent_host,
                              self.config.parent_token, old_id)
        return src and dest

    def __enabled(self, host, token, id):
        project = api.generate_get_request(host, token, "projects/%d" % id).json()
        if project.get("container_registry_enabled"):
            return project["container_registry_enabled"]
        return False

    # Get a list of registry repositories in a project
    def __list_registry_repositories(self, host, token, id):
        return api.list_all(host, token, "projects/%d/registry/repositories" % id)

    # Get a list of tags for given registry repository
    def __list_repository_tags(self, host, token, id, repo_id):
        return api.list_all(host, token, "projects/%d/registry/repositories/%d/tags" % (id, repo_id))

    # Get details of a registry repository tag
    def __get_repository_tag_details(self, host, token, id, repo_id, tag_name):
        return api.generate_get_request(host, token, "projects/%d/registry/repositories/%d/tags/%s" % (id, repo_id, tag_name))

    def migrate_registries(self, id, old_id):
        try:
            # Login to source registry
            client = self.__login_to_registry(self.config.child_host, self.config.child_token, self.config.child_registry)
            registries = self.__list_registry_repositories(self.config.child_host, self.config.child_token, old_id)
            for registry in registries:
                tags = self.__list_repository_tags(
                    self.config.child_host, self.config.child_token, old_id, registry["id"])
                if list(tags):
                    reg = registry["location"]
                    self.log.info("Pulling images from registry %s" % reg)
                    images = client.images.pull(reg)
                    self.__import_registries(images, registry)
        except (APIError) as err:
            self.log.error("Failed to export registry, with error:\n%s" % err)

    def __import_registries(self, images, registry):
        try:
            # Login to destination registry
            client = self.__login_to_registry(self.config.parent_host, self.config.parent_token, self.config.parent_registry)
            new_reg = "%s/%s" % (self.config.parent_registry, registry["path"])
            for image in images:
                for tag in image.tags:
                    # TODO: use a key value instead
                    tag_name = tag.replace(self.config.child_registry, "").split(":")[-1]
                    if image.tag(new_reg, tag_name):
                        self.log.info(
                            "Migrating tag %s to registry %s" % (tag_name, new_reg))
                        for line in client.images.push(new_reg, stream=True, decode=True):
                            print(line)
                self.log.info("Removing stored image (ID) %s" % image.id)
                client.images.remove(image.id, force=True)
        except (APIError) as err:
            self.log.error("Failed to import registry, with error:\n%s" % err)

    def __login_to_registry(self, host, token, registry):
        try:
            client = from_env()
            client.login(username=self.users.get_current_user(host, token).json()["username"],
                         password=token,
                         registry=registry)
            return client
        except (APIError, TLSParameterError) as err:
            self.log.error("Failed to login to docker registry %s, with error:\n%s" % (registry, err))
