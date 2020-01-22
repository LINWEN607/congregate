import json

from requests.exceptions import RequestException

from congregate.helpers.base_class import BaseClass
from congregate.helpers import api
from congregate.helpers.misc_utils import json_pretty, get_dry_log


class BadgesClient(BaseClass):
    def get_all_group_badges(self, host, token, gid):
        """
        List all badges of a group

        GitLab API doc: https://docs.gitlab.com/ee/api/group_badges.html#list-all-badges-of-a-group

            :param: id: (int) GitLab group ID
            :yield: Generator containing JSON from GET /groups/:id/badges
        """
        return api.list_all(host, token, "groups/%d/badges" % gid)

    def add_group_badge(self, host, token, gid, data):
        """
        Add a badge to a group

        GitLab API doc: https://docs.gitlab.com/ee/api/group_badges.html#add-a-badge-to-a-group

            :param: id: (int) GitLab group ID
            :param: data: (dict) Object containing the various data requried for creating a badge. Refer to the link above for specific examples
            :return: Response object containing the response to POST /groups/:id/badges
        """
        return api.generate_post_request(host, token, "groups/%d/badges" % gid, json.dumps(data))

    def get_all_project_badges(self, host, token, pid):
        """
        List all badges of a project

        GitLab API doc: https://docs.gitlab.com/ee/api/project_badges.html#list-all-badges-of-a-project

            :param: pid: (int) GitLab project ID
            :param: host: (str) GitLab host URL
            :param: token: (str) Access token to GitLab instance
            :yield: Generator containing JSON from GET /projects/:id/badges
        """
        return api.list_all(host, token, "projects/%d/badges" % pid)

    def edit_project_badge(self, host, token, pid, badge_id, data=None):
        """
        Edit a badge of a project

        GitLab API doc: https://docs.gitlab.com/ee/api/project_badges.html#edit-a-badge-of-a-project

            :param: pid: (int) GitLab project ID
            :param: badge_id: (int) The badge ID
            :param: link_url: (str) URL of the badge link
            :param: image_url: (str) URL of the badge image
            :return: Response object containing the response to PUT /projects/:id/badges/:badge_id
        """
        return api.generate_put_request(host, token, "projects/%d/badges/%d" % (pid, badge_id), json.dumps(data))

    def migrate_group_badges(self, old_id, new_id, parent_group_path, dry_run=True):
        try:
            response = self.get_all_group_badges(
                self.config.source_host, self.config.source_token, old_id)
            badges = iter(response)
            for badge in badges:
                # split after hostname and retrieve only reamining path
                link_url_suffix = badge["link_url"].split("/", 3)[3]
                image_url_suffix = badge["image_url"].split("/", 3)[3]
                data = {
                    "link_url": "{0}/{1}/{2}".format(self.config.destination_host, parent_group_path, link_url_suffix),
                    "image_url": "{0}/{1}/{2}".format(self.config.destination_host, parent_group_path, image_url_suffix)
                }
                self.log.info("{0}Migrating group {1} (ID: {2}) badge:\n{3}".format(
                    get_dry_log(dry_run), parent_group_path, old_id, json_pretty(badge)))
                if not dry_run:
                    self.add_group_badge(
                        self.config.destination_host,
                        self.config.destination_token,
                        new_id,
                        data=data)
        except TypeError as te:
            self.log.error("Group badges {0} {1}".format(response, te))
        except RequestException as re:
            self.log.error("Failed to migrate group {0} (ID: {1}) badges, with error:\n{2}".format(
                parent_group_path, old_id, re))

    def update_project_badges(self, new_id, name, full_parent_namespace):
        try:
            response = self.get_all_project_badges(
                self.config.destination_host,
                self.config.destination_token,
                new_id)
            badges = iter(response)
            for badge in badges:
                # split after hostname and retrieve only remaining path
                link_url_suffix = badge["link_url"].split("/", 3)[3]
                image_url_suffix = badge["image_url"].split("/", 3)[3]
                data = {
                    "link_url": "{0}/{1}/{2}".format(self.config.destination_host, full_parent_namespace, link_url_suffix),
                    "image_url": "{0}/{1}/{2}".format(self.config.destination_host, full_parent_namespace, image_url_suffix)
                }
                self.edit_project_badge(self.config.destination_host,
                                        self.config.destination_token,
                                        new_id,
                                        badge["id"],
                                        data=data)
                self.log.info("Updated project {0} (ID: {1}) badge with data:\n{2}".format(
                    name, new_id, json_pretty(data)))
        except TypeError as te:
            self.log.error(
                "Project {0} badges {1} {2}".format(name, response, te))
            return False
        except RequestException as re:
            self.log.error("Failed to update project {0} (ID: {1}) badges, with error:\n{3}".format(
                name, new_id, re))
            return False
        else:
            return True
