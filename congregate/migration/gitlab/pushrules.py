import json

from requests.exceptions import RequestException

from congregate.helpers.base_class import BaseClass
from congregate.migration.gitlab.api.projects import ProjectsApi


class PushRulesClient(BaseClass):
    def __init__(self):
        self.projects_api = ProjectsApi()
        super(PushRulesClient, self).__init__()

    def add_push_rule(self, new_id, host, token, data):
        data.pop("id", None)
        data.pop("project_id", None)
        self.projects_api.create_project_push_rule(
            new_id, host, token, json.dumps(data))

    def migrate_push_rules(self, old_id, new_id, name):
        try:
            push_rule = self.projects_api.get_all_project_push_rules(
                old_id,
                self.config.source_host,
                self.config.source_token).json()
            if push_rule is not None and push_rule:
                self.log.info("Migrating push rules for {}".format(name))
                self.add_push_rule(
                    new_id,
                    self.config.destination_host,
                    self.config.destination_token,
                    push_rule)
        except RequestException as re:
            self.log.error(
                "Failed to migrate {0} push rules, with error:\n{1}".format(name, re))
            return False
        else:
            return True
