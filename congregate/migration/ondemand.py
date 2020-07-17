from congregate.migration.bitbucket.client import handle_bitbucket_migration
from congregate.migration.migrate import start_multi_process
from congregate.migration.mirror import MirrorClient
from congregate.migration.verify import Verification
from congregate.helpers import logger as log, api, conf
# from congregate.helpers.dbc import gl_connector
# from congregate.helpers.decorators import stable_retry
from congregate.helpers.git_scm_data import SCMVerifier
from congregate.migration.gitlab.repo import gitlab_repo
from congregate.migration.user_authorization.user_authorization_functions import user_is_authorized
import json
import os
import subprocess
from time import sleep
from sys import exit
from shutil import rmtree
import re


class OnDemand:
    def __init__(self):
        self.config = conf.Config()
        self.l = log.myLogger(__name__)
        self.v = None
        self.bb_json = None
        self.project_key = None
        self.working_dir = os.getcwd()

    def migrate_to_gitlab(self, migration_type, clone_url):
        self.l.logger.info("Generating %s json" % migration_type)
        self.generate_data(migration_type, clone_url)
        bb_json = self.bb_json
        self.l.logger.info("Migrating %s to GitLab" % clone_url)
        if len(bb_json.projects[self.project_key]["repos"]) > 2:
            data = []
            for _, repo_data in bb_json.projects[self.project_key]["repos"].items():
                data.append(repo_data["metadata"])
            self.l.logger.debug(data)
            start_multi_process(handle_bitbucket_migration, data)
        else:
            for _, repo_data in bb_json.projects[self.project_key]["repos"].items():
                handle_bitbucket_migration(repo_data["metadata"])
        results = self.verify()

        if results["Status"] == "Failure":
            print(json.dumps(results, indent=4))
            exit(1)

        for _, repo_data in bb_json.projects[self.project_key]["repos"].items():
            self.mark_as_read_only(
                migration_type, repo_data["metadata"]["web_repo_url"], repo_data["metadata"]["name"])

        for err in self.v.errors:
            if "The git history may have diverged. Please sync your git history." in err or "User not authorized to mark" in err:
                results["Status"] = "Success with warnings"

        print(json.dumps(results, indent=4))
        if results["Status"] == "Success":
            exit(0)
        elif results["Status"] == "Success with warnings":
            exit(2)
        else:
            exit(1)

    def verify_migration(self, migration_type, clone_url):
        self.generate_data(migration_type, clone_url)
        results = self.verify()
        print(json.dumps(results, indent=4))
        if results["Status"] == "Success":
            exit(0)
        elif results["Status"] == "Success with warnings":
            exit(2)
        else:
            exit(1)

    def re_enable_mirroring(self, arg):
        m = MirrorClient()
        self.l.logger.info("Enabling mirroring for %s" % str(arg))
        try:
            arg = int(arg)
            m.enable_mirror_by_id(arg)
        except ValueError:
            m.enable_mirror_by_id(arg)

    def generate_data(self, migration_type, clone_url):
        project_key = ""
        if clone_url[-1] == "/":
            clone_url = clone_url[:-1]
        if migration_type == "Project" and ".git" in clone_url:
            migration_type = "Repository"
        if migration_type == "Repository" and "/browse" in clone_url:
            migration_type = "Project"
        if migration_type == "Project":
            project_key = clone_url.split("/")[-1].upper()
            self.bb_json = SCMVerifier(
                project=project_key,
                host=self.config.external_source_url.split("://")[1],
                port='',
                protocol='https'
            )
        elif migration_type == "Repository":
            project_key = clone_url.split("/")[-2].upper()
            repo = clone_url.split("/")[-1].replace(".git", "")
            self.bb_json = SCMVerifier(
                project=project_key,
                host=self.config.external_source_url.split("://")[1],
                port='',
                protocol='https',
                repo=repo
            )
        # TODO: Throw or default for project_key?
        self.l.logger.info(self.bb_json.projects[project_key])
        self.v = Verification(self.bb_json)
        self.project_key = project_key

    def verify(self):
        attempt = 0
        verified = True
        verification_results = {}
        m = MirrorClient()
        gl = gitlab_repo()
        while attempt <= 4:
            re_attempt = False
            verification_results = self.v.compare_multiple_repositories(
                self.bb_json.projects[self.project_key]["repos"])
            print(verification_results)
            for k, v in verification_results["results"].items():
                if v is False:
                    verified = False
                    if attempt == 3:
                        self.l.logger.info("Manually pushing %s to GitLab" % k)
                        self.hard_push(
                            self.bb_json.projects[self.project_key]["repos"][k])
                    re_attempt = True
                else:
                    self.l.logger.info("Removing mirror for %s" % k)
                    gitlab_id = gl.search_for_project(
                        self.bb_json.projects[self.project_key]["repos"][k]["metadata"]["name"],
                        self.bb_json.projects[self.project_key]["repos"][k]["metadata"]["group"],
                        self.bb_json.projects[self.project_key]["repos"][k]["metadata"]["name"])
                    m.remove_mirror(gitlab_id)

            if re_attempt is True:
                self.l.logger.info(
                    "Waiting 5 seconds to re-attempt verification")
                sleep(5)
                attempt += 1
            else:
                verified = True
                break

        if verified is False:
            self.l.logger.error(
                "Migration failed. Verification results are the following:")
            return {
                "Status": "Failure",
                "Results": verification_results
            }

        self.l.logger.info(
            "%s repositories have been migrated successfully" %
            len(verification_results["results"]))

        return {
            "Status": "Success",
            "Results": verification_results
        }

    def mark_as_read_only(self, migration_type, repo_url, repo_name):
        first_name = os.getenv('BUILD_USER_FIRST_NAME')
        last_name = os.getenv('BUILD_USER_LAST_NAME')
        email = os.getenv('BUILD_USER_EMAIL')
        bbStuff = repo_url.replace("%s@" % self.config.external_user_name, "")
        bbStuff = bbStuff.split("%s/scm" % self.config.external_source_url)[1]
        project_key = bbStuff.split("/")[1].upper()
        repoSlug = bbStuff.split("/")[2]
        repo_slug = repoSlug.replace(".git", "")
        build_user_id = os.getenv('BUILD_USER_ID')
        auth = user_is_authorized(migration_type, https_clone_url=repo_url, repo_name=repo_name,
                                  first_name=first_name, last_name=last_name, email=email, build_user_id=build_user_id)
        if auth is True:
            m = MirrorClient()
            self.l.logger.info("Marking %s/%s as read-only" %
                               (project_key, repo_slug))
            m.set_repo_read_only(project_key, repo_slug)
        else:
            self.v.errors.append(
                "User not authorized to mark %s/%s assets as read-only" % (project_key, repo_slug))
            self.l.logger.error(
                "User not authorized to mark %s/%s assets as read-only" % (project_key, repo_slug))

    def hard_push(self, repo):
        gl = gitlab_repo()
        if not os.path.isdir("repos"):
            os.mkdir("repos")
        gitlab_id = gitlab_id = gl.search_for_project(
            repo["metadata"]["name"], repo["metadata"]["group"], repo["metadata"]["name"])
        if gitlab_id is not None:
            clone_url = json.load(api.generate_get_request(self.config.destination_host,
                                                           self.config.destination_token, "projects/%d" % gitlab_id))["http_url_to_repo"]

            protocol = clone_url.split("://")[0]
            url = clone_url.split("://")[1]
            new_clone_url = "%s://%s:%s@%s" % (
                protocol, self.config.external_user_name, self.config.destination_token, url)
            os.chdir("repos")
            subprocess.call(["git", "clone", re.sub('@onestash', ':%s@onestash' %
                                                    self.config.external_user_password, repo["metadata"]["web_repo_url"]), repo["metadata"]["name"]])
            os.chdir(repo["metadata"]["name"])
            # # the following pulls the current branches and makes the local repo aware of all the remotes
            subprocess.call(["git", "pull", "--all"])
            # Had concerns about the string, but this was tested succesfully on Python 2.7.15
            cmd = '''git branch -r | grep -v '\->' | while read remote; do git branch --track "${remote#origin/}" "$remote"; done'''
            # This command will exit with non 0 if there are no remotes to pull, thats why the if statement
            if subprocess.call(cmd, shell=True):
                return False
            # Replacing origin with new origin
            subprocess.call(["git", "remote", "remove", "origin"])
            subprocess.call(["git", "remote", "add", "origin", new_clone_url])
            # not sure why we do a git pull here, is this a last ditch attempt to make sure we aren't overwriting?
            subprocess.call(["git", "pull", "--all"])
            # this pushes all the local repos followed by all their tags
            subprocess.call(["git", "push", "-u", "--all"])
            subprocess.call(["git", "push", "-u", "--tags"])
            os.chdir("..")
            rmtree(repo["metadata"]["name"])
            os.chdir(self.working_dir)
