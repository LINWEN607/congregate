import json

def read_json_file(json_file_key):
    with open(json_file_key) as f:
        data = json.load(f)
    return data

def write_to_json_file(data, write_file_key):
    with open(write_file_key, "w") as f:
        json.dump(data, f, indent=4)