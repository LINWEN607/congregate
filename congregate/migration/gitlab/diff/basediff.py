import json
import base64
import re
from types import GeneratorType
from bs4 import BeautifulSoup as bs
from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import is_error_message_present, pretty_print_key
from congregate.helpers.dict_utils import rewrite_list_into_dict, is_nested_dict, dig, find as nested_find
from congregate.helpers.jsondiff import Comparator
from congregate.helpers.mdbc import MongoConnector


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
        body {
            width: 100%;
            padding: 1em;
            text-align: center;
            margin: 0 auto;
        }
        td, th {
            border: 1px solid #000;
            text-align: left;
            vertical-align: top;
        }
        pre {
            display: none;
        }
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
        table.content {
            width: 60%;
            text-align: center;
            margin: 0 auto;
        }
    """

    def __init__(self):
        super().__init__()
        self.keys_to_ignore = []
        self.results = None

    def connect_to_mongo(self):
        return MongoConnector()

    def generate_split_html_report(self):
        """
            Queries MongoDB for all diff_report collections 
            and outputs them to the HTML report format
        """
        mongo = self.connect_to_mongo()
        for diff_col in mongo.wildcard_collection_query("diff_report"):
            diff = {}
            for d, _ in mongo.stream_collection(diff_col):
                # if isinstance(d, str):
                #     diff.update(json.loads(d))
                # else:
                diff.update(d)
            self.generate_html_report(
                "Project", diff, f"/data/results/{diff_col}.html")
        mongo.close_connection()

    def diff(self, source_data, destination_data, critical_key=None, obfuscate=False, parent_group=None):
        engine = Comparator()
        diff = None
        accuracy = 1
        if destination_data:
            if isinstance(source_data, list):
                if obfuscate:
                    for i, _ in enumerate(source_data):
                        source_data[i] = self.obfuscate_values(
                            source_data[i])
                    for i, _ in enumerate(destination_data):
                        destination_data[i] = self.obfuscate_values(
                            destination_data[i])
                diff = engine._compare_arrays(
                    source_data, destination_data)
            else:
                if obfuscate:
                    source_data = self.obfuscate_values(source_data)
                    destination_data = self.obfuscate_values(
                        destination_data)
                diff = engine.compare_dicts(source_data, destination_data)
            if source_data:
                if isinstance(source_data, list):
                    if diff:
                        accuracy = 0
                        for i, _ in enumerate(source_data):
                            if diff.get(i):
                                try:
                                    accuracy += self.calculate_individual_dict_accuracy(
                                        diff[i], source_data[i], destination_data[i], critical_key, parent_group=parent_group)
                                except IndexError as e:
                                    self.log.warning(e)
                        if accuracy != 0:
                            accuracy = float(accuracy) / \
                                float(len(source_data))
                    else:
                        accuracy = 1.0
                else:
                    accuracy = self.calculate_individual_dict_accuracy(
                        diff, source_data, destination_data, critical_key, parent_group=parent_group)
            if bool(list(nested_find("error", diff))):
                accuracy = 0
        return {
            "diff": diff,
            "accuracy": accuracy
        }

    def generate_diff(self, asset, key, endpoint, critical_key=None, obfuscate=False, parent_group=None, **kwargs):
        valid_source_endpoint, source_data = self.is_endpoint_valid(
            endpoint(asset["id"], self.config.source_host, self.config.source_token, **kwargs))
        if valid_source_endpoint:
            source_data = self.generate_cleaned_instance_data(source_data)
            if source_data:
                identifier = "{0}/{1}".format(parent_group,
                                              asset[key]) if parent_group else asset[key]
                if self.results.get(identifier) is not None:
                    if isinstance(self.results[identifier], dict):
                        destination_id = self.results[identifier]["id"]
                        # response = endpoint(
                        #     destination_id, self.config.destination_host, self.config.destination_token, **kwargs)
                        # if isinstance(response, GeneratorType):
                        #     response = list(response)
                        # valid_destination_endpoint, response = self.is_endpoint_valid(response)
                        valid_destination_endpoint, response = self.is_endpoint_valid(endpoint(
                            destination_id, self.config.destination_host, self.config.destination_token, **kwargs))
                        if valid_destination_endpoint:
                            destination_data = self.generate_cleaned_instance_data(
                                response)
                        else:
                            destination_data = self.generate_empty_data(
                                source_data)
                    else:
                        destination_data = {
                            "error": "asset missing"
                        }
                else:
                    destination_data = self.generate_empty_data(
                        source_data)
                return self.diff(source_data, destination_data, critical_key=critical_key, obfuscate=obfuscate, parent_group=parent_group)

        return self.empty_diff()

    def generate_count_diff(self, source_count, destination_count):
        return {
            "source": source_count,
            "destination": destination_count
        }

    def generate_gh_diff(self, asset, key, sort_key, source_data, gl_endpoint, critical_key=None, obfuscate=False, parent_group=None, **kwargs):
        identifier = "{0}/{1}".format(parent_group,
                                      asset[key]) if parent_group else asset[key]
        if self.results.get(identifier) is not None:
            if isinstance(self.results[identifier], dict):
                destination_id = dig(
                    self.results, identifier, 'response', 'id')
                response = gl_endpoint(
                    destination_id, self.config.destination_host, self.config.destination_token, **kwargs)
                destination_data = self.generate_cleaned_instance_data(
                    response)
            else:
                destination_data = {
                    "error": "asset missing"
                }
        else:
            destination_data = self.generate_empty_data(
                source_data)

        if sort_key:
            source_data = rewrite_list_into_dict(source_data, sort_key)
            destination_data = rewrite_list_into_dict(
                destination_data, sort_key)

        return self.diff(source_data, destination_data, critical_key=critical_key, obfuscate=obfuscate, parent_group=parent_group)

    def calculate_individual_dict_accuracy(self, diff, source_data, destination_data, critical_key, parent_group=None):
        if diff is not None:
            dest_lines = self.total_number_of_lines(destination_data)
            src_lines = self.total_number_of_lines(source_data)
            if dest_lines > src_lines:
                discrepency = dest_lines - src_lines
                src_lines += discrepency
                dest_lines -= discrepency
            src_lines += self.total_number_of_differences(diff)
            original_accuracy = dest_lines / src_lines
        else:
            original_accuracy = 1.0

        return self.critical_key_case_check(diff, critical_key, original_accuracy, parent_group=parent_group)

    def total_number_of_lines(self, d, keys_to_exclude=None):
        count = 0
        if is_nested_dict(d):
            for k in d.keys():
                if isinstance(d[k], dict):
                    count += self.total_number_of_lines(
                        d[k], keys_to_exclude=keys_to_exclude)
        else:
            if keys_to_exclude:
                length = len({k for k in d if k not in keys_to_exclude})
                count += 1 if (length ==
                               0 and "+++" in keys_to_exclude) else length
            else:
                count += len(d)
        return count

    def total_number_of_differences(self, d):
        count = 0
        if is_nested_dict(d):
            for k in d.keys():
                if isinstance(d[k], dict):
                    count += self.total_number_of_differences(d[k])
        else:
            for k, v in d.items():
                if k in ["+++", "---"]:
                    if not isinstance(v, dict):
                        count += 1
        return count

    def critical_key_case_check(self, diff, critical_key, original_accuracy, parent_group=None):
        if critical_key in diff:
            diff_minus = diff[critical_key]['---']
            diff_plus = diff[critical_key]['+++']
            if (parent_group and parent_group not in diff_plus) or diff_minus.lower() != diff_plus.lower():
                return 0
        return original_accuracy

    def calculate_overall_accuracy(self, obj):
        accuracy = 0
        percentage_sum = 0
        result = None
        total_number_of_keys = len(obj)
        try:
            if isinstance(obj, dict):
                for o in obj.keys():
                    if "total" not in o.lower():
                        if (o == "/projects/:id" or o == "/groups/:id") and obj[o]["accuracy"] == 0:
                            result = "failure"
                            percentage_sum = 0
                            break
                        percentage_sum += obj[o]["accuracy"]
                        if obj[o]["accuracy"] == 0:
                            result = "failure"
                    else:
                        total_number_of_keys -= 1
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
                    if (o == "/projects/:id" or o == "/groups/:id") and dig(obj, o, 'accuracy') == 0:
                        result = "failure"
                        percentage_sum = 0
                        break
                    percentage_sum += dig(obj, o,
                                          'overall_accuracy', 'accuracy')
                    if dig(obj, o, 'overall_accuracy', 'accuracy') == 0:
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
                    if isinstance(data[i], str):
                        return data
                    data[i] = self.ignore_keys(data[i])
            else:
                for k in list(data.keys()):
                    if isinstance(data.get(k), dict):
                        self.ignore_keys(data[k])
                for key in self.keys_to_ignore:
                    if key in data:
                        data.pop(key)
            # return sorted(data, key=lambda x: str(x))
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
                    try:
                        obj[key] = base64.b64encode(obj[key])
                    except TypeError:
                        obj[key] = str(base64.b64encode(
                            bytes(obj[key], encoding='UTF-8')))

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
        if isinstance(obj, dict):
            for o in obj.keys():
                accuracies[o] = {i: obj[o][i] for i in obj[o] if i != 'diff'}
        return accuracies

    def generate_cleaned_instance_data(self, instance_data):
        try:
            if instance_data:
                instance_data = self.ignore_keys(instance_data)
            return instance_data
        except TypeError as te:
            self.log.error(
                f"Unable to generate cleaned instance data. Returning empty list, with error:\n{te}")
            return []

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

    def generate_html_report(self, asset, diff, filepath, nested=False):
        filepath = "{0}{1}".format(self.app_path, filepath)
        self.log.info(f"Writing HTML report to {filepath}")
        soup = bs(
            "<html><body><table class = 'content'></table></body></html>", features="lxml")
        style = soup.new_tag("style")
        style.content = "table tr th td { border: 1px solid #000 }"
        soup.html.append(soup.new_tag("head"))
        soup.html.head.append(style)

        for d, v in diff.items():
            if not isinstance(v, dict):
                # Make sure the JSON only has double quotes
                p = re.compile('(?<!\\\\)\'')
                v = json.loads(json.dumps(p.sub('\"', v)))
            if (len(v) > 50000 and len(v) < 100000) and nested is False:
                self.log.info("Writing to a separate file")
                subdiff = {d: v}
                subfilepath = (
                    f"{filepath.split('.html')[0]}_{d.split('/')[-1]}.html").replace(self.app_path, "")
                self.generate_html_report(
                    asset, subdiff, subfilepath, nested=True)
            elif len(v) > 100000:
                self.log.warning(f"Skipping {d} due to large size")
            else:
                # if not isinstance(v, dict):
                #     # Make sure the JSON only has double quotes
                #     p = re.compile('(?<!\\\\)\'')
                #     v = json.loads(json.dumps(p.sub('\"', v)))
                if "migration_results" not in d:
                    header_row = soup.new_tag("tr")
                    header_data_row = soup.new_tag("tr")
                    header_data = {
                        asset: d,
                        "Accuracy": str(dig(v, "overall_accuracy", "accuracy")),
                        "Result": dig(v, "overall_accuracy", "result")
                    }
                    for k, kv in header_data.items():
                        cell_header = soup.new_tag("th")
                        cell_data = soup.new_tag("td")
                        cell_header.string = k
                        cell_data.string = str(kv)
                        header_row.append(cell_header)
                        header_data_row.append(cell_data)
                    soup.html.body.table.append(header_row)
                    soup.html.body.table.append(header_data_row)

                    diff_row = soup.new_tag("tr")
                    diff_row_table = soup.new_tag("table")
                    diff_headers = ["endpoint", "accuracy", "diff"]
                    diff_cell_row = soup.new_tag("tr")
                    for diff_header in diff_headers:
                        diff_cell_header = soup.new_tag("th")
                        diff_cell_header.string = diff_header
                        diff_cell_row.append(diff_cell_header)
                    diff_row_table.append(diff_cell_row)
                    for endpoint in v:
                        if endpoint not in ["overall_accuracy", "error"] and 'total' not in endpoint.lower():
                            diff_data_row = soup.new_tag("tr")
                            data = [
                                endpoint,
                                str(dig(v, endpoint, 'accuracy')),
                                dig(v, endpoint, 'diff')
                            ]
                        elif "overall_accuracy" in endpoint:
                            data = []
                        elif "error" in endpoint:
                            diff_data_row = soup.new_tag("tr")
                            data = [
                                "Error",
                                "N/A",
                                dig(v, endpoint, 'error')
                            ]
                        elif "total" in endpoint.lower():
                            diff_data_row = soup.new_tag("tr")
                            data = [
                                endpoint,
                                "N/A",
                                [f"{count_key}: {count_value}" for count_key,
                                    count_value in dig(v, endpoint).items()]
                            ]

                        for da in data:
                            cell_data = soup.new_tag("td")
                            if isinstance(da, dict):
                                showhide = soup.new_tag("button")
                                showhide['id'] = f"{endpoint}-showhide"
                                showhide['class'] = 'accordion'
                                showhide.string = "show/hide"
                                cell_data.append(showhide)
                                json_block = soup.new_tag("pre")
                                json_block['id'] = 'json'
                                json_block['class'] = 'accordion-content'
                                json_block.string = json.dumps(da, indent=4)
                                cell_data.append(json_block)
                            elif isinstance(da, list):
                                for count in da:
                                    count_data = soup.new_tag("p")
                                    count_data.string = count
                                    cell_data.append(count_data)
                            else:
                                cell_data.string = da if da else ""
                            diff_data_row.append(cell_data)
                        diff_row_table.append(diff_data_row)

                    td = soup.new_tag("td")
                    td['colspan'] = 3
                    td.append(diff_row_table)
                    diff_row.append(td)
                    soup.html.body.table.append(diff_row)
                else:
                    overall_results_header_row = soup.new_tag("tr")
                    diff_headers = [pretty_print_key(
                        d), "Overall Accuracy", "Result"]
                    for diff_header in diff_headers:
                        diff_cell_header = soup.new_tag("th")
                        diff_cell_header.string = diff_header
                        overall_results_header_row.append(diff_cell_header)
                    soup.html.body.table.insert(0, overall_results_header_row)
                    overall_results_data_row = soup.new_tag("tr")
                    data = [
                        "",
                        str(v.get("overall_accuracy", 0)),
                        v.get("result", "failure")
                    ]
                    for da in data:
                        cell_data = soup.new_tag("td")
                        cell_data.string = da if da else ""
                        overall_results_data_row.append(cell_data)
                    soup.html.body.table.insert(1, overall_results_data_row)

        head = soup.new_tag("head")
        script = soup.new_tag("script")
        script.string = self.SCRIPT
        style = soup.new_tag("style")
        style.string = self.STYLE
        head.append(script)
        head.append(style)
        soup.html.append(head)
        with open(filepath, "wb") as f:
            f.write(soup.prettify().encode())

    def asset_exists(self, endpoint, identifier):
        if identifier:
            resp = endpoint(identifier, self.config.destination_host,
                            self.config.destination_token)
            error, resp = is_error_message_present(resp)
            if not error:
                return True
        return False

    def is_endpoint_valid(self, request):
        error, request = is_error_message_present(request)
        if error or not request:
            return False, request
        return True, request

    def get_destination_id(self, asset, key, parent_group):
        identifier = "{0}/{1}".format(parent_group,
                                      asset[key]) if parent_group else asset[key]
        if self.results.get(identifier) is not None:
            if isinstance(self.results[identifier], dict):
                if did := dig(self.results, identifier, "id"):
                    return did
                elif did := dig(self.results, identifier, "response", "id"):
                    return did
                else:
                    return None
