from requests.exceptions import RequestException

from gitlab_ps_utils.misc_utils import get_dry_log
from gitlab_ps_utils.json_utils import json_pretty

from congregate.helpers.base_class import BaseClass
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.api.projects import ProjectsApi


class BadgesClient(BaseClass):
    def __init__(self):
        self.groups = GroupsApi()
        self.projects = ProjectsApi()
        super().__init__()

    # TO BE REMOVED - introduced as part of streaming approach - https://docs.gitlab.com/ee/user/group/import/#migrated-resources
    def migrate_group_badges(self, old_id, new_id, parent_group_path, dry_run=True):
        try:
            response = self.groups.get_all_group_badges(
                old_id, self.config.source_host, self.config.source_token)
            badges = iter(response)
            host = self.config.destination_host

            for badge in badges:
                # Split after hostname and retrieve only remaining path
                link_url_suffix = badge["link_url"].split("/", 3)[3]
                image_url_suffix = badge["image_url"].split("/", 3)[3]
                data = {
                    "link_url": f"{host}/{parent_group_path}/{link_url_suffix}",
                    "image_url": f"{host}/{parent_group_path}/{image_url_suffix}"
                }
                self.log.info(
                    f"{get_dry_log(dry_run)}Migrating group {parent_group_path} (ID: {old_id}) badge:\n{json_pretty(badge)}")
                if not dry_run:
                    self.groups.add_group_badge(
                        new_id, self.config.destination_host, self.config.destination_token, data=data)
        except TypeError as te:
            self.log.error(f"Group badges {response}:\n{te}")
        except RequestException as re:
            self.log.error(
                f"Failed to migrate group {parent_group_path} (ID: {old_id}) badges, with error:\n{re}")
