import json
import base64
import re
from bs4 import BeautifulSoup as bs
from httpx import Response
from gitlab_ps_utils.misc_utils import is_error_message_present, pretty_print_key, safe_json_response
from gitlab_ps_utils.dict_utils import rewrite_list_into_dict, is_nested_dict, dig, find as nested_find
from gitlab_ps_utils.jsondiff import Comparator
from gitlab_ps_utils.json_utils import read_json_file_into_object
from congregate.helpers.migrate_utils import get_target_project_path, get_full_path_with_parent_namespace
from congregate.helpers.base_class import BaseClass
from congregate.helpers.congregate_mdbc import CongregateMongoConnector

b = BaseClass()

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
        function toggleBasicStatsMismatch() {
            var rows = document.getElementsByClassName('project-row');
            var button = document.getElementById('filterButton');
            var showMismatch = button.getAttribute('data-showMismatch');
            if (showMismatch === 'false') {
                button.innerHTML = 'Show Failed Projects';
                button.setAttribute('data-showMismatch', 'true');
                for (var i = 0; i < rows.length; i++) {
                    var row = rows[i];
                    if (row.classList.contains('basic-stats-mismatch')) {
                        row.style.display = '';
                    } else {
                        row.style.display = 'none';
                    }
                }
            } else {
                button.innerHTML = 'Show only projects with basic stats mismatches';
                button.setAttribute('data-showMismatch', 'false');
                for (var i = 0; i < rows.length; i++) {
                    var row = rows[i];
                    row.style.display = '';
                }
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

    # Define the problematic fields as a class attribute
    PROBLEMATIC_FIELDS = [
        # "Total Number of Branches",
        "Total Number of Issues",
        "Total Number of Issue Comments",
        "Total Number of Merge Requests",
        "Total Number of Merge Request Comments"
    ]

    def __init__(self):
        super().__init__()
        self.keys_to_ignore = []
        self.results = None
        self.target_parent_paths = set()
        self.staged_data = read_json_file_into_object(f"{b.app_path}/data/staged_projects.json")

    def generate_split_html_report(self):
        """
            Queries MongoDB for all diff_report collections
            and outputs them to the HTML report format
        """
        mongo = CongregateMongoConnector()
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

                        for i in range(len(source_data)):
                            if diff.get(i) is not None and i <= len(source_data) and i <= len(destination_data):
                                try:
                                    accuracy += self.calculate_individual_dict_accuracy(
                                        diff[i], source_data[i], destination_data[i], critical_key, parent_group=parent_group)
                                except Exception as e:
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
            if 0 in [src_lines, dest_lines]:
                original_accuracy = 1.0
            else:
                src_lines += self.total_number_of_differences(diff)
                original_accuracy = dest_lines / (src_lines or 1.0)
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
                accuracy = percentage_sum / total_number_of_keys if total_number_of_keys else 1
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
                accuracy = percentage_sum / total_number_of_keys if total_number_of_keys else 1
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

    def calculate_count_accuracy(self, source_count, destination_count):
        """
        Calculate a relative accuracy percentage between two counts.
        Returns a value between 0.0 and 1.0.
        """
        # Handle edge cases
        if source_count == destination_count:
            return 1.0
        if source_count == 0:
            return 0.0  # Can't have a percentage of zero
        
        # Calculate the percentage difference
        difference = abs(source_count - destination_count)
        percentage_diff = difference / float(source_count)
        
        # Convert to accuracy (1.0 - difference)
        accuracy = 1.0 - percentage_diff
        
        # Cap between 0 and 1
        return max(0.0, min(accuracy, 1.0))

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
            if isinstance(data, Response):
                data = safe_json_response(data)
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

    def is_json_serializable(self, obj):
        try:
            json.dumps(obj)
            return True
        except (TypeError, ValueError):
            return False

    def obfuscate_values(self, obj):
        if isinstance(obj, dict):
            keys_to_obfuscate = [
                "value",
                "key",
                "runners_token"
            ]
            for key in keys_to_obfuscate:
                if key in obj and obj[key]:
                    obj[key] = base64.b64encode(obj[key].encode('utf-8'))
                    if not self.is_json_serializable(obj[key]):
                        obj[key] = str(obj[key])
                elif key in obj and obj[key] == None:
                    del obj[key]

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

    def calculate_problematic_fields_accuracy(self, v):
        for field in self.PROBLEMATIC_FIELDS:
            source_count = dig(v, field, 'source')
            destination_count = dig(v, field, 'destination')
            if source_count is not None and destination_count is not None:
                if source_count == destination_count:
                    accuracy = 1.0
                else:
                    accuracy = 0.0
                if v.get(field):
                    v[field]['accuracy'] = accuracy
                    # Remove any existing 'diff' entry to avoid redundancy
                    if 'diff' in v[field]:
                        del v[field]['diff']
            else:
                # If counts are missing, set accuracy to None or 0 and keep the counts
                accuracy = 0.0
                if v.get(field):
                    v[field]['accuracy'] = accuracy

    def generate_html_report(self, asset, diff, filepath, nested=False):
        filepath = f"{self.app_path}{filepath}"
        self.log.info(f"Writing HTML report to {filepath}")

        soup = bs(
            "<html><body><table class = 'content'></table></body></html>", features="lxml")
        style = soup.new_tag("style")
        style.content = "table tr th td { border: 1px solid #000 }"
        soup.html.append(soup.new_tag("head"))
        soup.html.head.append(style)

        # Separate failed projects from successful ones
        failed_projects = []
        successful_projects = []
        summary_data = None

        # First pass - sort projects into failed and successful
        for d, v in sorted(diff.items()):
            if not isinstance(v, dict):
                p = re.compile('(?<!\\\\)\'')
                v = json.loads(json.dumps(p.sub('\"', v)))
            
            if "migration_results" in d:
                summary_data = (d, v)
            elif (len(v) <= 50000 or nested is True) and len(v) <= 100000:
                # Calculate accuracies for problematic fields
                self.calculate_problematic_fields_accuracy(v)
                
                # Check if this is a failure
                if dig(v, "overall_accuracy", "result") == "failure":
                    failed_projects.append((d, v))
                else:
                    successful_projects.append((d, v))

        # Add summary header and instructions first
        if summary_data:
            d, v = summary_data
            # Create the Summary Header Row
            summary_header_row = soup.new_tag("tr")
            summary_cell_header = soup.new_tag("th")
            summary_cell_header['colspan'] = 3
            summary_cell_header.string = "Instructions"
            summary_header_row.append(summary_cell_header)
            soup.html.body.table.append(summary_header_row)
            
            # Create the Summary Data Row
            summary_data_row = soup.new_tag("tr")
            summary_cell_data = soup.new_tag("td")
            summary_cell_data['colspan'] = 3
            summary_cell_data.string = self.SUMMARY
            summary_data_row.append(summary_cell_data)
            soup.html.body.table.append(summary_data_row)

            # Add the filter button row
            filter_row = soup.new_tag("tr")
            filter_cell = soup.new_tag("td")
            filter_cell['colspan'] = 3
            filter_button = soup.new_tag("button", id="filterButton", onclick="toggleBasicStatsMismatch()", **{'data-showMismatch':'false'})
            filter_button.string = "Show Categories Only"
            filter_cell.append(filter_button)
            filter_row.append(filter_cell)
            soup.html.body.table.append(filter_row)

            # Add overall results header with correct color
            overall_results_header_row = soup.new_tag("tr")
            diff_headers = [pretty_print_key(d), "Overall Accuracy", "Result"]
            for diff_header in diff_headers:
                diff_cell_header = soup.new_tag("th")
                diff_cell_header.string = diff_header
                overall_results_header_row.append(diff_cell_header)
            
            # Set background color based on result
            if v.get("result") == "failure":
                overall_results_header_row['bgcolor'] = self.HEX_FAIL
            else:
                overall_results_header_row['bgcolor'] = self.HEX_SUCCESS
                
            soup.html.body.table.append(overall_results_header_row)
            
            # Add overall results data with correct counts
            overall_results_data_row = soup.new_tag("tr")
            
            # Count only truly successful projects
            successful_count = len([x for x in diff.items() if 
                                isinstance(x[1], dict) and 
                                dig(x[1], "overall_accuracy", "result") == "success" and
                                "error" not in x[1] and
                                "migration_results" not in x[0]])
            total_count = len([x for x in diff.items() if 
                            isinstance(x[1], dict) and 
                            "error" not in x[1] and 
                            "migration_results" not in x[0]])

            data = [
                f"Staged {asset}'s: '{len(self.staged_data)}' Successful {asset}'s: '{successful_count}'",
                str(self.as_percentage(v.get("overall_accuracy", 0))),
                v.get("result", "failure")
            ]
            for da in data:
                cell_data = soup.new_tag("td")
                cell_data.string = da if da else ""
                overall_results_data_row.append(cell_data)
            soup.html.body.table.append(overall_results_data_row)
        
        # Add a header for failed projects section with count
        if failed_projects:
            failed_header_row = soup.new_tag("tr")
            failed_header = soup.new_tag("th")
            failed_header['colspan'] = 3
            failed_header['bgcolor'] = self.HEX_FAIL
            total_projects = len(failed_projects) + len(successful_projects)
            failed_header.string = f"Failed Projects ({len(failed_projects)}/{total_projects})"
            failed_header_row.append(failed_header)
            soup.html.body.table.append(failed_header_row)

        # Add failed projects (with details expanded)
        for d, v in failed_projects:
            self.add_project_to_report(soup, d, v, asset, True)  # True = expand details

        # Add a header for successful projects section with count
        if successful_projects:
            success_header_row = soup.new_tag("tr")
            success_header = soup.new_tag("th")
            success_header['colspan'] = 3
            success_header['bgcolor'] = self.HEX_SUCCESS
            total_projects = len(failed_projects) + len(successful_projects)
            success_header.string = f"Successful Projects ({len(successful_projects)}/{total_projects})"
            success_header_row.append(success_header)
            soup.html.body.table.append(success_header_row)
        
        # Add successful projects (with details collapsed)
        for d, v in successful_projects:
            self.add_project_to_report(soup, d, v, asset, False)  # False = collapse details

        # Add JavaScript for show/hide functionality
        head = soup.new_tag("head")
        script = soup.new_tag("script")
        
        # Extend the existing script with project-specific toggle function
        script_content = self.SCRIPT
        project_toggle_function = """
            function toggleProjectDetails(projectId) {
                var detailsDiv = document.getElementById('details-' + projectId);
                var button = document.getElementById('toggle-' + projectId);
                
                if (detailsDiv.style.display === "none") {
                    detailsDiv.style.display = "block";
                    button.innerHTML = "Hide Details";
                } else {
                    detailsDiv.style.display = "none";
                    button.innerHTML = "Show Details";
                }
            }
        """
        script.string = script_content + project_toggle_function
        
        style = soup.new_tag("style")
        style.string = self.STYLE
        head.append(script)
        head.append(style)
        soup.html.append(head)
        
        with open(filepath, "wb") as f:
            f.write(soup.prettify().encode())

    def add_project_to_report(self, soup, project_name, project_data, asset_type, expand_details=False):
        """
        Add a project to the HTML report with optional details expansion
        
        Args:
            soup: BeautifulSoup object
            project_name: Name of the project
            project_data: Project data dictionary
            asset_type: Type of asset (e.g., "Project")
            expand_details: Whether to expand details by default
        """
        # Check for basic stats mismatches
        basic_stats_mismatch = False
        for field in self.PROBLEMATIC_FIELDS:
            accuracy = dig(project_data, field, 'accuracy')
            if accuracy is not None and accuracy < 1.0:
                basic_stats_mismatch = True
                break

        # Generate a unique ID for this project
        project_id = re.sub(r'[^a-zA-Z0-9]', '-', project_name)
        
        # Creating project row header
        project_row = soup.new_tag("tr")
        if basic_stats_mismatch:
            project_row['class'] = 'project-row basic-stats-mismatch'
        else:
            project_row['class'] = 'project-row'
        
        # Project name cell with show/hide button
        name_cell = soup.new_tag("td")
        name_cell.string = project_name
        
        # Accuracy cell
        accuracy_cell = soup.new_tag("td")
        accuracy_cell.string = str(self.as_percentage(dig(project_data, "overall_accuracy", "accuracy")))
        
        # Result cell with toggle button
        result_cell = soup.new_tag("td")
        overall_accuracy = project_data.get("overall_accuracy")

        # Handle both data structure formats
        if isinstance(overall_accuracy, dict):
            result = overall_accuracy.get("result")
        else:
            # If overall_accuracy is not a dict, look for result at the same level
            result = project_data.get("result")

        result_cell.string = (result or "unknown") + " "

        # Add show/hide button
        toggle_button = soup.new_tag("button")
        toggle_button['id'] = f"toggle-{project_id}"
        toggle_button['onclick'] = f"toggleProjectDetails('{project_id}')"
        toggle_button.string = "Hide Details" if expand_details else "Show Details"
        result_cell.append(toggle_button)
        
        # Set background color based on result
        if result == "failure":
            project_row['bgcolor'] = self.HEX_FAIL
        else:
            project_row['bgcolor'] = self.HEX_SUCCESS
        
        # Add cells to row
        project_row.append(name_cell)
        project_row.append(accuracy_cell)
        project_row.append(result_cell)
        
        # Add row to table
        soup.html.body.table.append(project_row)
        
        # Create details div
        details_row = soup.new_tag("tr")
        if basic_stats_mismatch:
            details_row['class'] = 'project-row basic-stats-mismatch'
        else:
            details_row['class'] = 'project-row'
        
        details_cell = soup.new_tag("td")
        details_cell['colspan'] = 3
        
        details_div = soup.new_tag("div")
        details_div['id'] = f"details-{project_id}"
        if not expand_details:
            details_div['style'] = "display: none;"
        
        # Create details table
        details_table = soup.new_tag("table")
        details_table['width'] = "100%"
        
        # Add table headers
        header_row = soup.new_tag("tr")
        headers = ["Endpoint", "Accuracy", "Diff"]
        
        for header_text in headers:
            header = soup.new_tag("th")
            header.string = header_text
            header_row.append(header)
        
        details_table.append(header_row)
        
        # Add endpoint rows
        for endpoint in project_data:
            if endpoint not in ["overall_accuracy", "error"] and 'total' not in endpoint.lower():
                endpoint_row = soup.new_tag("tr")
                data = [
                    endpoint,
                    str(self.as_percentage(dig(project_data, endpoint, 'accuracy'))),
                    dig(project_data, endpoint, 'diff')
                ]
            elif "overall_accuracy" in endpoint:
                continue  # Skip overall accuracy
            elif "error" in endpoint:
                endpoint_row = soup.new_tag("tr")
                data = [
                    "Error",
                    "N/A",
                    dig(project_data, endpoint, 'error')
                ]
            elif "total" in endpoint.lower():
                endpoint_row = soup.new_tag("tr")
                data = [
                    endpoint,
                    str(self.as_percentage(dig(project_data, endpoint, 'accuracy'))),
                    [f"source: {dig(project_data, endpoint, 'source')}", 
                    f"destination: {dig(project_data, endpoint, 'destination')}"]
                ]
            else:
                continue  # Skip if doesn't match any category
            
            # Add the data to the row
            for item in data:
                cell = soup.new_tag("td")
                if isinstance(item, dict):
                    # Add show/hide button for JSON
                    button = soup.new_tag("button")
                    button['class'] = "accordion"
                    button_id = f"{endpoint}-{project_id}"
                    button['id'] = f"{button_id}-showhide"
                    button.string = "show/hide"
                    cell.append(button)
                    
                    # Add JSON content
                    json_pre = soup.new_tag("pre")
                    json_pre['class'] = "accordion-content"
                    json_pre['id'] = "json"
                    json_pre.string = json.dumps(item, indent=4)
                    cell.append(json_pre)
                elif isinstance(item, list):
                    # Add list items as paragraphs
                    for list_item in item:
                        p = soup.new_tag("p")
                        p.string = list_item
                        cell.append(p)
                else:
                    # Add simple text
                    cell.string = item if item else ""
                
                endpoint_row.append(cell)
            
            details_table.append(endpoint_row)
        
        # Add the table to the div
        details_div.append(details_table)
        
        # Add the div to the cell and the cell to the row
        details_cell.append(details_div)
        details_row.append(details_cell)
        
        # Add the details row to the table
        soup.html.body.table.append(details_row)

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
        mongo = CongregateMongoConnector()
        for diff_col in mongo.wildcard_collection_query("diff_report"):
            mongo.drop_collection(diff_col)
