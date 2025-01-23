import os
import glob
import errno
import mimetypes
from re import sub
from shutil import copy
from datetime import datetime
from urllib.parse import urlparse
from gitlab_ps_utils.json_utils import read_json_file_into_object


def get_congregate_path():
    app_path = os.getenv("CONGREGATE_PATH")
    if app_path is None:
        app_path = os.getcwd()
    return app_path


def is_dot_com(host):
    return "gitlab.com" in host if host else None


def is_github_dot_com(host):
    return "api.github.com" in host


def rotate_logs():
    """
        Rotate and empty logs
    """
    log_path = f"{get_congregate_path()}/data/logs"
    if os.path.isdir(log_path):
        log = f"{log_path}/congregate.log"
        audit_log = f"{log_path}/audit.log"
        import_json = f"{log_path}/import_failed_relations.json"
        end_time = str(datetime.now()).replace(" ", "_")
        try:
            for file in [log, audit_log, import_json]:
                if os.path.getsize(file) > 0:
                    print(f"Rotating and emptying '{file}'")
                    index = file.find(".")
                    copy(file, file[:index] + f"_{end_time}" + file[index:])
                    open(file, "w").close()
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise
    else:
        raise NotADirectoryError(
            "Cannot find data directory. CONGREGATE_PATH not set or you are not running this in the Congregate directory.")


def stitch_json_results(result_type="project", steps=0, order="tail"):
    """
    Stitch together multiple JSON results files into a single file.

        :param result_type: (str) The specific result type file you want to stitch. (Default: project)
        :param steps: (int) How many files back you want to go for the stitching. (Default: 0)
        :return: list containing the newly stitched results
    """
    reverse = order.lower() == "tail"
    steps += 1
    files = glob.glob(
        f"{get_congregate_path()}/data/results/{result_type}_migration_results_*")
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

def is_valid_url(url):
    parsed = urlparse(url)
    return all([parsed.scheme, parsed.netloc])

def guess_file_type(filename):
    """
        Guess file type based on file path/url
    """
    guess = mimetypes.guess_type(filename)
    if guess[0] and guess[1]:
        return f"{guess[0].split('/')[0]}/{guess[1]}"
    return guess[0]

# TODO: Move this to gitlab-ps-utils since it's used here and in Evaluate
def to_camel_case(s):
    """
        Shameless copy from https://www.w3resource.com/python-exercises/string/python-data-type-string-exercise-96.php
    """
    s = sub(r"(_|-)+", " ", s).title().replace(" ", "")
    return ''.join([s[0].lower(), s[1:]])