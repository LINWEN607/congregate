from requests.exceptions import RequestException

from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import is_error_message_present, safe_json_response
from congregate.migration.gitlab.api.projects import ProjectsApi


class PushRulesClient(BaseClass):
    def __init__(self):
        self.projects_api = ProjectsApi()
        super(PushRulesClient, self).__init__()

    def migrate_push_rules(self, old_id, new_id, name):
        try:
            push_rules = safe_json_response(self.projects_api.get_all_project_push_rules(
                old_id, self.config.source_host, self.config.source_token))
            if push_rules is None:
                self.log.info(
                    f"No push rules ({push_rules}) to migrate for project {name}")
                return None
            elif is_error_message_present(push_rules):
                self.log.error(
                    f"Failed to fetch push rules ({push_rules}) for project {name}")
                return False
            self.log.info(f"Migrating project {name} push rules")
            push_rules.pop("id", None)
            push_rules.pop("created_at", None)
            push_rules.pop("project_id", None)
            self.projects_api.create_project_push_rule(
                new_id, self.config.destination_host, self.config.destination_token, push_rules)
            return True
        except RequestException as re:
            self.log.error(
                f"Failed to migrate {name} push rules, with error:\n{e}")
            return False
