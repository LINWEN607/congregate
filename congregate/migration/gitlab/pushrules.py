from helpers.base_class import BaseClass
from helpers import api

class PushRulesClient(BaseClass):
    def get_push_rules(self, id, host, token):
        return api.generate_get_request(host, token, "projects/%d/push_rule" % id)

    def add_push_rule(self, id, host, token, data):
        try:
            data.pop("id")
            data.pop("project_id")
        except KeyError:
            pass

        return api.generate_post_request(host, token, "projects/%d/push_rule" % id, data)
