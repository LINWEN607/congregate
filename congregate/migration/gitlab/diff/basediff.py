import json
from jsondiff import diff as d
from congregate.helpers.base_class import BaseClass


class BaseDiffClient(BaseClass):
    def diff(self, source_data, destination_data, title_key):
        return {
            title_key: d(source_data, destination_data)
        }

    def load_json_data(self, path):
        with open(path, "r") as f:
            return json.load(f)