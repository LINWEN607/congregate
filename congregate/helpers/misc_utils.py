import os
import base64
import errno
import json
import getpass
import re
import hashlib
import sys

from collections import Counter
from base64 import b64encode, b64decode
from copy import deepcopy
from shutil import copy
from re import sub
from datetime import timedelta, date, datetime
from types import GeneratorType
from xml.parsers.expat import ExpatError
from urllib.parse import urlparse
from xmltodict import parse as xmlparse
from requests import Response


def remove_dupes(my_list):
    """
        Basic deduping function to remove any duplicates from a list
    """
    return list({v["id"]: v for v in my_list}.values())


def remove_dupes_with_keys(my_list, list_of_keys):
    """
        Deduping function to remove any duplicates from a list based on a set of keys
    """
    d = {}
    for v in my_list:
        key = ""
        for k in list_of_keys:
            key += str(v.get(k, ""))
        d[key] = v
    return list(d.values())


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
                c["index"] = already_found[obj_id]["index"]
                new_list[already_found[obj_id]["index"]] = c
                already_found[obj_id] = c
        else:
            already_found[obj_id] = deepcopy(d)
            new_list.append(d)
            already_found[obj_id]["index"] = len(new_list) - 1
    return new_list


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


def rewrite_list_into_dict(l, comparison_key, prefix="", lowercase=False):
    """
    Rewrites list of dictionaries into a dictionary for easier nested dict lookup

        :param: l: (list) list to convert to a dictionary
        :param: comparison_key: (str) key to use for lookup. Needs to be a unique value within the nested dictionaries like an ID
        :param: prefix: (str) optional string to use as a prefix for the key lookup
        :param: lowercase: (bool) will convert all comparison keys to lowercase to avoid any issues with case sensitive key lookups
        :return: (dict) rewritten dictionary
    """
    rewritten_obj = {}
    for i, _ in enumerate(l):
        new_obj = l[i]
        key = l[i][comparison_key]
        if prefix:
            key = prefix + str(key)
        if lowercase:
            rewritten_obj[str(key).lower()] = new_obj
        else:
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


def input_generator(params):
    for param in params:
        yield param


def get_dry_log(dry_run=True):
    return "DRY-RUN: " if dry_run else ""


def get_rollback_log(rollback=False):
    return "Rollback: " if rollback else ""


def xml_to_dict(data):
    return sanitize_booleans_in_dict(safe_xml_parse(data))


def safe_xml_parse(data):
    try:
        return xmlparse(data)
    except ExpatError:
        return {}


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


def obfuscate(prompt):
    return b64encode(getpass.getpass(prompt).encode("ascii")).decode("ascii")


def deobfuscate(secret):
    try:
        return b64decode(secret.encode("ascii")).decode("ascii")
    except Exception as e:
        print(f"Invalid token - {e}")
        sys.exit()


def convert_to_underscores(s):
    return sub(r" |\/|\.|\:", "_", s)


def pretty_print_key(s):
    return " ".join(w.capitalize() for w in s.split("_"))


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


def dig(dictionary, *args, default=None):
    """
        Recursive dictionary key lookup function

        Example:
            dig({"nest": {"hello": {"world": "this is nested"}}}, "nest", "hello")
            >>>> {'world': 'this is nested'}

        :param dictionary: (dict) dictionary to traverse
        :param *args: (tuple) series of keys to dig through
        :return: If the most nested key is found, the value of the key

    """
    if not args:
        return dictionary
    if isinstance(dictionary, dict):
        for i, arg in enumerate(args):
            found = dictionary.get(arg, None)
            if found is not None:
                if isinstance(found, dict):
                    args = args[i + 1:]
                    return dig(found, *args, default=default)
                return found
            return default
    return default


def is_error_message_present(response):
    errors = ["message", "errors", "error"]
    if isinstance(response, Response):
        response = safe_json_response(response)
    if isinstance(response, (GeneratorType, map, filter)):
        response = list(response)
    if isinstance(response, list) and response and response[0] in errors:
        return True
    if isinstance(response, dict) and any(r in response for r in errors):
        return True
    if isinstance(response, str) and response in errors:
        return True
    return False


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


def validate_name(name, log=None):
    """
    Validate group and project names to satisfy the following criteria:
    Name can only contain letters, digits, emojis, '_', '.', dash, space.
    It must start with letter, digit, emoji or '_'.
    """
    valid = " ".join(sub(r"[^a-zA-Z0-9\_\-\. ]", " ",
                         name.lstrip("-").lstrip(".")).split())
    if name != valid:
        output = f"Renaming invalid name {name} -> {valid}"
        log.warning(output) if log else print(output)
    return valid


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


def generate_audit_log_message(req_type, message, url, data=None):
    try:
        return "{0}enerating {1} request to {2}{3}".format(
            "{} by g".format(message) if message else "G",
            req_type,
            url,
            " with data: {}".format(data) if data else "")
    except TypeError as e:
        return "Message formatting ERROR. No specific message generated. Generating {0} request to {1}".format(
            req_type, url)


def safe_json_response(response):
    """
        Helper method to handle getting valid JSON safely. If valid JSON cannot be returned, it returns none.
    """
    if response is not None:
        try:
            if isinstance(response, GeneratorType):
                return list(response)
            return response.json()
        except ValueError:
            return None
    return None


def safe_list_index_lookup(l, v):
    """
        Helper method to safely lookup the index of a list based on a specific value
    """
    return l.index(v) if v in l else None


def get_hash_of_dict(d):
    SHAhash = hashlib.sha1()
    SHAhash.update(bytes(json.dumps(d), encoding="UTF-8"))
    return SHAhash.hexdigest()


def get_duplicate_paths(data, are_projects=True):
    """
        Legacy GL versions had case insensitive paths, which on newer GL versions are seen as duplicates
    """
    paths = [x.get("path_with_namespace", "").lower() if are_projects else x.get(
        "full_path", "").lower() for x in data]
    return [i for i, c in Counter(paths).items() if c > 1]


def are_keys_in_dict(list_of_keys, dictionary):
    keys_in_dict = False
    for k in list_of_keys:
        if k in dictionary.keys():
            keys_in_dict = True
    return keys_in_dict


def is_nested_dict(d):
    if isinstance(d, dict):
        return any(isinstance(i, dict) for i in d.values())
    return False


def strip_protocol(s):
    return urlparse(s).netloc


def pop_multiple_keys(src, keys):
    for k in keys:
        src.pop(k, None)
    return src


def clean_split(s, *args, **kwargs):
    """
        Returns split string without any empty string elements

        :param: s: (str) the string to split
        :param: *args, **kwargs: any arguments you need to pass to the split function

        example usage:

        s = "hello/world"
        clean_split(s, "/")
        ['hello', 'world']
    """
    return list(filter(None, s.split(*args, **kwargs)))


def sort_dict(d):
    """
        Sorts dictionary by key name in descending order
    """
    return {k: d[k] for k in sorted(d.keys())}


def get_decoded_string_from_b64_response_content(response):
    """
        Takes a web response, returns the decoded *string* of the content, not byte object
    """
    if j := safe_json_response(response):
        content = j.get("content", "")
        if content is not None and str("content").strip() != "":
            return base64.b64decode(content).decode()
    return None


def do_yml_sub(yml_file, pattern, replace_with):
    """
        Does a regex subn and returns the entity
    """
    return re.subn(pattern, replace_with, yml_file)
