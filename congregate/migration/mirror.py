import json
import requests
from requests.exceptions import RequestException
from congregate.helpers import api, logger as log
from congregate.helpers.base_class import BaseClass
from congregate.helpers.decorators import stable_retry


class MirrorClient(BaseClass):

    def __init__(self):
        # self.config = conf.ig()
        super(MirrorClient, self).__init__()
        self.logger = log.myLogger(__name__)
        # self.total_to_remove = 0
        # self.total_to_keep = 0

    @stable_retry
    def remove_mirror(self, project_id):
        """
            Removes repo mirror information after migration process is complete

            NOTE: Only works on GitLab EE instances
        """
        mirror_data = {
            "mirror": False,
            "mirror_user_id": None,
            "import_url": None
        }

        self.log.info("Removing mirror from project %d" % project_id)
        api.generate_put_request(self.config.parent_host, self.config.parent_token,
                                 "projects/%d" % project_id, json.dumps(mirror_data))

    @stable_retry
    def mirror_repo(self, repo, import_id):
        """
            Sets up mirrored repo to allow a soft cut-over during the migration process.

            NOTE: Only works on GitLab EE instances
        """
        # split_url = project["http_url_to_repo"].split("://")
        split_url = repo["web_repo_url"].split("://")

        protocol = split_url[0]
        repo_url = split_url[1]
        # for member in project["members"]:
        #     if member["access_level"] >= 40:
        #         mirror_user_id = member["id"]
        #         mirror_user_name = member["username"]
        #         break

        mirror_user_name = self.config.mirror_username
        mirror_user_id = self.config.parent_user_id
        self.log.info("Attempting to mirror repo")
        import_url = "%s://%s:%s@%s" % (protocol, mirror_user_name,
                                        self.config.child_token, repo_url)
        self.log.debug(import_url)
        mirror_data = {
            "mirror": True,
            "mirror_user_id": mirror_user_id,
            "import_url": import_url
        }

        response = api.generate_put_request(
            self.config.parent_host, self.config.parent_token, "projects/%d" % import_id, json.dumps(mirror_data))
        self.log.info(response.text)

    @stable_retry
    def mirror_generic_repo(self, generic_repo):
        """
            Generates shell repo with mirroring enabled by default

            NOTE: Mirroring through the API only works on GitLab EE instances
        """
        split_url = generic_repo["web_repo_url"].split("://")
        protocol = split_url[0]
        repo_url = split_url[1]
        namespace_id = int(generic_repo["namespace_id"])
        print namespace_id
        mirror_user_id = self.config.parent_user_id
        user_name = self.config.external_user_name
        user_password = self.config.external_user_password

        import_url = "%s://%s:%s@%s" % (protocol,
                                        user_name, user_password, repo_url)
        self.log.debug(import_url)
        data = {
            "name": generic_repo["name"],
            "namespace_id": namespace_id,
            "mirror": True,
            "mirror_user_id": mirror_user_id,
            "import_url": import_url,
            "only_mirror_protected_branches": False,
            "mirror_overwrites_diverged_branches": True,
            "default_branch": "master"
        }

        if generic_repo.get("visibility", None) is not None:
            data["visibility"] = generic_repo["visibility"]

        try:
            if generic_repo.get("personal_repo", None):
                data.pop("namespace_id")
                data.pop("default_branch")
                data["mirror_user_id"] = namespace_id
                self.log.info(
                    "Attempting to generate personal shell repo for %s and create mirror" % generic_repo["name"])
                # self.log.info(json.dumps(data, indent=4))
                response = api.generate_post_request(
                    self.config.parent_host, self.config.parent_token, "projects/user/%d" % namespace_id,
                    json.dumps(data)).json()
                if response.get("id", None) is not None:
                    self.log.debug("Setting default branch to master")
                    default_branch = {
                        "default_branch": "master"
                    }
                    api.generate_put_request(self.config.parent_host, self.config.parent_token,
                                             "projects/%d" % response["id"], json.dumps(default_branch))
            else:
                self.log.info(
                    "Attempting to generate shell repo for %s and create mirror" % generic_repo["name"])
                response = api.generate_post_request(
                    self.config.parent_host,
                    self.config.parent_token,
                    "projects",
                    json.dumps(data)).json()
                print(response)

            # put_response = api.generate_put_request(self.config.parent_host, self.config.parent_token, "projects/%d" % response["id"], json.dumps(put_data))
            self.log.info(
                "Project %s has been created and mirroring has been enabled" % generic_repo["name"])
            db_data = {
                "projectname": generic_repo["web_repo_url"],
                "projectid": response["id"]
            }
            # lock.acquire()
            # update_db(db_data)
            # lock.release()
            with open("repomap.txt", "ab") as f:
                f.write("%s\t%s\n" %
                        (generic_repo["web_repo_url"], response["id"]))
            # self.log.debug(response)

            return response["id"]
            # self.log.debug(put_response.json())
        except RequestException, e:
            self.log.error(e)
            return None

    @stable_retry
    def enable_mirroring(self):
        for project in api.list_all(self.config.parent_host, self.config.parent_token, "projects"):
            if isinstance(project, dict):
                encoded_name = project["name"].encode('ascii', 'replace')
                if project.get("import_status", None) == "failed":
                    print "Enabling mirroring for %s" % encoded_name
                    try:
                        resp = api.generate_post_request(
                            self.config.parent_host, self.config.parent_token,
                            "projects/%d/mirror/pull" % project["id"], None)
                        print "Status: %d" % resp.status_code
                    except Exception, e:
                        print e
                        print "Skipping %s" % encoded_name
                else:
                    if project.get("name", None) is not None:
                        print "Skipping %s" % encoded_name
            else:
                print "Skipping %s" % project

    @stable_retry
    def enable_mirror_by_id(self, id):
        resp = api.generate_post_request(
            self.config.parent_host, self.config.parent_token, "projects/%d/mirror/pull" % id, None)
        print resp.status_code

    # TODO: This was disabled in the source repo
    # @stable_retry
    # def disable_all_mirrors(self):
    #    self.l.logger.info("Removing mirroring system-wide")
    #    try:
    #        cur = self.db_connector.get_cursor()
    #        cur.execute("""
    #            SELECT p.id, p.name, p.import_url FROM public.projects p, public.project_mirror_data m
    #            where p.id = m.project_id
    #            and p.import_url is not null
    #            """)
    #        data = {
    #            "mirror": False,
    #            "mirror_user_id": None,
    #            "import_url": None
    #        }
    #        for row in cur:
    #            self.handle_removing_mirror(row, data)
    #
    #        self.l.logger.info("Total to keep %d" % self.total_to_keep)
    #        self.l.logger.info("Total to remove %d" % self.total_to_remove)
    #
    #    except Exception, e:
    #        self.l.logger.error(e)

    @stable_retry
    def set_repo_read_only(self, project_key, repository_slug):
        PROXY_LIST = {'http': '', 'https': ''}
        username = self.config.external_user_name
        password = self.config.external_user_password
        auth = (username, password)
        headers = {
            "Content-Type": "application/vnd.atl.bitbucket.bulk+json",
            "X-Atlassian-Token": "nocheck"
        }
        # Accessing personal repositories via REST is achieved through the
        # normal project-centric REST URLs using the user's slug prefixed by
        # tilde as the project
        url = self.config.external_source_url
        # Create a restriction for the supplied branch or set of branches to be
        # applied to the given repository.
        api_url = url + "/rest/branch-permissions/2.0/projects/" + \
                  project_key + "/repos/" + repository_slug + "/restrictions/"
        payload = {"type": "read-only", "matcher": {"id": "*",
                                                    "type": {"id": "PATTERN", "name": "Pattern"}}, "users": "",
                   "groups": ""}
        r = requests.session().post(api_url, auth=auth, proxies=PROXY_LIST, json=payload)
        self.logger.info(r.status_code)
