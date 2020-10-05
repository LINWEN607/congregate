import json
import sys
from congregate.helpers.base_class import BaseClass
from congregate.migration.gitlab.users import UsersClient

## Usage: poetry run python congregate/correct_null_users.py <file-in-data-directory>

path = sys.argv[1]

b = BaseClass()
u = UsersClient()


with open(f"{b.app_path}/data/{path}", "r") as f:
    data = json.load(f)

count = 0

for k, v in data.items():
    if user := u.find_user_by_email_comparison_without_id(v["email"]):
        print(user["id"])
        data[k]["id"] = user["id"]
        count += 1
    
print(data)
print(f"total users created: {count}")
with open(f"{b.app_path}/data/new_user_migration_results.json", "w") as f:
    json.dump(data, f, indent=4)
