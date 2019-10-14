import json

from congregate.helpers.base_class import BaseClass
from congregate.helpers import api


class PushRulesClient(BaseClass):
    def get_push_rules(self, old_id, host, token):
        return api.generate_get_request(host, token, "projects/{}/push_rule".format(old_id))

    def add_push_rule(self, new_id, host, token, data):
        data.pop("id", None)
        data.pop("project_id", None)
        api.generate_post_request(host, token, "projects/{}/push_rule".format(new_id), json.dumps(data))

    def migrate_push_rules(self, old_id, new_id, name):
        try:
            push_rule = self.get_push_rules(
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
                return True
        except Exception, e:
            self.log.error("Failed to migrate {0} push rules, with error:\n{1}".format(name, e))
            return False