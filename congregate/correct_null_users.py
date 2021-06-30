import json
import sys
from congregate.helpers.base_class import BaseClass
from congregate.helpers.migrate_utils import find_user_by_email_comparison_without_id

# Usage: poetry run python congregate/correct_null_users.py <file-in-data-directory>
# Use this in the event all users listed the user_migration_results file had no IDs

def correct_null_users(path):
    b = BaseClass()

    with open(f"{b.app_path}/data/results/{path}", "r") as f:
        data = json.load(f)

    count = 0

    for k, v in data.items():
        if user := find_user_by_email_comparison_without_id(v["email"]):
            print(user["id"])
            data[k]["id"] = user["id"]
            count += 1

    print(data)
    print(f"total users created: {count}")
    with open(f"{b.app_path}/data/results/new_user_migration_results.json", "w") as f:
        json.dump(data, f, indent=4)

if __name__ == "__main__":
    if path := sys.argv[1]:
        correct_null_users(path)
    else:
        print("No path provided. Please provide a path to user_migration_results.json")