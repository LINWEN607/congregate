import os
import subprocess
from congregate.helpers.misc_utils import get_hash_of_dirs

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