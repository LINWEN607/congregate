from congregate.helpers.base_class import BaseClass
from congregate.helpers import api
from congregate.helpers.misc_utils import strip_numbers, remove_dupes
from congregate.migration.gitlab.api.issues import IssuesApi
from congregate.migration.gitlab.api.merge_requests import MergeRequestsApi
from congregate.migration.gitlab.api.snippets import SnippetsApi
from congregate.migration.gitlab.users import UsersClient
from datetime import timedelta, date


class AwardsClient(BaseClass):
    AWARDABLES = ["issues", "merge_requests", "snippets"]

    def __init__(self):
        self.issues = IssuesApi()
        self.merge_requests = MergeRequestsApi()
        self.snippets = SnippetsApi()
        self.users = UsersClient()
        self.token_expiration_date = (date.today() + timedelta(days=2)
                                      ).strftime('%Y-%m-%d')
        self.awardable_client = None
        super(AwardsClient, self).__init__()

    def are_enabled(self, id):
        project = api.generate_get_request(self.config.source_host, self.config.source_token, "projects/%d" % id).json()
        return (project.get("issues_enabled", False),
                project.get("merge_requests_enabled", False),
                project.get("snippets_enabled", False))

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
        for awardable_name in self.AWARDABLES:
            self.__set_client(awardable_name)
            self.log.info("Migrating %s emojis for %d" %
                          (awardable_name, old_id))
            get_all_project_awardables = getattr(
                self.awardable_client, "get_all_project_%s" % awardable_name)
            for awardable in get_all_project_awardables(self.config.source_host, self.config.source_token, old_id):
                self.__handle_migrating_award(
                    awardable, awardable_name, old_id, new_id, users_map)

    def __handle_migrating_award(self, awardable, awardable_name, old_project_id, new_project_id, users_map):
        awardable_id = self.__get_awardable_id(awardable)

        if awardable_name == self.AWARDABLES[0]:
            get_single_project_awardable = self.issues.get_single_project_issues
        elif awardable_name == self.AWARDABLES[1]:
            get_single_project_awardable = self.merge_requests.get_single_project_merge_requests
        elif awardable_name == self.AWARDABLES[2]:
            get_single_project_awardable = self.snippets.get_single_project_snippets
        else:
            self.log.warn("Award type is not in the list")
        for award in self.__get_all_project_awardable_emojis(self.config.source_host, self.config.source_token, awardable_name, old_project_id, awardable_id):
            response = get_single_project_awardable(
                self.config.destination_host, self.config.destination_token, new_project_id, awardable_id)
            if response.status_code == 200:
                new_award_giver = self.users.find_user_by_email_comparison_with_id(
                    award["user"]["id"])

                impersonation_token = self.users.find_or_create_impersonation_token(
                    self.config.destination_host, self.config.destination_token, new_award_giver, users_map, self.token_expiration_date)

                self.__create_awardable_emoji(
                    self.config.destination_host, impersonation_token["token"], awardable_name, new_project_id, awardable_id, award["name"])
        self.__handle_migrating_note_awards(
            awardable, awardable_name, old_project_id, new_project_id, awardable_id, users_map)

    def __handle_migrating_note_awards(self, awardable, awardable_name, old_project_id, new_project_id, awardable_id, users_map):
        for note in self.__get_all_project_awardable_notes(self.config.source_host, self.config.source_token, awardable_name, old_project_id, awardable_id):
            note_id = note["id"]
            response = self.__get_single_project_awardable_note_emoji(
                self.config.source_host, self.config.source_token, awardable_name, old_project_id, awardable_id, note_id)
            if response.status_code == 200:
                notes_json = response.json()
                if len(notes_json) > 0:
                    dest_note = []
                    for x in self.__get_all_project_awardable_notes(
                        self.config.destination_host,
                        self.config.destination_token,
                        awardable_name,
                        new_project_id,
                        awardable_id
                    ):
                        dest_note.append(x)
                    # The destination note note_id is needed to assign the emoji
                    self.log.info("Destination note return was {0}".format(dest_note))

                    for dn in dest_note:
                        if isinstance(dn, dict):
                            for n in notes_json:
                                i = notes_json.index(n)
                                new_award_giver = self.users.find_user_by_email_comparison_with_id(
                                    n["user"]["id"])

                                impersonation_token = self.users.find_or_create_impersonation_token(
                                    self.config.destination_host,
                                    self.config.destination_token,
                                    new_award_giver,
                                    users_map,
                                    self.token_expiration_date
                                )

                                self.__create_awardable_note_emoji(
                                    self.config.destination_host,
                                    impersonation_token["token"],
                                    awardable_name,
                                    new_project_id,
                                    awardable_id,
                                    dest_note[i]["id"],
                                    n["name"]
                                )
                        else:
                            self.log.error(
                                "%s/api/v4/projects/%d/%s/%d didn't successfully migrate. Unable to migrate note award" %
                                (self.config.source_host, old_project_id, awardable_name, awardable_id))

    def __set_client(self, awardable_name):
        self.awardable_client = getattr(self, awardable_name)

    def __get_awardable_id(self, awardable):
        if awardable.get("iid", None) is not None:
            # iid is used for issues and merge requests
            return awardable["iid"]
        else:
            # id is used for snippets
            return awardable["id"]
