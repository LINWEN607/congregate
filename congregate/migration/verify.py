from congregate.helpers import logger as log, conf
from congregate.migration.gitlab.repo import gitlab_repo
from re import sub
import datetime
import time


class Verification:
    def __init__(self, project):
        self.config = conf.ig()
        self.l = log.myLogger(__name__)
        self.gl = gitlab_repo()
        self.bb = project
        self.errors = []

    def compare_multiple_repositories(self, projects):
        verification_map = {"results": {}}
        # assuming initially generated json
        for project_name, project_data in projects.iteritems():
            self.l.logger.info("Comparing data for %s" % project_name)
            verification_map["results"][project_name] = self.compare_repositories(project_data["metadata"])
        verification_map["errors"] = self.errors
        return verification_map

    def compare_repositories(self, project):
        # Assuming initially generated json
        name = project["name"]
        gitlab_id = self.gl.search_for_project(
            name, project["group"], project["name"])
        if gitlab_id is not None:
            repo = self.bb.projects[project["project_key"]]["repos"][name]
            branches_match = self.compare_repository_branches(
                name, repo, gitlab_id)
            commit_hashes_match = self.compare_commit_hashes(
                name, repo, gitlab_id)
            if branches_match and commit_hashes_match:
                self.l.logger.info("Commit hashes match")
                return True
            else:
                self.l.logger.info("Branches and commit hashes don't match")
                return False
        self.l.logger.info("Branches and/or commit hashes don't match")
        return False

    def compare_commit_hashes(self, name, repo, id):
        verified = False
        self.errors = []
        self.l.logger.info("Comparing commit hashes for %s" % name)
        if len(repo["branches"]) > 0:
            for branch in repo["branches"]:
                sha = branch["latestCommit"]
                time.sleep(0.2)
                gitlab_branch = self.gl.get_single_branch(id, branch["name"])
                if gitlab_branch is not None:
                    latest_gitlab_sha = gitlab_branch["commit"]["id"]
                    matching_bitbucket_sha = self.gl.get_single_commit(id, sha)
                    if matching_bitbucket_sha is not None:
                        if matching_bitbucket_sha["id"] != latest_gitlab_sha:
                            self.l.logger.info(
                                "Latest GitLab sha doesn't match latest BitBucket sha. Comparing timestamps")
                            timestamp = None
                            for commit in repo["commits"]:
                                if commit["id"] == sha:
                                    timestamp = datetime.datetime.fromtimestamp(
                                        commit["authorTimestamp"] / 1000).strftime('%Y-%m-%dT%H:%M:%S.000Z')
                            if timestamp is not None:
                                bb_time = datetime.datetime.strptime(
                                    timestamp, "%Y-%m-%dT%H:%M:%S.000Z")
                                try:
                                    gl_time = datetime.datetime.strptime(
                                        matching_bitbucket_sha["committed_date"], "%Y-%m-%dT%H:%M:%S.000Z")
                                except ValueError, e:
                                    rewritten_timestamp = matching_bitbucket_sha["committed_date"].replace(" ", "T")
                                    rewritten_timestamp = sub(r"-\d{2}:\d{2}", "Z", rewritten_timestamp)
                                    gl_time = datetime.datetime.strptime(
                                        rewritten_timestamp, "%Y-%m-%dT%H:%M:%S.000Z")

                                if gl_time > bb_time:
                                    self.l.logger.info(
                                        "GitLab is ahead of Bitbucket on the %s branch" % branch["name"])
                                    verified = True
                                elif gl_time <= bb_time:
                                    self.errors.append("GitLab is behind Bitbucket on the %s branch" % branch["name"])
                                    self.l.logger.error(
                                        "GitLab is behind Bitbucket on the %s branch" % branch["name"])
                                    verified = False
                                    break
                            else:
                                self.errors.append("Cannot find %s/%s/%s in the GitLab repo. The git history may have diverged. Please sync your git history." % (name, branch['name'], sha))
                                self.l.logger.error(
                                    "Cannot find %s/%s/%s in the GitLab repo. The git history may have diverged. Please sync your git history." % (name, branch['name'], sha))
                                verified = False
                                break
                        else:
                            verified = True

                else:
                    self.errors.append("%s/%s has not yet been migrated" % (name, branch["name"]))
                    self.l.logger.error(
                        "%s/%s has not yet been migrated" % (name, branch["name"]))
                    verified = False
                    break

        else:
            self.l.logger.info("No branches exist in this repo.")
            verified = True
        return verified

    def compare_repository_branches(self, name, repo, id):
        self.l.logger.info("Comparing branches for %s" % name)
        bitbucket_branches = repo["branch_count"]
        gitlab_branches = self.gl.get_branches(
            id, include_count=True)
        if gitlab_branches is not None:
            gitlab_branches = gitlab_branches["total-branches"]
            if int(bitbucket_branches) == int(gitlab_branches):
                self.l.logger.info("%s/%s branches migrated for %s" %
                                   (gitlab_branches, bitbucket_branches, name))
                return True
            else:
                self.l.logger.info("%s/%s branches migrated for %s" %
                                   (gitlab_branches, bitbucket_branches, name))
                return False
        return False
