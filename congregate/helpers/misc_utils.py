import base64
import os
import errno
import json

from time import time
from getpass import getpass
from re import sub, findall
from datetime import timedelta, date
from requests import get, head


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
            filename = __get_filename_from_cd(r.headers.get('content-disposition'))
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
        except OSError as exc: # Guard against race condition
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

def json_pretty(data):
    return json.dumps(data, indent=4, sort_keys=True)

def obfuscate(prompt):
    return base64.b64encode(getpass(prompt))

def deobfuscate(secret):
    return base64.b64decode(secret)

def clean_data():
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
        "group_migration_results.json"
    ]
    if os.path.isdir("{0}/data".format(app_path)):
        for f in files_to_delete:
            path = "{0}/data/{1}".format(app_path, f)
            if os.path.exists(path):
                print "Removing {}".format(f)
                os.remove(path)
            else:
                print "Couldn't find {}".format(f)
    else:
        print "Cannot find data directory. CONGREGATE_PATH not set or you are not running this in the Congregate directory."

def is_recent_file(path, age=2592000):
    """
        Check whether a file path exists, is empty and older than 1 month
    """
    return os.path.exists(path) and os.path.getsize(path) > 0 and time() - os.path.getmtime(path) < age

def find(key, dictionary):
    """
        Nested dictionary lookup from https://gist.github.com/douglasmiranda/5127251
    """
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