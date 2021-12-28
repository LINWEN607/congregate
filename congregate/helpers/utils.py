import os
import glob
import errno
from shutil import copy
from datetime import datetime
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
        end_time = str(datetime.now()).replace(" ", "_")
        print("Rotating and emptying:\n{}".format("\n".join([log, audit_log])))
        try:
            copy(log, f"{log_path}/congregate_{end_time}.log")
            open(log, "w").close()
            copy(
                audit_log, f"{log_path}/audit_{end_time}.log")
            open(audit_log, "w").close()
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise
    else:
        print("Cannot find data directory. CONGREGATE_PATH not set or you are not running this in the Congregate directory.")


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