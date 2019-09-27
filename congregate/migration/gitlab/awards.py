from datetime import timedelta, date
from requests.exceptions import RequestException

from congregate.helpers.base_class import BaseClass
from congregate.helpers import api
from congregate.migration.gitlab.api.issues import IssuesApi
from congregate.migration.gitlab.api.merge_requests import MergeRequestsApi
from congregate.migration.gitlab.api.snippets import SnippetsApi
from congregate.migration.gitlab.users import UsersClient


class AwardsClient(BaseClass):
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
        return api.generate_post_request(host, token, "projects/%d/%s/%d/award_emoji?name=%s" % (
            project_id, awardable, awardable_id, name), None)

    def __get_all_project_awardable_notes(self, host, token, awardable, project_id, awardable_id):
        return api.list_all(host, token, "projects/%d/%s/%d/notes" % (project_id, awardable, awardable_id))

    def __get_single_project_awardable_note_emoji(self, host, token, awardable, project_id, awardable_id, note_id):
        return api.generate_get_request(host, token, "projects/%d/%s/%d/notes/%d/award_emoji" % (
            project_id, awardable, awardable_id, note_id))

    def __create_awardable_note_emoji(self, host, token, awardable, project_id, awardable_id, note_id, name):
        return api.generate_post_request(host, token, "projects/%d/%s/%d/notes/%d/award_emoji?name=%s" % (
            project_id, awardable, awardable_id, note_id, name), None)

    def migrate_awards(self, new_id, old_id, users_map, mr_enabled=False):
        AWARDABLES = {
            "issues": self.issues.get_single_project_issues,
            "merge_requests": self.merge_requests.get_single_project_merge_requests,
            "snippets": self.snippets.get_single_project_snippets
        }
        for k, v in AWARDABLES.items():
            if not mr_enabled and "merge_requests" in k:
                continue
            self.__set_client(k)
            self.log.info("Migrating project ID {0} {1}".format(old_id, k))
            get_all_project_awardables = getattr(
                self.awardable_client, "get_all_project_%s" % k)
            for awardable in get_all_project_awardables(self.config.source_host, self.config.source_token, old_id):
                self.log.info("Awardable is {0}".format(awardable))

                awardable_id = self.__get_awardable_id(awardable)
                self.log.info("Awardable id is {0}".format(awardable_id))

                get_single_project_awardable = v
                for award in self.__get_all_project_awardable_emojis(self.config.source_host,
                                                                     self.config.source_token,
                                                                     k,
                                                                     old_id,
                                                                     awardable_id):
                    self.log.info("Award is {0}".format(award))
                    try:
                        response = get_single_project_awardable(
                            self.config.destination_host,
                            self.config.destination_token,
                            new_id,
                            awardable_id
                        )
                        if response.status_code == 200:
                            self.log.info("Getting new award giver with {0}".format(award["user"]["id"]))
                            token = self.__generate_token(award["user"], users_map)

                            self.__create_awardable_emoji(
                                self.config.destination_host,
                                token,
                                k,
                                new_id,
                                awardable_id,
                                award["name"]
                            )
                        else:
                            raise RequestException(
                                "Response status code {0} and response content {1}".format(response.status_code,
                                                                                           response.content))
                    except RequestException as e:
                        self.log.error("Failed to migrate awardable {0} ID {1} emoji {2}, with error:\n{3}"
                                       .format(k, awardable_id, award["name"], e))
                self.__handle_migrating_note_awards(
                    k, old_id, new_id, awardable_id, users_map)

    def __handle_migrating_note_awards(self, awardable_name, old_project_id, new_project_id, awardable_id, users_map):
        for note in self.__get_all_project_awardable_notes(self.config.source_host, self.config.source_token,
                                                           awardable_name, old_project_id, awardable_id):
            note_id = note["id"]
            response = self.__get_single_project_awardable_note_emoji(
                self.config.source_host, self.config.source_token, awardable_name, old_project_id, awardable_id,
                note_id)
            try:
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
                        self.log.debug("Destination note return was {}".format(dest_note))

                        for dn in dest_note:
                            if isinstance(dn, dict):
                                for n in notes_json:
                                    i = notes_json.index(n)
                                    
                                    token = self.__generate_token(n["user"], users_map)

                                    self.__create_awardable_note_emoji(
                                        self.config.destination_host,
                                        token,
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
            except RequestException as e:
                self.log.error("Failed to migrate awardable {0} ID {1} note emoji {2}, with error:\n{4}"
                               .format(awardable_name, awardable_id, n["name"], e))

    def __generate_token(self, user, users_map):
        new_award_giver = self.users.find_user_primarily_by_email(user)
        if new_award_giver is not None:
            impersonation_token = self.users.find_or_create_impersonation_token(
                self.config.destination_host,
                self.config.destination_token,
                new_award_giver,
                users_map,
                self.token_expiration_date
            )
            return impersonation_token["token"]
        else:
            self.log.warn("Award giver not found. Defaulting to import user")
            return self.config.destination_token

    def __set_client(self, awardable_name):
        self.awardable_client = getattr(self, awardable_name)

    def __get_awardable_id(self, awardable):
        if awardable.get("iid", None) is not None:
            # issues and MRs have an iid
            return awardable["iid"]
        elif awardable.get("id", None) is not None:
            # snippets have an id
            return awardable["id"]
