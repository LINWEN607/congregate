import json
from csv import reader

from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import strip_numbers


'''

Usage:

1. Add "user_map_csv" to config file containing path to user map in CSV form
2. Open up a python shell with poetry (potery run python)
3. Import this function (from congregate.helpers.misc_utils import map_users)
4. Execute this function (map_users())

'''

bm = BaseClass()

def map_users(dry_run=True):
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
            username = row[1].strip()
            email = row[2].strip()
            if users_dict.get(username, None) is not None:
                if email != users_dict[username]["email"]:
                    bm.log.info("Mapping %s with email [%s] to %s" % (
                        name, users_dict[username]["email"], email))
                    users_dict[username]["email"] = email
                    total_matches += 1
    for _, u in users_dict.items():
        rewritten_users.append(u)
    bm.log.info("{0}Found {1} users to remap:\n{2}".format(
        "DRY-RUN: " if dry_run else "",
        total_matches,
        "\n".join(ru for ru in rewritten_users)))
    if not dry_run:
        with open("%s/data/staged_users.json" % bm.app_path, "w") as f:
            json.dump(rewritten_users, f, indent=4)


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
                print(json.dumps(users_dict[username], indent=4))
                #api.generate_delete_request(config.destination_host, config.destination_token, "users/%d" % users_dict[username]["id"])


def map_and_stage_users_by_email_match(dry_run=True):
    """
        Similar to user map, but assumes you have the standard staged_users.json as one input,
        and a CSV of name,old email,new email as the other (instead of username matching)

        Another core difference is that rather than dumping the entire user_dict to rewritten, it will only
        dump items that are actually rewritten to staged_users.json. This is for stripping staging as well
        as rewritting.

        :param dry_run: (bool) When True, will not commit data to destination system or write the new staged_users.json. Default True.
    """

    total_matches = 0
    users_dict = {}
    user_json = {}
    rewritten_users = []
    in_csv_not_staged = []
    dry = "DRY-RUN: " if dry_run else ""

    with open("%s/data/staged_users.json" % bm.app_path, "r") as f:
        bm.log.info(f"Opening {bm.app_path}")
        user_json = json.load(f)
    for user in user_json:
        users_dict[str(user["email"]).lower()] = user

    with open(bm.config.user_map) as csv_file:
        csv_reader = reader(csv_file, delimiter=',')
        for row in csv_reader:
            name = row[0].strip()
            old_email = row[1].strip().lower()
            new_email = row[2].strip().lower()
            if users_dict.get(old_email, None) is not None:
                if new_email != str(users_dict[old_email]["email"]).lower():
                    bm.log.info(
                        f"Mapping {name} with email [{users_dict[old_email]['email']}] to {new_email}")
                    users_dict[old_email]["email"] = new_email
                    rewritten_users.append(users_dict[old_email])
                    total_matches += 1
            else:
                in_csv_not_staged.append(
                    {"old_email": old_email, "new_email": new_email})

    joined = "\n".join(json.dumps(ru) for ru in rewritten_users)
    bm.log.info(f"{dry}Found {total_matches} users to remap:\n{joined}")

    joined = "\n".join(json.dumps(icns) for icns in in_csv_not_staged)
    bm.log.info(f"{dry}Found {len(in_csv_not_staged)} users in the CSV not in staged_users: \n{joined}")

    bm.log.info(f"{dry}{len(users_dict) - len(rewritten_users)} users will be removed from staging, and only the mapped will be staged")

    if not dry_run:
        with open("%s/data/staged_users.json" % bm.app_path, "w") as f:
            json.dump(rewritten_users, f, indent=4)
        bm.log.info(
            "staged_users rewritten. Check for old emails (by domain, etc) in the file and verify counts.")
