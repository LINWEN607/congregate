import os
import subprocess
from gitlab_ps_utils.file_utils import get_hash_of_dirs


def build_ui(app_path):
    os.chdir(f"{app_path}/frontend")
    build_command = "npm run build"
    subprocess.call(build_command.split(" "))
    if not os.path.exists(f"{app_path}/ui_checksum"):
        with open(f"{app_path}/ui-checksum", "w") as f:
            f.write(get_hash_of_dirs(f"{app_path}/dist"))


def spin_up_ui(app_path, port):
    if not os.path.exists(f"{app_path}/frontend/node_modules"):
        print("No node_modules found. Running npm install")
        install_deps = "npm install"
        os.chdir(f"{app_path}/frontend")
        subprocess.call(install_deps.split(" "))
    if not os.path.exists(f"{app_path}/dist"):
        print("UI not built. Building it before deploying")
        build_ui(app_path)
    if is_ui_out_of_date(app_path):
        print("UI is out of date. Rebuilding UI")
        build_ui(app_path)
    os.chdir(f"{app_path}/congregate")
    run_ui = f"gunicorn -k gevent -w 4 --env CONGREGATE_PATH={app_path} --env APP_PATH={app_path} ui:app --bind=0.0.0.0:{str(port)}"
    subprocess.call(run_ui.split(" "))


def is_ui_out_of_date(app_path):
    try:
        with open(f"{app_path}/ui-checksum", "r") as f:
            return get_hash_of_dirs(f"{app_path}/frontend/dist") != f.read()
    except IOError:
        print("UI Checksum not found")
        return True
