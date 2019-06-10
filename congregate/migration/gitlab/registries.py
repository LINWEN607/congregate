from helpers.base_class import BaseClass
from helpers import api
import docker


class RegistryClient(BaseClass):
    def __init__(self):
        self.client = docker.from_env()
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
        for image in self.client.images.pull(repo):
            for tag in image.tags:
                image.tag(new_registry_path, tag)
            self.client.images.push(new_registry_path)
            self.client.images.remove(repo)
            self.client.images.remove(new_registry_path)
