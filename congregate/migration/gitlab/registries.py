import docker

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

    # Get a list of registry repositories in a project.
    def list_registry_repositories(self, host, token, id):
        return api.list_all(host, token, "projects/%d/registry/repositories" % id)

    # Get a list of tags for given registry repository.
    def list_repository_tags(self, host, token, id, repo_id):
        return api.generate_get_request(host, token, "projects/%d/registry/repositories/%d/tags" % (id, repo_id))

    # Get details of a registry repository tag.
    def get_repository_tag_details(self, host, token, id, repo_id, tag_name):
        return api.generate_get_request(host, token, "projects/%d/registry/repositories/%d/tags/%s" % (id, repo_id, tag_name))

    def migrate_registries(self, id, old_id, new_project_path):
        for registry in self.list_registry_repositories(self.config.child_host, self.config.child_token, old_id):
            new_registry_path = "%s/%s" % (self.config.parent_container_registry_url, new_project_path)
            self.migrate_container(registry, new_registry_path)

    def migrate_container(self, old_registry, new_registry_path):
        repo = old_registry["location"]
        client = self.login_to_docker_registries()
        for image in client.images.pull(repo):
            for tag in image.tags:
                image.tag(new_registry_path, tag)
            client.images.push(new_registry_path)
            client.images.remove(repo)
            client.images.remove(new_registry_path)

    def login_to_docker_registries(self):
        try:
            client = docker.from_env()
            old_user = self.get_user(self.config.child_host, self.config.child_token)
            new_user = self.get_user(self.config.parent_host, self.config.parent_token)
            client.login(username=old_user, password=self.config.child_token, registry=self.config.child_container_registry_url)
            client.login(username=new_user, password=self.config.parent_token, registry=self.config.parent_container_registry_url)
            return client
        except (APIError, TLSParameterError) as err:
            self.log.error("Unable to login to docker registry, failing with error:\n%s" % err)

    def get_user(self, host, token):
        return self.users.get_current_user(host, token).json()["username"]