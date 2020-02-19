import json
import base64
from opslib.icsutils.jsondiff import Comparator
from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import find as nested_find

class BaseDiffClient(BaseClass):
    def __init__(self):
        super(BaseDiffClient, self).__init__()
        self.keys_to_ignore = []

    def diff(self, source_data, destination_data, critical_key=None, obfuscate=False):
        engine = Comparator()
        if isinstance(source_data, list):
            if obfuscate:
                for i in xrange(len(source_data)):
                    source_data[i] = self.obfuscate_values(source_data[i])
                for i in xrange(len(destination_data)):
                    destination_data[i] = self.obfuscate_values(destination_data[i])
            diff = engine._compare_arrays(source_data, destination_data)
        else:
            if obfuscate:
                source_data = self.obfuscate_values(source_data)
                destination_data = self.obfuscate_values(destination_data)
            diff = engine.compare_dicts(source_data, destination_data)

        if source_data:
            accuracy = 1 - float(len(diff)) / float(len(source_data))
        else:
            accuracy = 0
        if critical_key in diff or bool(list(nested_find("error", diff))):
            accuracy = 0
                    
        return {
            "diff": diff,
            "accuracy": accuracy
        }
        
    def load_json_data(self, path):
        with open(path, "r") as f:
            return json.load(f)

    def calculate_overall_accuracy(self, obj):
        accuracy = 0
        percentage_sum = 0
        result = None
        total_number_of_keys = len(obj)
        for o in obj.keys():
            percentage_sum += obj[o]["accuracy"]
            if obj[o]["accuracy"] == 0:
                result = "failure"
        accuracy = percentage_sum / total_number_of_keys
        if result is None:
            result = "success"
        return {
            "accuracy": accuracy,
            "result": result
        }

    def ignore_keys(self, data):
        for key in self.keys_to_ignore:
            if key in data:
                data.pop(key)
        return data

    def obfuscate_values(self, obj):
        keys_to_obfuscate = [
            "value",
            "key"
        ]
        for key in keys_to_obfuscate:
            if key in obj:
                obj[key] = base64.b64encode(obj[key])

        return obj

    def generate_final_diff_dict(self, diff_report):
        accuracy_results = self.calculate_overall_accuracy(diff_report)
        return {
            "diff": diff_report,
            "results": accuracy_results
        }