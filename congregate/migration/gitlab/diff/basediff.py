import json
import base64
from types import GeneratorType
from bs4 import BeautifulSoup as bs
from json2html import json2html
from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import find as nested_find, is_error_message_present
from congregate.helpers.jsondiff import Comparator


class BaseDiffClient(BaseClass):
    SCRIPT = """
        window.onload = function () {
            var acc = document.getElementsByClassName("accordion");
            var accordionContentList = document.getElementsByClassName("accordion-content");
            for (var i = 0; i < acc.length; i++) {
                acc[i].setAttribute("id", i);
                acc[i].addEventListener("click", function() {
                    this.classList.toggle("active");
                    var accordionContent = accordionContentList[this.getAttribute("id")];
                    console.log(accordionContent);
                    if (accordionContent.style.display === "block") {
                    accordionContent.style.display = "none";
                    } else {
                    accordionContent.style.display = "block";
                    }
                });
            }
        }
    """
    STYLE = """
        .accordion {
            background-color: #eee;
            color: #444;
            cursor: pointer;
            padding: 18px;
            width: 100%;
            border: none;
            text-align: left;
            outline: none;
            font-size: 15px;
            transition: 0.4s;
        }
        
        .active, .accordion:hover {
            background-color: #ccc; 
        }
        
        .accordion-content {
            padding: 0 18px;
            display: none;
            background-color: white;
            overflow: hidden;
        }
    """

    def __init__(self):
        super(BaseDiffClient, self).__init__()
        self.keys_to_ignore = []
        self.results = None

    def diff(self, source_data, destination_data, critical_key=None, obfuscate=False, parent_group=None):
        engine = Comparator()
        if isinstance(source_data, list):
            if is_error_message_present(destination_data):
                destination_data = []
            if obfuscate:
                for i, _ in enumerate(source_data):
                    source_data[i] = self.obfuscate_values(source_data[i])
                for i, _ in enumerate(destination_data):
                    destination_data[i] = self.obfuscate_values(
                        destination_data[i])
            diff = engine._compare_arrays(source_data, destination_data)
        else:
            if obfuscate:
                source_data = self.obfuscate_values(source_data)
                destination_data = self.obfuscate_values(destination_data)
            diff = engine.compare_dicts(source_data, destination_data)
        if source_data:
            accuracy = 0
            if isinstance(source_data, list):
                if diff:
                    for i, _ in enumerate(source_data):
                        if diff.get(i):
                            accuracy += self.calculate_individual_accuracy(
                                diff[i], source_data[i], critical_key, parent_group=parent_group)
                    if accuracy != 0:
                        accuracy = float(accuracy) / float(len(source_data))
                else:
                    accuracy = 1.0
            else:
                accuracy = self.calculate_individual_accuracy(
                    diff, source_data, critical_key, parent_group=parent_group)
        else:
            accuracy = 0

        if bool(list(nested_find("error", diff))) or bool(list(nested_find("message", diff))):
            accuracy = 0

        return {
            "diff": diff,
            "accuracy": accuracy
        }

    def generate_diff(self, asset, key, endpoint, critical_key=None, obfuscate=False, **kwargs):
        source_data = self.generate_cleaned_instance_data(
            endpoint(asset["id"], self.config.source_host, self.config.source_token, **kwargs))
        if source_data:
            identifier = asset[key]
            if self.results.get(identifier.lower()) is not None:
                identifier = identifier.lower()
            if self.results.get(identifier) is not None:
                if isinstance(self.results[identifier], dict):
                    destination_id = self.results[identifier]["id"]
                    destination_data = self.generate_cleaned_instance_data(
                        endpoint(destination_id, self.config.destination_host, self.config.destination_token, **kwargs))
                else:
                    destination_data = {
                        "error": "asset missing"
                    }
            else:
                destination_data = self.generate_empty_data(
                    source_data)
            return self.diff(source_data, destination_data, critical_key=critical_key, obfuscate=obfuscate)

        return self.empty_diff()

    def calculate_individual_accuracy(self, diff, source_data, critical_key, parent_group=None):
        original_accuracy = 1 - float(len(diff)) / float(len(source_data))
        return self.critical_key_case_check(diff, critical_key, original_accuracy, parent_group=parent_group)

    def critical_key_case_check(self, diff, critical_key, original_accuracy, parent_group=None):
        if critical_key in diff:
            diff_minus = diff[critical_key]['---']
            diff_plus = diff[critical_key]['+++']
            if parent_group:
                if parent_group not in diff_plus:
                    return 0
            elif diff_minus.lower() != diff_plus.lower():
                return 0
        return original_accuracy

    def load_json_data(self, path):
        with open(path, "r") as f:
            return json.load(f)

    def calculate_overall_accuracy(self, obj):
        accuracy = 0
        percentage_sum = 0
        result = None
        total_number_of_keys = len(obj)
        try:
            if isinstance(obj, dict):
                for o in obj.keys():
                    if (o == "/projects/:id" or o == "/groups/:id") and obj[o]["accuracy"] == 0:
                        result = "failure"
                        percentage_sum = 0
                        break
                    percentage_sum += obj[o]["accuracy"]
                    if obj[o]["accuracy"] == 0:
                        result = "failure"
                accuracy = percentage_sum / total_number_of_keys if total_number_of_keys else 0
                if result is None:
                    result = "success"
        except Exception as e:
            self.log.error(
                "Failed to calculate accuracy for {0}, due to {1}".format(obj, e))
        return {
            "accuracy": accuracy,
            "result": result
        }

    def calculate_overall_stage_accuracy(self, obj):
        accuracy = 0
        percentage_sum = 0
        result = None
        total_number_of_keys = len(obj)
        try:
            if isinstance(obj, dict):
                for o in obj.keys():
                    if (o == "/projects/:id" or o == "/groups/:id") and obj[o]["accuracy"] == 0:
                        result = "failure"
                        percentage_sum = 0
                        break
                    percentage_sum += obj[o]["overall_accuracy"]["accuracy"]
                    if obj[o]["overall_accuracy"]["accuracy"] == 0:
                        result = "failure"
                accuracy = percentage_sum / total_number_of_keys if total_number_of_keys else 0
                if result is None:
                    result = "success"
                return {
                    "overall_accuracy": accuracy,
                    "result": result
                }
        except Exception as e:
            self.log.error(
                "Unable to calculate overall_accuracy for {0}, due to {1}".format(obj, e))
            return {
                "overall_accuracy": 0,
                "results": "failure"
            }

    def ignore_keys(self, data):
        if data is not None:
            if isinstance(data, list):
                for i, _ in enumerate(data):
                    if isinstance(data[i], str) or isinstance(data[i], unicode):
                        return data
                    data[i] = self.ignore_keys(data[i])
            else:
                for key in self.keys_to_ignore:
                    if key in data:
                        data.pop(key)
            return data
        return {}

    def obfuscate_values(self, obj):
        if isinstance(obj, dict):
            keys_to_obfuscate = [
                "value",
                "key",
                "runners_token"
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

    def empty_diff(self):
        return {
            "diff": None,
            "accuracy": 1
        }

    def return_only_accuracies(self, obj):
        accuracies = {}
        for o in obj.keys():
            accuracies[o] = {i: obj[o][i] for i in obj[o] if i != 'diff'}
        return accuracies

    def generate_cleaned_instance_data(self, instance_data):
        if instance_data is not None:
            if isinstance(instance_data, GeneratorType):
                try:
                    instance_data = self.ignore_keys(list(instance_data))
                    instance_data.sort()
                except TypeError:
                    self.log.error(
                        "Unable to generate cleaned instance data. Returning empty list")
                    return []
            elif isinstance(instance_data, list):
                instance_data = sorted(self.ignore_keys(instance_data))
            else:
                instance_data = sorted(self.ignore_keys(instance_data.json()))
        return instance_data

    def generate_empty_data(self, source):
        if isinstance(source, list):
            return [
                {
                    'error': 'asset is missing'
                }
            ]
        return {
            'error': 'asset is missing'
        }

    def generate_html_report(self, diff, filepath):
        filepath = "{0}{1}".format(self.app_path, filepath)
        html_data = json2html.convert(json=diff)
        soup = bs(html_data, features="lxml")
        style = soup.new_tag("style")
        style.content = "table tr th td { border: 1px solid #000 }"
        soup.html.append(soup.new_tag("head"))
        soup.html.head.append(style)
        for tr in soup.html.body.table.find_all('tr', recursive=False):
            if "results" not in tr.th.text:
                tr.th['class'] = "accordion"
                if tr.td:
                    tr.td['class'] = "accordion-content"
            new_tr = soup.new_tag("tr")
            new_tr.append(tr.td)
            tr.insert_after(new_tr)
        head = soup.new_tag("head")
        script = soup.new_tag("script")
        script.string = self.SCRIPT
        style = soup.new_tag("style")
        style.string = self.STYLE
        head.append(script)
        head.append(style)
        soup.html.append(head)
        with open(filepath, "w") as f:
            f.write(soup.prettify(encoding="UTF-8"))
