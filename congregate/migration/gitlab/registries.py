from helpers.base_class import BaseClass
from helpers import api


class RegistryClient(BaseClass):
    # Get a list of registry repositories in a project.
    def list_registry_repositories(self, host, token, id):
        return api.list_all(host, token, "projects/%d/registry/repositories" % id)

    # Get a list of tags for given registry repository.
    def list_repository_tags(self, host, token, id, repo_id):
        return api.generate_get_request(host, token, "projects/%d/registry/repositories/%d/tags" % (id, repo_id))

    # Get details of a registry repository tag.
    def get_repository_tag_details(self, host, token, id, repo_id, tag_name):
        return api.generate_get_request(host, token, "projects/%d/registry/repositories/%d/tags/%s" % (id, repo_id, tag_name))

    def migrate_registries(self, id, old_id):
        for registry in self.list_registry_repositories(self.config.child_host, self.config.child_token, old_id):
            print(registry)