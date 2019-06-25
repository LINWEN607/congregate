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

    def create_issue_emojis(self, host, token, project_id, issue_id, name):
        return api.generate_post_request(host, token, "projects/%d/issues/%d/award_emoji?name=%s" % (project_id, issue_id, name), None)

    def create_merge_request_emojis(self, host, token, project_id, mr_id, name):
        return api.generate_post_request(host, token, "projects/%d/merge_requests/%d/award_emoji?name=%s" % (project_id, mr_id, name), None)

    def create_snippet_emojis(self, host, token, project_id, snippet_id, name):
        return api.generate_post_request(host, token, "projects/%d/snippets/%d/award_emoji?name=%s" % (project_id, snippet_id, name), None)

    def migrate_awards(self, old_id, new_id, users_map):
        expiration_date = (date.today() + timedelta(days=2)).strftime('%Y-%m-%d')
        for issue in self.issues.get_all_project_issues(self.config.child_host, self.config.child_token, old_id):
            for award in self.get_issue_emojis(self.config.parent_host, self.config.parent_token, old_id, issue["id"]):
                new_award_giver = self.users.find_user_by_email_comparison(award["user"]["id"])
                new_user_email = new_award_giver["email"]
                if users_map.get(new_user_email, None) is None:
                    data = {
                        "name": "temp_migration_token",
                        "expires_at": expiration_date,
                        "scopes": [
                            "api"
                        ]
                    }
                    new_impersonation_token = self.users.create_user_impersonation_token(self.config.parent_host, self.config.parent_token, new_award_giver["id"], data).json()
                    users_map[new_user_email] = new_impersonation_token
                else:
                    new_impersonation_token = users_map[new_user_email]
                
                

                

                
