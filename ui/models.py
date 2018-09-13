import os
import json

app_path = os.getenv("CONGREGATE_PATH")

def get_data(file_name):
    with open("%s/data/%s.json" % (app_path, file_name), "r") as f:
        return json.load(f)