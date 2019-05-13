from helpers.base_class import BaseClass
from helpers import api
from requests.exceptions import RequestException
import json

class MirrorClient(BaseClass):

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

        self.l.logger.info("Removing mirror from project %d" % project_id)
        api.generate_put_request(self.config.parent_host, self.config.parent_token, "projects/%d" % project_id, json.dumps(mirror_data))

    def mirror_repo(self, project, import_id):
        """
            Sets up mirrored repo to allow a soft cut-over during the migration process.

            NOTE: Only works on GitLab EE instances
        """
        split_url = project["http_url_to_repo"].split("://")
        protocol = split_url[0]
        repo_url = split_url[1]
        # for member in project["members"]:
        #     if member["access_level"] >= 40:
        #         mirror_user_id = member["id"]
        #         mirror_user_name = member["username"]
        #         break

        mirror_user_name = self.config.mirror_username
        mirror_user_id = self.config.parent_user_id
        self.l.logger.info("Attempting to mirror repo")
        import_url = "%s://%s:%s@%s" % (protocol, mirror_user_name, self.config.child_token, repo_url)
        self.l.logger.debug(import_url)
        mirror_data = {
            "mirror": True,
            "mirror_user_id": mirror_user_id,
            "import_url": import_url
        }

        response = api.generate_put_request(self.config.parent_host, self.config.parent_token, "projects/%d" % import_id, json.dumps(mirror_data))
        self.l.logger.info(response.text)

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
        
        import_url = "%s://%s:%s@%s" % (protocol, user_name, user_password, repo_url)
        self.l.logger.debug(import_url)
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
            if generic_repo.get("personal_repo", None) == True:
                data.pop("namespace_id")
                data.pop("default_branch")
                data["mirror_user_id"] = namespace_id
                self.l.logger.info("Attempting to generate personal shell repo for %s and create mirror" % generic_repo["name"])
                # self.l.logger.info(json.dumps(data, indent=4))
                response = json.load(api.generate_post_request(self.config.parent_host, self.config.parent_token, "projects/user/%d" % namespace_id, json.dumps(data)))
                if response.get("id", None) is not None:
                    self.l.logger.debug("Setting default branch to master")
                    default_branch = {
                        "default_branch": "master"
                    }
                    api.generate_put_request(self.config.parent_host, self.config.parent_token, "projects/%d" % response["id"], json.dumps(default_branch))
            else:
                self.l.logger.info("Attempting to generate shell repo for %s and create mirror" % generic_repo["name"])
                response = json.load(api.generate_post_request(self.config.parent_host, self.config.parent_token, "projects", json.dumps(data)))
            #put_response = api.generate_put_request(self.config.parent_host, self.config.parent_token, "projects/%d" % response["id"], json.dumps(put_data))
            self.l.logger.info("Project %s has been created and mirroring has been enabled" % generic_repo["name"])
            db_data = {
                "projectname": generic_repo["web_repo_url"],
                "projectid": response["id"]
            }
            # lock.acquire()
            # update_db(db_data)
            # lock.release()
            with open("repomap.txt", "ab") as f:
                f.write("%s\t%s\n" % (generic_repo["web_repo_url"], response["id"]))
            # self.l.logger.debug(response)

            return response["id"]
            #self.l.logger.debug(put_response.json())
        except RequestException, e:
            self.l.logger.error(e)
            return None

    def enable_mirroring(self):
        for project in api.list_all(self.config.parent_host, self.config.parent_token, "projects"):
            if isinstance(project, dict):
                encoded_name = project["name"].encode('ascii','replace')
                if project.get("import_status", None) == "failed":
                    print "Enabling mirroring for %s" % encoded_name
                    try:
                        resp = api.generate_post_request(self.config.parent_host, self.config.parent_token, "projects/%d/mirror/pull" % project["id"], None)
                        print "Status: %d" % resp.status_code
                    except Exception, e:
                        print e
                        print "Skipping %s" % encoded_name
                else:
                    if project.get("name", None) is not None:
                        print "Skipping %s" % encoded_name
            else:
                print "Skipping %s" % project