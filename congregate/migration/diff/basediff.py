import json
import base64
import re
from bs4 import BeautifulSoup as bs
from gitlab_ps_utils.misc_utils import is_error_message_present, pretty_print_key
from gitlab_ps_utils.dict_utils import rewrite_list_into_dict, is_nested_dict, dig, find as nested_find
from gitlab_ps_utils.jsondiff import Comparator

from congregate.helpers.migrate_utils import get_target_project_path, get_full_path_with_parent_namespace
from congregate.helpers.base_class import BaseClass
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

    # Setting Red/Green colors here in case someone needs to change them later.
    HEX_FAIL = "#ff0000"  # Red
    HEX_SUCCESS = "#00800"  # Green
    HEX_TITLE = "#6699CC"  # Blue Gray

    # Report Description
    SUMMARY = """
        This report is a high level view of the migration with diffs listed
        between source and destination. The report is meant for engineers to
        get details and stats without having to rely on other teams to verify
        all the details about the migration. This report DOES NOT replace User
        Acceptance Testing.

        The report will show a color coded 'Overall Accuracy' along with
        individual endpoint 'Accuracy'.  Anything with an accuracy of 90% or
        above is considered a success, and isn't worth looking at unless
        something comes up in User Acceptance Testing.  Items under 90% accuracy
        should merit further investigation.
    """

    def __init__(self):
        super().__init__()
        self.keys_to_ignore = []
        self.results = None
        self.target_parent_paths = set()

    def generate_split_html_report(self):
        """
            Queries MongoDB for all diff_report collections
            and outputs them to the HTML report format
        """
        mongo = MongoConnector()
        for diff_col in mongo.wildcard_collection_query("diff_report"):
            diff = {}
            for d, _ in mongo.stream_collection(diff_col):
                # if isinstance(d, str):
                #     diff.update(json.loads(d))
                # else:
                diff.update(d)
            diff["project_migration_results"] = self.calculate_overall_stage_accuracy(
                diff)
            self.generate_html_report(
                "Project", diff, f"/data/results/{diff_col}.html")
        mongo.close_connection()

    def diff(self, source_data, destination_data,
             critical_key=None, obfuscate=False, parent_group=None):
        engine = Comparator()
        diff = {}
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

    def generate_diff(self, asset, key, endpoint, critical_key=None,
                      obfuscate=False, parent_group=None, **kwargs):
        valid_source_endpoint, source_data = self.is_endpoint_valid(
            endpoint(asset["id"], self.config.source_host, self.config.source_token, **kwargs))
        if valid_source_endpoint:
            source_data = self.generate_cleaned_instance_data(source_data)
            if source_data:
                identifier = f"{parent_group}/{asset[key]}" if parent_group else asset[key]
                destination_data = self.validate_destination_data(
                    identifier, endpoint, source_data, **kwargs)
                return self.diff(source_data, destination_data, critical_key=critical_key,
                                 obfuscate=obfuscate, parent_group=parent_group)
        return self.empty_diff()

    def generate_count_diff(self, source_count, destination_count):
        return {
            "source": source_count,
            "destination": destination_count
        }

    def generate_external_diff(self, asset, sort_key, source_data, gl_endpoint, critical_key=None, obfuscate=False, parent_group=None, **kwargs):
        if sort_key == "username":
            identifier = get_full_path_with_parent_namespace(
                asset["full_path"])
        else:
            identifier = get_target_project_path(asset)
        destination_data = self.validate_destination_data(
            identifier, gl_endpoint, source_data, external=True, **kwargs)
        if sort_key:
            source_data = rewrite_list_into_dict(source_data, sort_key)
            destination_data = rewrite_list_into_dict(
                destination_data, sort_key)
        return self.diff(source_data, destination_data, critical_key=critical_key,
                         obfuscate=obfuscate, parent_group=parent_group)

    def validate_destination_data(self, identifier, gl_endpoint, source_data, external=False, **kwargs):
        if self.results.get(identifier):
            if isinstance(self.results[identifier], dict):
                destination_id = dig(self.results, identifier, 'response',
                                     'id') if external else self.results[identifier]["id"]
                valid_destination_endpoint, response = self.is_endpoint_valid(gl_endpoint(
                    destination_id, self.config.destination_host, self.config.destination_token, **kwargs))
                if valid_destination_endpoint:
                    destination_data = self.generate_cleaned_instance_data(
                        response, source_data=source_data)
                else:
                    destination_data = self.generate_empty_data(
                        source_data, identifier)
            else:
                destination_data = {
                    # identifier being the specific API endpoint
                    "error": f"asset '{identifier}' is missing"
                }
        else:
            destination_data = self.generate_empty_data(
                source_data, identifier)
        return destination_data

    def calculate_individual_dict_accuracy(
            self, diff, source_data, destination_data, critical_key, parent_group=None):
        if diff is not None:
            dest_lines = self.total_number_of_lines(destination_data)
            src_lines = self.total_number_of_lines(source_data)
            if dest_lines > src_lines:
                discrepancy = dest_lines - src_lines
                src_lines += discrepancy
                dest_lines -= discrepancy
            src_lines += self.total_number_of_differences(diff)
            original_accuracy = dest_lines / src_lines
        else:
            original_accuracy = 1.0

        return self.critical_key_case_check(
            diff, critical_key, original_accuracy, parent_group=parent_group)

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

    def critical_key_case_check(
            self, diff, critical_key, original_accuracy, parent_group=None):
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
                        obj_accuracy = dig(obj, o, 'accuracy', default=0)
                        if (o in ["/projects/:id", "/groups/:id"]) and obj_accuracy == 0:
                            result = "failure"
                            percentage_sum = 0
                            break
                        percentage_sum += obj_accuracy
                        if obj_accuracy == 0:
                            result = "failure"
                    else:
                        total_number_of_keys -= 1
                accuracy = percentage_sum / total_number_of_keys if total_number_of_keys else 0
                if result is None:
                    result = "success"
        except Exception as e:
            self.log.error(
                f"Failed to calculate accuracy for {obj}, due to {e}")
            return {
                "accuracy": 0,
                "result": "failure"
            }
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
                    if (o in ["/projects/:id", "/groups/:id"]) and dig(obj, o, 'accuracy', default=0) == 0:
                        result = "failure"
                        percentage_sum = 0
                        break
                    obj_accuracy = dig(
                        obj, o, 'overall_accuracy', 'accuracy', default=0)
                    percentage_sum += obj_accuracy
                    if obj_accuracy == 0:
                        result = "failure"
                accuracy = percentage_sum / total_number_of_keys if total_number_of_keys else 0
                if result is None:
                    result = "success"
        except Exception as e:
            self.log.error(
                f"Failed to calculate overall_accuracy for {obj}, due to {e}")
            return {
                "overall_accuracy": 0,
                "results": "failure"
            }
        return {
            "overall_accuracy": accuracy,
            "result": result
        }

    def generate_cleaned_instance_data(self, instance_data, source_data=None):
        try:
            if instance_data:
                if self.config.source_type == "gitlab":
                    instance_data = self.ignore_keys(instance_data)
                elif self.config.source_type in ["bitbucket server", "github"]:
                    instance_data = self.add_keys(
                        instance_data, source_data)
            return instance_data
        except TypeError as te:
            self.log.error(
                f"Unable to generate cleaned instance data. Returning empty list, with error:\n{te}")
            return []

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
                        data.pop(key, None)
            # return sorted(data, key=lambda x: str(x))
            return data
        return {}

    def add_keys(self, dst_data, src_data):
        if src_data:
            # Extract and compare ONLY matching keys
            src_entry = src_data[0]
            new_data = []
            for d in dst_data:
                element = {}
                for k, v in src_entry.items():
                    if isinstance(v, dict):
                        element[k] = {}
                        # Compare up to one key sublevel
                        for k1 in v:
                            sub_value = d[k].get(k1)
                            element[k][k1] = sub_value.strip() if isinstance(
                                sub_value, str) else sub_value
                    else:
                        value = d.get(k)
                        element[k] = value.strip() if isinstance(
                            value, str) else value
                new_data.append(element)
            return new_data
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

    def generate_empty_data(self, source, identifier):
        # identifier being the specific API endpoint
        if isinstance(source, list):
            return [
                {
                    "error": f"asset '{identifier}' is missing"
                }
            ]
        return {
            "error": f"asset '{identifier}' is missing"
        }

    def as_percentage(self, num):
        '''
        Change a float to a percentage for display purposes.  This should probably be in ps-utils, but just putting it here to get it done.

        :param num: (float) The accuracy float number.
        :return: % formatted number, 0 in the case of None
        '''
        valid_types = [float, int, bool]

        if not num or type(num) not in valid_types:
            return "0%"
        return f"{num: .2%}"

    def select_bg_color(self, value="Title"):
        '''
        Choose a HEX background color code based on keywords.

        :param value: (str) String to evaluate and return a hex color code
        :return: (str) Hex Color Code to use in HTML
        '''

        if not value:
            value = "Title"
        if str(value).lower() == 'success':
            bgcolor = self.HEX_SUCCESS
        elif str(value.lower() == 'failure'):
            bgcolor = self.HEX_FAIL
        else:
            bgcolor = self.HEX_TITLE
        return bgcolor

    def generate_html_report(self, asset, diff, filepath, nested=False):
        filepath = f"{self.app_path}{filepath}"
        self.log.info(f"Writing HTML report to {filepath}")

        soup = bs(
            "<html><body><table class = 'content'></table></body></html>", features="lxml")
        style = soup.new_tag("style")
        style.content = "table tr th td { border: 1px solid #000 }"
        soup.html.append(soup.new_tag("head"))
        soup.html.head.append(style)

        for d, v in sorted(diff.items()):
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

                # This is the main table body of the report, and contains all the individual projects, groups, or users, etc...
                if "migration_results" not in d:
                    # Creating the normal asset row
                    header_row = soup.new_tag("tr")
                    header_data_row = soup.new_tag("tr")
                    header_data = {
                        "Group" if d in self.target_parent_paths else asset: d,
                        "Accuracy": str(self.as_percentage(dig(v, "overall_accuracy", "accuracy"))),
                        "Result": dig(v, "overall_accuracy", "result")
                    }
                    for k, kv in header_data.items():
                        cell_header = soup.new_tag("th")
                        cell_data = soup.new_tag("td")
                        cell_header.string = k
                        cell_data.string = str(kv)
                        header_data_row['bgcolor'] = self.select_bg_color(kv)
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
                        if endpoint not in [
                                "overall_accuracy", "error"] and 'total' not in endpoint.lower():
                            diff_data_row = soup.new_tag("tr")
                            data = [
                                endpoint,
                                str(self.as_percentage(
                                    dig(v, endpoint, 'accuracy'))),
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

                # This is the Main Header Row for the page
                else:
                    # Create the Summary Header Row
                    summary_header_row = soup.new_tag("tr")
                    summary_cell_header = soup.new_tag("th")
                    summary_cell_header['colspan'] = 3
                    summary_cell_header.string = "Instructions"
                    summary_header_row.append(summary_cell_header)
                    soup.html.body.table.insert(0, summary_header_row)
                    # Create the Summary Data Row
                    summary_data_row = soup.new_tag("tr")
                    summary_cell_data = soup.new_tag("td")
                    summary_cell_data['colspan'] = 3
                    summary_cell_data.string = self.SUMMARY
                    summary_data_row.append(summary_cell_data)
                    soup.html.body.table.insert(1, summary_data_row)

                    overall_results_header_row = soup.new_tag("tr")
                    diff_headers = [pretty_print_key(
                        d), "Overall Accuracy", "Result"]
                    for diff_header in diff_headers:
                        diff_cell_header = soup.new_tag("th")
                        diff_cell_header.string = diff_header
                        overall_results_header_row.append(diff_cell_header)
                    overall_results_header_row['bgcolor'] = self.select_bg_color(
                    )
                    soup.html.body.table.insert(2, overall_results_header_row)
                    overall_results_data_row = soup.new_tag("tr")

                    # When the parent group is included in the repo report
                    parent_count = 2 if self.target_parent_paths else 1
                    dest_length = len(
                        [x for x in diff.items() if 'error' not in x[1]]) - parent_count
                    source_length = len(diff.items()) - parent_count
                    data = [
                        f"Staged {asset}'s: '{source_length}' Successful {asset}'s: '{dest_length}'",
                        str(self.as_percentage(v.get("overall_accuracy", 0))),
                        v.get("result", "failure")
                    ]
                    for da in data:
                        cell_data = soup.new_tag("td")
                        cell_data.string = da if da else ""
                        overall_results_data_row.append(cell_data)
                    soup.html.body.table.insert(3, overall_results_data_row)

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
        error, response = is_error_message_present(request)
        if error:
            return False, response
        return True, response

    def get_destination_id(self, asset):
        identifier = get_target_project_path(asset)
        if self.results.get(identifier):
            if isinstance(self.results[identifier], dict):
                if did := dig(self.results, identifier, "id"):
                    return did
                if did := dig(self.results, identifier, "response", "id"):
                    return did
        return None

    def drop_diff_report_collections(self):
        self.log.info("Dropping all diff_report_* mongo db collections")
        mongo = MongoConnector()
        for diff_col in mongo.wildcard_collection_query("diff_report"):
            mongo.drop_collection(diff_col)
