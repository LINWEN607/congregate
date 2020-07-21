import json
from urllib2 import HTTPError
from congregate.helpers.base_class import BaseClass
from congregate.helpers import bitbucket_client as bbc
from congregate.migration.mirror import MirrorClient
from congregate.migration.gitlab.repo import gitlab_repo

gl = gitlab_repo()

users_map = {}
groups_map = {}

mirror = MirrorClient()


# {
#     "name": "repo_1",
#     "web_repo_url": "http://gmiller@localhost:7990/scm/tp1/repo_1.git"
# }
# {
#     "source_host": "http://gmiller@localhost:7990"
# }
# http://gmiller@localhost:7990/scm/tp1/repo_1.git


# TODO: decouple this as much as possible
def handle_bitbucket_migration(repo):
    b = BaseClass()
    project_id = None
    group_id = None
    personal_repo = False
    # searching for project
    if len(repo["name"]) > 0:
        b.log.info("Searching for project %s" % repo["name"])
        search_name = repo["web_repo_url"].split(
            "%s/scm/" % b.config.source_host)[1]
        search_name = search_name.split(".git")[0]
        if len(search_name.split("~")) > 1:
            search_name = search_name.split("~")[1]
        print(search_name)
        if len(search_name) > 0:
            try:
                # Search for the project in our target GitLab space
                project_id = gl.search_for_project(
                    repo["name"], repo["group"], search_name)
                if project_id is None:
                    b.log.info(
                        "Couldn't find %s. Creating it now." %
                        search_name)
                # Group or project available to migrate?
                if repo.get("group", None) is not None or repo.get(
                        "project", None) is not None:
                    if repo.get("web_repo_url", None) is None:
                        repo["web_repo_url"] = repo["links"]["clone"][0]["href"]
                    # Check if this is a personal repo
                    if "~" in repo.get("web_repo_url", ""):
                        personal_repo = True
                        b.log.info("Searching for personal project")
                        cat_users = repo["project_users"] + repo["repo_users"]
                        if len(cat_users) > 0:
                            user_id = None
                            for user in cat_users:
                                if len(user["email"]) > 0:
                                    user_search = bbc.user_search_by_email_or_name(
                                        user["email"])

                                    if len(user_search) > 0:
                                        b.log.info(
                                            "Found %s: %s" %
                                            (user_search[0]["id"], user_search[0]["email"]))
                                        user_objects = bbc.get_user_objects_from_user_search_and_user(
                                            user_search,
                                            user,
                                            users_map,  # Go, go Gadget pass by reference
                                            True
                                        )
                                        user_id = user_objects["user_id"]
                                        user_name = user_objects["user_name"]
                                        users_map[user_name] = user_id
                                    else:
                                        if len(user["email"]) > 0:
                                            user_name = user["email"].split("@")[
                                                0]
                                            if users_map.get(
                                                    user_name, None) is None:
                                                new_user_data = bbc.new_user_data_from_user(
                                                    user)
                                                b.log.info(
                                                    "Creating new user %s" %
                                                    user["email"])
                                                created_user = bbc.create_user(
                                                    new_user_data)
                                                user_id = created_user["id"]
                                            else:
                                                # TODO: This else doesn't do
                                                # much
                                                group_id = users_map[user_name]
                                                b.log.info(
                                                    "Adding new email to user %s" % user["email"])
                                    if user["permission"] == "PROJECT_ADMIN":
                                        group_id = user_id
                    else:
                        if repo.get("group", None) is not None:
                            group_name = repo["group"]
                        elif repo.get("project", None) is not None:
                            project = repo["project"]
                            group_name = project.get("key", None)
                        else:
                            # Should never need this, as we know either group or project exists from the outer
                            # if statement. Just keeps the syntax checker happy until we
                            # TODO: can refactor for better group or project
                            # logic
                            group_name = ""
                        group_name = group_name.replace(" ", "_")
                        b.log.info(
                            "Searching for existing group '%s'" %
                            group_name)
                        group_search = bbc.group_search_by_name(group_name)
                        for group in group_search:
                            if group["path"] == group_name:
                                b.log.info("Found %s" % group_name)
                                group_id = group["id"]

                        if group_id is None:
                            group_path = group_name.replace(" ", "_")
                            group_data = {
                                "name": group_name,
                                "path": group_path,
                                "visibility": "private"
                            }
                            b.log.info("Creating new group %s" % group_name)
                            new_group = bbc.create_group_from_group_data(
                                group_data)
                            group_id = new_group["id"]

                        print("group_id", group_id)

                    # Seems that the groups_map.get calls and
                    # members_already_added check are dupes?
                    if len(repo["project_users"]) > 0 and groups_map.get(
                            group_id, None) is None:
                        members_already_added = groups_map.get(group_id, False)
                        if not members_already_added:
                            for user in repo["project_users"]:
                                # First, don't even try unless there is an
                                # email
                                if user.get("email", None) is not None:
                                    user_id = None
                                    search_array = [
                                        user["email"], user["email"].split("@")[0]]
                                    if user.get("name", None) is not None:
                                        search_array.append(user["name"])
                                    if user.get("username", None) is not None:
                                        search_array.append(user["username"])
                                    if user.get("displayName",
                                                None) is not None:
                                        search_array.append("displayName")
                                    user_data = None
                                    user_search = None
                                    # There are multiple ways to find a user in GitLab. Set them all up based
                                    # on the user info from the repo, and try them until one works.
                                    # When a user doesn't exist. Four tries for nothing.
                                    # Maybe when GraphGL is out of alpha, there will be an easier way to
                                    # filter across an entire result set in a
                                    # group

                                    # based on some of the issues we've had with imports, user_ids, and usernames
                                    # with other imports to .COM, should we
                                    # just do email or bust?
                                    for search_term in search_array:
                                        b.log.info(
                                            "Searching for existing user '%s'" % search_term)
                                        if search_term is not None:
                                            user_search = bbc.user_search_by_email_or_name(
                                                search_term)
                                        if user_search is not None and len(
                                                user_search) > 0:
                                            b.log.info("Found %s" %
                                                       user_search[0])
                                            user_objects = bbc.get_user_objects_from_user_search_and_user(user_search,
                                                                                                          user,
                                                                                                          users_map)
                                            user_data = user_objects["user_data"]
                                            user_name = user_objects["user_name"]
                                            users_map[user_name] = user_objects["user_id"]
                                            break
                                    # user_data is set if we find a user, so
                                    # use it as a flag to create
                                    if user_data is None:
                                        if len(user["email"]) > 0:
                                            user_name = user["email"].split("@")[
                                                0]
                                            if users_map.get(
                                                    user_name, None) is None:
                                                new_user_data = bbc.new_user_data_from_user(
                                                    user)
                                                b.log.info(
                                                    "Creating new user %s" %
                                                    user["email"])
                                                if user["name"] == "admin":
                                                    new_user_data["username"] = "bb_root"
                                                try:
                                                    created_user = bbc.create_user(
                                                        new_user_data)
                                                    print(
                                                        "created_user: ", created_user)
                                                    b.log.info(json.dumps(
                                                        created_user, indent=4))
                                                    user_data = {
                                                        "user_id": created_user["id"],
                                                        "access_level": bbc.bitbucket_permission_map[user["permission"]]
                                                    }
                                                except HTTPError as e:
                                                    b.log.error(
                                                        "Failed to create user %s" % user["email"])
                                                    b.log.error(e)
                                                    b.log.error(e.read())
                                            else:
                                                new_user_email_data = {
                                                    "email": user["email"],
                                                    "skip_confirmation": True,
                                                }
                                                b.log.info(
                                                    "Adding new email to user %s" % user["email"])
                                                try:
                                                    created_user = bbc.create_user_by_email_and_user_id(
                                                        new_user_email_data,
                                                        user_id
                                                    )
                                                    b.log.info(json.dumps(
                                                        created_user, indent=4))
                                                    user_data = {
                                                        "user_id": created_user["id"],
                                                        "access_level": bbc.bitbucket_permission_map[user["permission"]]
                                                    }
                                                except HTTPError as e:
                                                    b.log.error(
                                                        "Failed to create %s" %
                                                        user["email"])
                                                    b.log.error(e)
                                                    b.log.error(e.read())

                                    # Add the new or existing user to the
                                    # proper group
                                    b.log.info(
                                        "%d: %s" %
                                        (group_id, groups_map.get(
                                            group_id, None)))
                                    if user_data is not None and personal_repo is False and \
                                            members_already_added is False:
                                        try:
                                            b.log.info(
                                                "Adding %s to group" %
                                                user["email"])
                                            bbc.add_user_to_group(
                                                user_data, group_id)
                                        except HTTPError as e:
                                            b.log.error(
                                                "Failed to add %s to group" % user["email"])
                                            b.log.error(e)
                                            b.log.error(e.read())
                                else:
                                    b.log.info(
                                        "SKIP: User {} with empty email" %
                                        user.get(
                                            "name", None))
                            groups_map[group_id] = True
                        else:
                            b.log.info("Members already exist")

                    # At this point, we've added users (project/group level)
                    b.log.info("Getting to the mirroring")
                    repo["namespace_id"] = group_id

                    # Removing any trace of a tilde in the project name
                    repo["name"] = "".join(repo["name"].split("~"))
                    repo["personal_repo"] = personal_repo
                    b.log.info(repo.get("namespace_id", None))
                    if repo.get("namespace_id", None) is not None:
                        print("namespace_id")
                        b.log.info("Project ID: %s" % project_id)
                        if project_id is None:
                            print("project_id none")
                            project_id = mirror.mirror_generic_repo(repo)
                            b.log.info("Project ID: %s" % project_id)
                        else:
                            print("project id not none")
                            # Remove this line later
                            # mirror.mirror_repo(repo["web_repo_url"], project_id)

                            if len(repo["repo_users"]) > 0:
                                for user in repo["repo_users"]:
                                    if len(user["email"]) > 0:
                                        print(
                                            "search by email:", user["email"])
                                        user_data = None
                                        b.log.info(
                                            "Searching for existing user '%s'" % user["email"])
                                        user_search = bbc.user_search_by_email_or_name(
                                            user["email"])
                                        print("user search:", user_search)
                                        if len(user_search) > 0:
                                            user_objects = bbc.get_user_objects_from_user_search_and_user(
                                                user_search,
                                                user,
                                                users_map,
                                                True
                                            )
                                            user_data = user_objects["user_data"]
                                            user_name = user_objects["user_name"]
                                            users_map[user_name] = user_objects["user_id"]
                                        else:
                                            if len(user["email"]) > 0:
                                                user_name = user["email"].split("@")[
                                                    0]
                                                if users_map.get(
                                                        user_name, None) is None:
                                                    new_user_data = bbc.new_user_data_from_user(
                                                        user)
                                                    b.log.info(
                                                        "Creating new user %s" %
                                                        user["email"])
                                                    created_user = bbc.create_user(
                                                        new_user_data)
                                                    b.log.info(json.dumps(
                                                        created_user, indent=4))
                                                else:
                                                    new_user_email_data = {
                                                        "email": user["email"],
                                                        "skip_confirmation": True,
                                                    }
                                                    b.log.info(
                                                        "Adding new email to user %s" % user["email"])
                                                    created_user = bbc.create_user_by_group(new_user_email_data,
                                                                                            group_id)
                                                    b.log.info(json.dumps(
                                                        created_user, indent=4))
                                                user_data = {
                                                    "user_id": created_user["id"],
                                                    "access_level": bbc.bitbucket_permission_map[user["permission"]]
                                                }
                                        if user_data is not None:
                                            try:
                                                b.log.info(
                                                    "Adding %s to project" %
                                                    user["email"])
                                                bbc.add_user_to_project(
                                                    user_data, project_id)
                                            except HTTPError as e:
                                                b.log.error(
                                                    "Failed to add %s to project" % user["email"])
                                                b.log.error(e)
                                                b.log.error(e.read())
                                        else:
                                            b.log.info("No user data found")
                    else:
                        b.log.info(
                            "Namespace ID null. Ignoring %s" %
                            repo["name"])
                else:
                    b.log.info("Invalid JSON found. Ignoring object")
            except HTTPError as e:
                b.log.error(e)
                b.log.error(e.read())

# def update_db(db_values):
#     # lock.acquire()
#     conn = psycopg2.connect(
#         host=os.getenv('db_host_name'),
#         dbname=os.getenv('db_name'),
#         user=os.getenv('db_username'),
#         password=os.getenv('db_password'))
#     conn.autocommit = True
#     print("[DEBUG] Inserting into database table")
#     cur = conn.cursor()
#     cur.execute(
#         """INSERT INTO ondemandmigration.gitlab_project(projectid, projectname) VALUES (%s, %s);""",
#         (db_values['projectid'], db_values['projectname']))
#     cur.close()
#     conn.close()
#     # lock.release()
#     return json.dumps(db_values)
