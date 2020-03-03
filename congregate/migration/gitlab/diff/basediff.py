import json
import base64
from opslib.icsutils.jsondiff import Comparator
from bs4 import BeautifulSoup as bs
from json2html import json2html
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
            original_accuracy = 1 - float(len(diff)) / float(len(source_data))
            accuracy = self.critical_key_case_check(diff, critical_key, original_accuracy)
        else:
            accuracy = 0
        if bool(list(nested_find("error", diff))):
            accuracy = 0
                    
        return {
            "diff": diff,
            "accuracy": accuracy
        }

    def critical_key_case_check(self, diff, critical_key, original_accuracy):
        if critical_key in diff:
            diff_minus = diff[critical_key]['---']
            diff_plus = diff[critical_key]['+++']
            if diff_minus.lower() != diff_plus.lower():
                return 0
            return 1
        return original_accuracy
        
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

    def calculate_overall_stage_accuracy(self, obj):
        accuracy = 0
        percentage_sum = 0
        result = None
        total_number_of_keys = len(obj)
        for o in obj.keys():
            percentage_sum += obj[o]["overall_accuracy"]["accuracy"]
            if obj[o]["overall_accuracy"]["accuracy"] == 0:
                result = "failure"
        accuracy = percentage_sum / total_number_of_keys
        if result is None:
            result = "success"
        return {
            "overall_accuracy": accuracy,
            "result": result
        }

    def ignore_keys(self, data):
        if isinstance(data, list):
            for x in xrange(len(data)):
                data[x] = self.ignore_keys(data[x])
        else:
            for key in self.keys_to_ignore:
                if key in data:
                    data.pop(key)
        return data

    def obfuscate_values(self, obj):
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

    def generate_html_report(self, diff, filepath):
        html_data = json2html.convert(json=diff)
        soup = bs(html_data, features="lxml")
        style = soup.new_tag("style")
        style.content = "table tr th td { border: 1px solid #000 }"
        soup.html.append(soup.new_tag("head"))
        soup.html.head.append(style)
        # header_element = None
        for tr in soup.html.body.table.find_all('tr', recursive=False):
            # if "migration_results" in tr.th.text:
            #     header_index = tr
            if "results" not in tr.th.text:
                tr.th['class'] = "accordion"
                if tr.td:
                    tr.td['class'] = "accordion-content"
            new_tr = soup.new_tag("tr")
            new_tr.append(tr.td)
            tr.insert_after(new_tr)
        # new_order = soup.html.body.table.find_all('tr', recursive=False)
        # soup.html.body.table.insert(0, soup.html.body.table[header_index])
        # new_soup.insert_before
        # print soup.html.body.table.find_all('tr', recursive=False)[0]
        head = soup.new_tag("head")
        script = soup.new_tag("script")
        script.string = """
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
        style = soup.new_tag("style")
        style.string = """
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
        head.append(script)
        head.append(style)
        soup.html.append(head)
        with open(filepath, "w") as f:
            f.write(soup.prettify())