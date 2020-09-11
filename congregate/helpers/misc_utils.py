import os
import errno
import json
import getpass
import subprocess
import hashlib

import glob
from xmltodict import parse as xmlparse
from traceback import print_exc
from base64 import b64encode, b64decode
from copy import deepcopy
from shutil import copy
from time import time
from re import sub, findall
from datetime import timedelta, date, datetime
from requests import get, head, Response


def remove_dupes(my_list):
    """
        Basic deduping function to remove any duplicates from a list
    """
    return list({v["id"]: v for v in my_list}.values())

def remove_dupes_but_take_higher_access(my_list):
    """
        Deduping function for keeping members with higher access
    """
    already_found = {}
    new_list = []
    for d in my_list:
        obj_id = d["id"]
        if already_found.get(obj_id):
            if already_found[obj_id]["access_level"] < d["access_level"]:
                c = deepcopy(d)
                new_list[already_found[obj_id]["index"]] = c
                already_found[obj_id] = c
        else:
            already_found[obj_id] = deepcopy(d)
            new_list.append(d)
            already_found[obj_id]["index"] = len(new_list) - 1
    return new_list
    
def download_file(url, path, filename=None, headers=None):
    # NOTE the stream=True parameter
    if __is_downloadable(url):
        r = get(url, stream=True, headers=headers, allow_redirects=True)
        if filename is None:
            filename = __get_filename_from_cd(
                r.headers.get('content-disposition'))
        file_path = "{0}/downloads/{1}".format(path, filename)
        create_local_project_export_structure(os.path.dirname(file_path))
        with open(file_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
    return filename


def create_local_project_export_structure(dir_path):
    if not os.path.exists(dir_path):
        try:
            os.makedirs(dir_path)
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise


def __is_downloadable(url):
    """
        Does the url contain a downloadable resource
    """
    h = head(url, allow_redirects=True)
    header = h.headers
    content_type = header.get('content-type')
    if 'text' in content_type.lower():
        return False
    if 'html' in content_type.lower():
        return False
    return True


def __get_filename_from_cd(cd):
    """
        Get filename from content-disposition
    """
    if not cd:
        return None
    fname = findall('filename=(.+)', cd)
    if len(fname) == 0:
        return None
    return fname[0]


def strip_numbers(s):
    return sub(r"[0-9]+", '', s)


def expiration_date():
    return (date.today() + timedelta(days=2)).strftime('%Y-%m-%d')


def parse_query_params(params):
    query_params_string = ""
    query_params_list = []
    for p in params:
        if params.get(p, None) is not None:
            query_params_list.append("%s=%s" % (p, str(params[p])))

    if len(query_params_list) > 0:
        query_params_string = "?%s" % "&".join(query_params_list)

    return query_params_string


def rewrite_list_into_dict(l, comparison_key, prefix=""):
    rewritten_obj = {}
    for i, _ in enumerate(l):
        new_obj = l[i]
        key = l[i][comparison_key]
        if prefix:
            key = prefix + str(key)
        rewritten_obj[key] = new_obj

    return rewritten_obj


def rewrite_json_list_into_dict(l):
    """
        Converts a JSON list:
        [
            {
                "hello": {
                    "world": "how are you"
                }
            },
            {
                "world": {
                    "how": "are you"
                }
            }
        ]

        to:
        {
            "hello": {
                "world": "how are you"
            },
            "world": {
                "how": "are you"
            }
        }

        Note: The top level keys in the nested objects must be unique or else data will be overwritten
    """
    new_dict = {}
    for i, _ in enumerate(l):
        key = list(l[i].keys())[0]
        new_dict[key] = l[i][key]
    return new_dict


def get_congregate_path():
    app_path = os.getenv("CONGREGATE_PATH")
    if app_path is None:
        app_path = os.getcwd()
    return app_path


def input_generator(params):
    for param in params:
        yield param


def migration_dry_run(data_type, post_data):
    with open("{0}/data/dry_run_{1}_migration.json".format(get_congregate_path(), data_type), "a") as f:
        json.dump(post_data, f, indent=4)


def get_dry_log(dry_run=True):
    return "DRY-RUN: " if dry_run else ""


def get_rollback_log(rollback=False):
    return "Rollback: " if rollback else ""


def json_pretty(data):
    return json.dumps(data, indent=4, sort_keys=True)

def xml_to_dict(data):
    return sanitize_booleans_in_dict(xmlparse(data))

def sanitize_booleans_in_dict(d):
    """
        Helper method to convert string representations of boolean values to boolean type
    """
    for k, v in d.items():
        if isinstance(v, dict):
            sanitize_booleans_in_dict(v)
        if isinstance(v, str):
            if v.lower() == 'false':
                d[k] = False
            elif v.lower() == 'true':
                d[k] = True
    return d

def write_json_to_file(path, data, log=None):
    if log:
        log.info("### Writing output to %s" % path)
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def read_json_file_into_object(path):
    with open(path, "r") as f:
        return json.load(f)


def obfuscate(prompt):
    return b64encode(getpass.getpass(prompt).encode("ascii")).decode("ascii")


def deobfuscate(secret):
    return b64decode(secret.encode("ascii")).decode("ascii")


def convert_to_underscores(s):
    return sub(r" |\/", "_", s)


def clean_data(dry_run=True, files=None):
    app_path = get_congregate_path()
    files_to_delete = [
        "staged_projects.json",
        "staged_users.json",
        "staged_groups.json",
        "project_json.json",
        "users.json",
        "groups.json",
        "user_migration_results.json",
        "user_migration_results.html",
        "user_diff.json",
        "group_migration_results.json",
        "group_migration_results.html",
        "group_diff.json",
        "project_migration_results.json",
        "project_migration_results.html",
        "project_diff.json",
        "migration_rollback_results.html",
        "newer_users.json",
        "unknown_users.json",
        "groups_audit.json",
        "dry_run_user_migration.json",
        "dry_run_group_migration.json",
        "dry_run_project_migration.json"
    ] if not files else files

    if os.path.isdir("{}/data".format(app_path)):
        for f in files_to_delete:
            path = "{0}/data/{1}".format(app_path, f)
            try:
                print("{0}Removing {1}".format(get_dry_log(dry_run), path))
                if not dry_run:
                    os.remove(path)
            except OSError as e:
                if e.errno != errno.ENOENT:
                    raise
    else:
        print("Cannot find data directory. CONGREGATE_PATH not set or you are not running this in the Congregate directory.")


def rotate_logs():
    """
        Rotate and empty logs
    """
    app_path = get_congregate_path()
    if os.path.isdir("{}/data".format(app_path)):
        log = "{}/data/congregate.log".format(app_path)
        audit_log = "{}/data/audit.log".format(app_path)
        end_time = str(datetime.now()).replace(" ", "_")
        print("Rotating and emptying:\n{}".format("\n".join([log, audit_log])))
        try:
            copy(log, "{0}/data/congregate_{1}.log".format(app_path, end_time))
            open(log, "w").close()
            copy(
                audit_log, "{0}/data/audit_{1}.log".format(app_path, end_time))
            open(audit_log, "w").close()
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise
    else:
        print("Cannot find data directory. CONGREGATE_PATH not set or you are not running this in the Congregate directory.")


def is_recent_file(path, age=2592000):
    """
        Check whether a file path exists, is empty and older than 1 month
    """
    return os.path.exists(path) and os.path.getsize(
        path) > 0 and time() - os.path.getmtime(path) < age


def find(key, dictionary):
    """
        Nested dictionary lookup from https://gist.github.com/douglasmiranda/5127251
    """
    if isinstance(dictionary, dict):
        for k, v in dictionary.items():
            if k == key:
                yield v
            elif isinstance(v, dict):
                for result in find(key, v):
                    yield result
            elif isinstance(v, list):
                for d in v:
                    for result in find(key, d):
                        yield result


def is_dot_com(host):
    return True if "gitlab.com" in host else False


def check_is_project_or_group_for_logging(is_project):
    return "Project" if is_project else "Group"


def is_error_message_present(response):
    if isinstance(response, Response):
        safe_json_response(response)
    if isinstance(response, list) and response and response[0] == "message":
        return True
    elif isinstance(response, dict) and response.get("message", None) is not None:
        return True
    elif isinstance(response, str) and response == "message":
        return True
    return False


def add_post_migration_stats(start):
    """
        Print all POST/PUT/DELETE requests and their total number
        Assuming you've started the migration with an empty congregate.log
        Print total migration time
    """
    reqs = ["POST request to", "PUT request to", "DELETE request to"]
    reqs_no = 0
    with open("{}/data/audit.log".format(get_congregate_path()), "r") as f:
        for line in f:
            if any(req in line for req in reqs):
                reqs_no += 1
        print("Total number of POST/PUT/DELETE requests: {}".format(reqs_no))
    print("Total time: {}".format(timedelta(seconds=time() - start)))


def get_timedelta(timestamp):
    """
    Get timedelta between provided timestampe and current time

        :param timestamp: A timestamp string
        :return: timedelta between provided timestamp and datetime.now() in hours
    """
    try:
        created_at = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%SZ')
    except ValueError:
        created_at = datetime.strptime(
            timestamp.split(".")[0], '%Y-%m-%dT%H:%M:%S')
    now = datetime.now()
    return (now - created_at).days * 24


def validate_name(name):
    """
    Validate group and project names to satisfy the following criteria:
    Name can only contain letters, digits, emojis, '_', '.', dash, space.
    It must start with letter, digit, emoji or '_'.
    """
    return " ".join(sub(r"[^a-zA-Z0-9\_ ]", " ", name).split())


def list_to_dict(lst):
    """
    Convert list to dictionary for unique key comparison
    Example input:
        [1, 2, 3, 4, 5]
    Example output:
        {
            1: True,
            2: True,
            3: True,
            4: True,
            5L True
        }

        :param lst: list to convert
        :return: dictionary converted from list
    """
    res_dct = {lst[i]: True for i in range(0, len(lst), 2)}
    return res_dct


def write_results_to_file(import_results, result_type="project", log=None):
    end_time = str(datetime.now()).replace(" ", "_")
    file_path = "%s/data/%s_migration_results_%s.json" % (
        get_congregate_path(), result_type, end_time)
    write_json_to_file(file_path, import_results, log=log)
    copy(file_path, "%s/data/%s_migration_results.json" %
         (get_congregate_path(), result_type))


def stitch_json_results(result_type="project", steps=0, order="tail"):
    """
    Stitch together multiple JSON results files into a single file.

        :param result_type: (str) The specific result type file you want to stitch. (Default: project)
        :param steps: (int) How many files back you want to go for the stitching. (Default: 0)
        :return: list containing the newly stitched results
    """
    reverse = True if order.lower() == "tail" else False
    steps += 1
    files = glob.glob("%s/data/%s_migration_results_*" %
                      (get_congregate_path(), result_type))
    files.sort(key=lambda f: f.split("results_")[
               1].replace(".json", ""), reverse=reverse)
    if steps > len(files):
        steps = len(files)
    files = files[:steps]
    results = []
    for result in files:
        data = read_json_file_into_object(result)
        results += ([r for r in data if r[next(iter(r))]])
    return results


def build_ui(app_path):
    build_command = "npm run build"
    subprocess.call(build_command.split(" "))
    if not os.path.exists(app_path + "/ui_checksum"):
        with open(app_path + "/ui-checksum", "w") as f:
            f.write(get_hash_of_dirs("dist"))


def spin_up_ui(app_path, port):
    if not os.path.exists(app_path + "/node_modules"):
        print("No node_modules found. Running npm install")
        install_deps = "npm install"
        subprocess.call(install_deps.split(" "))
    if not os.path.exists(app_path + "/dist"):
        print("UI not built. Building it before deploying")
        build_ui(app_path)
    if is_ui_out_of_date(app_path):
        print("UI is out of date. Rebuilding UI")
        build_ui(app_path)
    os.chdir(app_path + "/congregate")
    run_ui = "gunicorn -k gevent -w 4 ui:app --bind=0.0.0.0:" + str(port)
    subprocess.call(run_ui.split(" "))


def is_ui_out_of_date(app_path):
    try:
        with open(app_path + "/ui-checksum", "r") as f:
            return get_hash_of_dirs(app_path + "/dist") != f.read()
    except IOError:
        print("UI Checksum not found")
        return True
    return False


def generate_audit_log_message(req_type, message, url, data=None):
    try:
        return "{0}enerating {1} request to {2}{3}".format(
            "{} by g".format(message) if message else "G",
            req_type,
            url,
            " with data: {}".format(data) if data else "")
    except TypeError as e:
        return "Message formatting ERROR. No specific message generated. Generating {0} request to {1}".format(req_type, url)


def write_json_yield_to_file(file_path, generator_function, *args):
    with open(file_path, "w") as f:
        output = []
        for data in generator_function(*args):
            output.append(data)
        f.write(json_pretty(output))


def safe_json_response(response):
    """
        Helper method to handle getting valid JSON safely. If valid JSON cannot be returned, it returns none.
    """
    try:
        return response.json()
    except ValueError:
        return None

# http://akiscode.com/articles/sha-1directoryhash.shtml
# Copyright (c) 2009 Stephen Akiki
# MIT License (Means you can do whatever you want with this)
#  See http://www.opensource.org/licenses/mit-license.php
# Error Codes:
#   -1 -> Directory does not exist
#   -2 -> General error (see stack traceback)


def get_hash_of_dirs(directory, verbose=0):
    SHAhash = hashlib.sha1()
    if not os.path.exists(directory):
        return -1

    try:
        for root, _, files in os.walk(directory):
            for names in files:
                if verbose == 1:
                    print('Hashing', names)
                filepath = os.path.join(root, names)
                f1 = None
                try:
                    f1 = open(filepath, 'rb')
                except:
                    # You can't open the file for some reason
                    f1.close()
                    continue

                while 1:
                    # Read file in as little chunks
                    buf = f1.read(4096)
                    if not buf:
                        break
                    SHAhash.update(hashlib.sha1(buf).hexdigest().encode())
                f1.close()
    except:
        # Print the stack traceback
        print_exc()
        return -2

    return SHAhash.hexdigest()
