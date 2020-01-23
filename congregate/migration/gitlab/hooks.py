import json

from requests.exceptions import RequestException

from congregate.helpers.base_class import BaseClass
from congregate.helpers import api
from congregate.helpers.misc_utils import get_dry_log


class HooksClient(BaseClass):
    def get_all_system_hooks(self, host, token):
        """
        Get a list of all system hooks

        GitLab API Doc: https://docs.gitlab.com/ee/api/system_hooks.html#list-system-hooks

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator returning JSON of each result from GET /hooks
        """
        return api.list_all(host, token, "hooks")

    def create_system_hook(self, host, token, data):
        """
        Add a new system hook

        GitLab API Doc: https://docs.gitlab.com/ee/api/system_hooks.html#add-new-system-hook

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: url: (str) The hook URL
            :return: Response object containing the response to POST /hooks
        """
        return api.generate_post_request(host, token, "hooks", json.dumps(data))

    def get_all_project_hooks(self, host, token, pid):
        """
        Get a list of project hooks

        GitLab API Doc: https://docs.gitlab.com/ee/api/projects.html#list-project-hooks

            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :param: pid: (int) GitLab project ID
            :yield: Generator returning JSON of each result from GET /projects/:id/hooks
        """
        return api.list_all(host, token, "projects/{}/hooks".format(pid))

    def add_project_hook(self, host, token, pid, data):
        """
        Add a hook to a specified project

        GitLab API doc: https://docs.gitlab.com/ee/api/projects.html#add-project-hook

            :param: pid: (int) GitLab project ID
            :param: data: (dict) Object containing the various data requried for creating a hook. Refer to the link above for specific examples
            :return: Response object containing the response to POST /projects/:id/hooks
        """
        return api.generate_post_request(host, token, "projects/{}/hooks".format(pid), json.dumps(data))

    def migrate_system_hooks(self, dry_run=True):
        try:
            response = self.get_all_system_hooks(
                self.config.source_host, self.config.source_token)
            s_hooks_src = iter(response)
            # used to check if hook already exists
            s_hooks_dstn = list(self.get_all_system_hooks(
                self.config.destination_host, self.config.destination_token))
            for h in s_hooks_dstn:
                h.pop("id", None)
                h.pop("created_at", None)
            for hook in s_hooks_src:
                self.log.info("{0}Migrating system hook {1} (ID: {2})".format(
                    get_dry_log(dry_run), hook["url"], hook["id"]))
                hook.pop("id", None)
                hook.pop("created_at", None)
                if not dry_run and not hook in s_hooks_dstn:
                    # hook does not include secret token
                    self.create_system_hook(
                        self.config.destination_host, self.config.destination_token, hook)
        except TypeError as te:
            self.log.error("System hooks {0} {1}".format(response, te))
        except RequestException as re:
            self.log.error(
                "Failed to migrate system hooks, with error:\n{}".format(re))

    def migrate_project_hooks(self, old_id, new_id, name):
        try:
            response = self.get_all_project_hooks(
                self.config.source_host, self.config.source_token, old_id)
            p_hooks = iter(response)
            for hook in p_hooks:
                self.log.info("Migrating project {0} (ID: {1}) hook {2} (ID: {3})".format(
                    name, old_id, hook["url"], hook["id"]))
                hook.pop("created_at", None)
                hook["project_id"] == new_id
                # hook does not include secret token
                self.add_project_hook(
                    self.config.destination_host, self.config.destination_token, new_id, hook)
        except TypeError as te:
            self.log.error("Project {0} (ID: {1}) hooks {2} {3}".format(
                name, old_id, response, te))
            return False
        except RequestException as re:
            self.log.error(
                "Failed to migrate project {0} (ID: {1}) hooks, with error:\n{2}".format(name, old_id, re))
            return False
        else:
            return True
