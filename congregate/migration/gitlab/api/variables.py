import json

from congregate.helpers import api


class VariablesApi():

    def get_variables(self, id, host, token, var_type="projects"):
        if var_type == "group":
            endpoint = "groups/%d/variables" % id
        else:
            endpoint = "projects/%d/variables" % id

        return api.generate_get_request(host, token, endpoint)

    def set_variables(self, id, data, host, token, var_type="projects"):
        if var_type == "group":
            endpoint = "groups/%d/variables" % id
        else:
            endpoint = "projects/%d/variables" % id

        return api.generate_post_request(host, token, endpoint, json.dumps(data))