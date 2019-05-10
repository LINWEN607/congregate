from helpers.base_class import base_class
from helpers import api

class gl_pushrules_client(base_class):
    def get_push_rules(self, id, host, token):
        yield api.list_all(host, token, "projects/%d/push_rule" % id)

    def add_push_rule(self, id, host, token, data):
        try:
            data.pop("id")
            data.pop("project_id")
        except KeyError:
            pass

        return api.generate_post_request(host, token, "projects/%d/push_rule" % id, data)

    