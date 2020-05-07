import base64
import os
import errno
import json

from glob import glob
from shutil import copy
from time import time
from getpass import getpass
from re import sub, findall
from datetime import timedelta, date, datetime
from requests import get, head, Response


def remove_dupes(my_list):
    """
        Basic deduping function to remove any duplicates from a list
    """
    if len(my_list) > 0:
        new_list = [my_list[0]]
        for e in my_list:
            if e not in new_list:
                new_list.append(e)
        return new_list
    return my_list


def download_file(url, path, filename=None, headers=None):
    # NOTE the stream=True parameter
    if __is_downloadable(url):
        r = get(url, stream=True, headers=headers, allow_redirects=True)
        if filename is None:
            filename = __get_filename_from_cd(
                r.headers.get('content-disposition'))
        file_path = "{0}/downloads/{1}".format(path, filename)
        create_local_project_export_structure(os.path.dirname(file_path))
        with open(file_path, 'wb') as f:
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
    rewritten_groups = {}
    for i in range(len(l)):
        new_obj = l[i]
        key = l[i][comparison_key]
        rewritten_groups[prefix + str(key)] = new_obj

    return rewritten_groups


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
    for i in xrange(len(l)):
        key = l[i].keys()[0]
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


def write_json_to_file(path, data, log=None):
    if log:
        log.info("### Writing output to %s" % path)
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def obfuscate(prompt):
    return base64.b64encode(getpass(prompt))


def deobfuscate(secret):
    return base64.b64decode(secret)


def clean_data(dry_run=True, files=None):
    app_path = get_congregate_path()
    files_to_delete = [
        "stage.json",
        "staged_users.json",
        "staged_groups.json",
        "project_json.json",
        "users.json",
        "groups.json",
        "users_not_found.json",
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
        "new_users.json",
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
                print "{0}Removing {1}".format(get_dry_log(dry_run), path)
                if not dry_run:
                    os.remove(path)
            except OSError as e:
                if e.errno != errno.ENOENT:
                    raise
    else:
        print "Cannot find data directory. CONGREGATE_PATH not set or you are not running this in the Congregate directory."


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
        print "Cannot find data directory. CONGREGATE_PATH not set or you are not running this in the Congregate directory."


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
        for k, v in dictionary.iteritems():
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
        response = response.json()
    if isinstance(response, list) and response and response[0] == "message":
        return True
    elif isinstance(response, dict) and response.get("message", None) is not None:
        return True
    elif isinstance(response, unicode) and response == "message":
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

def stitch_json_results(result_type="project", steps=0, log=None):
    files = glob("%s/data/%s_results_*" % (get_congregate_path(), result_type))
    files.sort(key=lambda f: f.split("results_")[1].replace(".json", ""), reverse=True)
    files = files[:steps]
    results = []
    for result in files:
        with open(result, "r") as f:
            data = json.load(f)
            results.append([r for r in data if r[next(iter(r))] != False])

    file_path = "%s/data/%s_migration_results.json" % (
        get_congregate_path(), result_type)
    write_json_to_file(file_path, results, log=log)
