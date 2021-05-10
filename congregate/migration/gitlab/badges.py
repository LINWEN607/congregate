from requests.exceptions import RequestException

from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import get_dry_log
from congregate.helpers.json_utils import json_pretty
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.api.projects import ProjectsApi


class BadgesClient(BaseClass):
    def __init__(self):
        self.groups = GroupsApi()
        self.projects = ProjectsApi()
        super(BadgesClient, self).__init__()

    def migrate_group_badges(self, old_id, new_id,
                             parent_group_path, dry_run=True):
        try:
            response = self.groups.get_all_group_badges(
                old_id, self.config.source_host, self.config.source_token)
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
                    self.groups.add_group_badge(
                        new_id, self.config.destination_host, self.config.destination_token, data=data)
        except TypeError as te:
            self.log.error("Group badges {0} {1}".format(response, te))
        except RequestException as re:
            self.log.error("Failed to migrate group {0} (ID: {1}) badges, with error:\n{2}".format(
                parent_group_path, old_id, re))
