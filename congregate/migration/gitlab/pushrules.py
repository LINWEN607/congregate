from requests.exceptions import RequestException

from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import is_error_message_present
from congregate.migration.gitlab.api.projects import ProjectsApi


class PushRulesClient(BaseClass):
    def __init__(self):
        self.projects_api = ProjectsApi()
        super(PushRulesClient, self).__init__()

    def add_push_rules(self, new_id, host, token, data):
        data.pop("id", None)
        data.pop("project_id", None)
        self.projects_api.create_project_push_rule(new_id, host, token, data)

    def migrate_push_rules(self, old_id, new_id, name):
        try:
            push_rules = self.projects_api.get_all_project_push_rules(
                old_id, self.config.source_host, self.config.source_token).json()
            if is_error_message_present(push_rules):
                self.log.error(
                    "Failed to fetch push rules ({0}) for project {1}".format(push_rules, name))
                return False
            else:
                self.log.info("Migrating project {} push rules".format(name))
                self.add_push_rules(
                    new_id, self.config.destination_host, self.config.destination_token, push_rules)
                return True
        except RequestException as re:
            self.log.error(
                "Failed to migrate {0} push rules, with error:\n{1}".format(name, re))
            return False
