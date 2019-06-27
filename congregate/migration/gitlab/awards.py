from helpers.base_class import BaseClass
from helpers import api
from helpers.misc_utils import strip_numbers, remove_dupes
from migration.gitlab.issues import IssuesClient
from migration.gitlab.merge_requests import MergeRequestsClient
from migration.gitlab.snippets import SnippetsClient
from migration.gitlab.users import UsersClient
from datetime import timedelta, date


class AwardsClient(BaseClass):
    def __init__(self):
        self.issues = IssuesClient()
        self.merge_requests = MergeRequestsClient()
        self.snippets = SnippetsClient()
        self.users = UsersClient()
        self.token_expiration_date = (date.today() + timedelta(days=2)
                                      ).strftime('%Y-%m-%d')
        self.awardables = ["issues", "merge_requests", "snippets"]
        self.awardable_client = None
        super(AwardsClient, self).__init__()

    def __get_all_project_awardable_emojis(self, host, token, awardable, project_id, awardable_id):
        return api.list_all(host, token, "projects/%d/%s/%d/award_emoji" % (project_id, awardable, awardable_id))

    def __create_awardable_emoji(self, host, token, awardable, project_id, awardable_id, name):
        return api.generate_post_request(host, token, "projects/%d/%s/%d/award_emoji?name=%s" % (project_id, awardable, awardable_id, name), None)

    def __get_all_project_awardable_notes(self, host, token, awardable, project_id, awardable_id):
        return api.list_all(host, token, "projects/%d/%s/%d/notes" % (project_id, awardable, awardable_id))

    def __get_single_project_awardable_note_emoji(self, host, token, awardable, project_id, awardable_id, note_id):
        return api.generate_get_request(host, token, "projects/%d/%s/%d/notes/%d/award_emoji" % (project_id, awardable, awardable_id, note_id))

    def __create_awardable_note_emoji(self, host, token, awardable, project_id, awardable_id, note_id, name):
        return api.generate_post_request(host, token, "projects/%d/%s/%d/notes/%d/award_emoji?name=%s" % (project_id, awardable, awardable_id, note_id, name), None)

    def migrate_awards(self, new_id, old_id, users_map):
        self.log.info("Migrating awards")
        for awardable_name in self.awardables:
            self.__set_client(awardable_name)
            self.log.info("Migrating %s emojis for %d" %
                          (awardable_name, old_id))
            get_all_project_awardables = getattr(
                self.awardable_client, "get_all_project_%s" % awardable_name)
            for awardable in get_all_project_awardables(self.config.child_host, self.config.child_token, old_id):
                self.__handle_migrating_award(
                    awardable, awardable_name, old_id, new_id, users_map)

    def __handle_migrating_award(self, awardable, awardable_name, old_project_id, new_project_id, users_map):
        awardable_id = self.__get_awardable_id(awardable)

        get_single_project_awardable = getattr(
            self.awardable_client, "get_single_project_%s" % awardable_name)
        for award in self.__get_all_project_awardable_emojis(self.config.child_host, self.config.child_token, awardable_name, old_project_id, awardable_id):
            response = get_single_project_awardable(
                self.config.parent_host, self.config.parent_token, new_project_id, awardable_id)
            if response.status_code == 200:
                new_award_giver = self.users.find_user_by_email_comparison(
                    award["user"]["id"])

                impersonation_token = self.users.find_or_create_impersonation_token(
                    new_award_giver, users_map, self.token_expiration_date)

                self.__create_awardable_emoji(
                    self.config.parent_host, impersonation_token["token"], awardable_name, new_project_id, awardable_id, award["name"])
                self.__handle_migrating_note_awards(
                    awardable, awardable_name, old_project_id, new_project_id, awardable_id, users_map)

    def __handle_migrating_note_awards(self, awardable, awardable_name, old_project_id, new_project_id, awardable_id, users_map):
        for note in self.__get_all_project_awardable_notes(self.config.child_host, self.config.child_token, awardable_name, old_project_id, awardable_id):
            note_id = note["id"]
            response = self.__get_single_project_awardable_note_emoji(
                self.config.child_host, self.config.child_token, awardable_name, old_project_id, awardable_id, note_id)
            if response.status_code == 200:
                notes_json = response.json()
                if len(notes_json) > 0:
                    for n in notes_json:
                        new_award_giver = self.users.find_user_by_email_comparison(
                            n["user"]["id"])

                        impersonation_token = self.users.find_or_create_impersonation_token(
                            new_award_giver, users_map, self.token_expiration_date)

                        self.__create_awardable_note_emoji(
                            self.config.parent_host, impersonation_token["token"], awardable_name, new_project_id, awardable_id, note_id, n["name"])

    def __set_client(self, awardable_name):
        self.awardable_client = getattr(self, awardable_name)

    def __get_awardable_id(self, awardable):
        if awardable.get("iid", None) is not None:
            # iid is used for issues and merge requests
            return awardable["iid"]
        else:
            # id is used for snippets
            return awardable["id"]
