from congregate.helpers import base_module as bm
from congregate.helpers.misc_utils import strip_numbers
from csv import reader
import json
'''

Usage:

1. Add "user_map_csv" to config file containing path to user map in CSV form
2. Open up a python shell with pipenv (pipenv run python)
3. Import this function (from congregate.helpers.misc_utils import map_users)
4. Execute this function (map_users())

'''


def map_users():
    total_matches = 0
    users_dict = {}
    user_json = {}
    rewritten_users = []
    with open("%s/data/staged_users.json" % bm.app_path, "r") as f:
        user_json = json.load(f)
    for user in user_json:
        users_dict[strip_numbers(user["username"])] = user

    with open(bm.config.user_map) as csv_file:
        csv_reader = reader(csv_file, delimiter=',')
        for row in csv_reader:
            name = row[0].strip()
            username = strip_numbers(row[1].strip())
            email = row[2].strip()
            if users_dict.get(username, None) is not None:
                if email != users_dict[username]["email"]:
                    bm.log.info("Mapping %s with email [%s] to %s" % (
                        name, users_dict[username]["email"], email))
                    users_dict[username]["email"] = email
                    total_matches += 1
    for _, u in users_dict.iteritems():
        rewritten_users.append(u)
    with open("%s/data/staged_users.json" % bm.app_path, "w") as f:
        json.dump(rewritten_users, f, indent=4)
    print "Found %d users to remap" % total_matches


def rm_non_ldap_users():
    total_matches = 0
    users_dict = {}
    user_json = {}
    rewritten_users = []
    with open("%s/data/new_users.json" % bm.app_path, "r") as f:
        user_json = json.load(f)
    for user in user_json:
        users_dict[strip_numbers(user["username"])] = user

    with open(bm.config.user_map) as csv_file:
        csv_reader = reader(csv_file, delimiter=',')
        for row in csv_reader:
            name = row[0].strip()
            username = strip_numbers(row[1].strip())
            email = row[2].strip()
            # if users_dict.get(username, None) is not None:
            #     if email != users_dict[username]["email"]:
            #         log.info("Mapping %s with email [%s] to %s" % (name, users_dict[username]["email"], email))
            #         users_dict[username]["email"] = email
            #         total_matches += 1
            if users_dict.get(username, None) is None:
                print json.dumps(users_dict[username], indent=4)
                #api.generate_delete_request(config.parent_host, config.parent_token, "users/%d" % users_dict[username]["id"])
