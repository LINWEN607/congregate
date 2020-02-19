import json
from opslib.icsutils.jsondiff import Comparator
from congregate.helpers.base_class import BaseClass


class BaseDiffClient(BaseClass):
    def diff(self, source_data, destination_data, critical_key=None):
        engine = Comparator()
        diff = engine.compare_dicts(source_data, destination_data)
        percentage_off = float(len(diff)) / float(len(source_data))
        if critical_key in diff or "error" in diff["+++"]:
            percentage_off = 1
                    
        diff["percentage_off"] = percentage_off
        return diff
        
    def load_json_data(self, path):
        with open(path, "r") as f:
            return json.load(f)