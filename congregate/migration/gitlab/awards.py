from helpers.base_class import BaseClass
from helpers import api
from helpers.misc_utils import strip_numbers, remove_dupes
from migration.gitlab.issues import IssuesClient
from migration.gitlab.merge_requests import MergeRequestsClient
from migration.gitlab.snippets import SnippetsClient
from migration.gitlab.users import UsersClient
from requests.exceptions import RequestException
from os import path
from datetime import timedelta, date
import json


class AwardsClient(BaseClass):
    def __init__(self):
        self.issues = IssuesClient()
        self.merge_requests = MergeRequestsClient()
        self.snippets = SnippetsClient()
        self.users = UsersClient()
        super(AwardsClient, self).__init__()

    def get_issue_emojis(self, host, token, project_id, issue_id):
        return api.list_all(host, token, "projects/%d/issues/%d/award_emoji" % (project_id, issue_id))

    def get_single_issue_emojis(self, host, token, project_id, issue_id, award_id):
        return api.generate_get_request(host, token, "projects/%d/issues/%d/award_emoji/%d" % (project_id, issue_id, award_id))

    def get_merge_request_emojis(self, host, token, project_id, mr_id):
        return api.list_all(host, token, "projects/%d/merge_requests/%d/award_emoji" % (project_id, mr_id))

    def get_single_merge_request_emojis(self, host, token, project_id, mr_id, award_id):
        return api.generate_get_request(host, token, "projects/%d/merge_requests/%d/award_emoji/%d" % (project_id, mr_id, award_id))

    def get_snippet_emojis(self, host, token, project_id, snippet_id):
        return api.list_all(host, token, "projects/%d/snippets/%d/award_emoji" % (project_id, snippet_id))

    def get_single_snippet_emojis(self, host, token, project_id, snippet_id, award_id):
        return api.generate_get_request(host, token, "projects/%d/snippets/%d/award_emoji/%d" % (project_id, snippet_id, award_id))

    def create_issue_emoji(self, host, token, project_id, issue_id, name):
        return api.generate_post_request(host, token, "projects/%d/issues/%d/award_emoji?name=%s" % (project_id, issue_id, name), None)

    def create_merge_request_emoji(self, host, token, project_id, mr_id, name):
        return api.generate_post_request(host, token, "projects/%d/merge_requests/%d/award_emoji?name=%s" % (project_id, mr_id, name), None)

    def create_snippet_emoji(self, host, token, project_id, snippet_id, name):
        return api.generate_post_request(host, token, "projects/%d/snippets/%d/award_emoji?name=%s" % (project_id, snippet_id, name), None)

    def migrate_awards(self, new_id, old_id, users_map):
        self.log.info("Migrating ")
        expiration_date = (date.today() + timedelta(days=2)
                           ).strftime('%Y-%m-%d')
        awardables = ["issues", "merge requests", "snippets"]
        functions = [
            [self.issues.get_all_project_issues,
                self.get_issue_emojis, self.issues.get_single_project_issue, self.create_issue_emoji],
            [self.merge_requests.get_all_project_merge_requests,
                self.get_merge_request_emojis, self.merge_requests.get_single_project_merge_request, self.create_merge_request_emoji],
            [self.snippets.get_all_project_snippets,
                self.get_snippet_emojis, self.snippets.get_single_project_snippet, self.create_snippet_emoji]
        ]
        for x in range(0, len(awardables)):
            awardable_name = awardables[x]
            self.log.info("Migrating %s emojis for %d" %
                          (awardable_name, old_id))
            for awardable in functions[x][0](self.config.child_host, self.config.child_token, old_id):
                if awardable.get("iid", None) is not None:
                    awardable_id = awardable["iid"]
                else:
                    awardable_id = awardable["id"]
                for award in functions[x][1](self.config.child_host, self.config.child_token, old_id, awardable_id):
                    response = functions[x][2](self.config.parent_host, self.config.parent_token, new_id, awardable_id)
                    if response.status_code == 200:
                        new_award_giver = self.users.find_user_by_email_comparison(
                            award["user"]["id"])

                        impersonation_token = self.users.find_or_create_impersonation_token(
                            new_award_giver, users_map, expiration_date)

                        functions[x][3](
                            self.config.parent_host, impersonation_token["token"], new_id, awardable_id, award["name"])
