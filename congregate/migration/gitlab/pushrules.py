from requests.exceptions import RequestException

from congregate.helpers.base_class import BaseClass
from gitlab_ps_utils.misc_utils import is_error_message_present, safe_json_response
from gitlab_ps_utils.dict_utils import pop_multiple_keys
from congregate.migration.gitlab.api.projects import ProjectsApi


class PushRulesClient(BaseClass):
    def __init__(self):
        self.projects_api = ProjectsApi()
        super(PushRulesClient, self).__init__()

    def migrate_push_rules(self, old_id, new_id, name):
        try:
            pr = safe_json_response(self.projects_api.get_all_project_push_rules(
                old_id, self.config.source_host, self.config.source_token))
            error, pr = is_error_message_present(pr)
            if pr is None:
                self.log.info(
                    f"No push rules ({pr}) to migrate for project {name}")
                return None
            elif error:
                self.log.error(
                    f"Failed to fetch push rules ({pr}) for project {name}")
                return False
            self.log.info(f"Migrating project {name} push rules")
            pr = pop_multiple_keys(pr, ["id", "created_at", "project_id"])
            self.projects_api.create_project_push_rule(
                new_id, self.config.destination_host, self.config.destination_token, pr)
            return True
        except RequestException as re:
            self.log.error(
                f"Failed to migrate {name} push rules, with error:\n{re}")
            return False
