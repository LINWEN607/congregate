import tarfile
import os
import json
import shutil

from congregate.helpers.base_class import BaseClass
from congregate.migration.gitlab.users import UsersClient
from congregate.aws import AwsClient


class ProjectExportClient(BaseClass):
    KEYS = ["author_id", "created_by_id", "user_id", "updated_by_id", "assignee_id", "merged_by_id", "merge_user_id",
            "last_edited_by_id", "closed_by_id"]

    def __init__(self):
        self.users = UsersClient()
        self.aws = AwsClient()
        self.users_map = {}
        super(ProjectExportClient, self).__init__()

    def update_project_export_members(self, name, namespace, filename):
        file_path, extract_path = self.generate_filepaths(name, namespace, filename)
        updated = self.__do_tar_and_rewrite(file_path, extract_path)
        self.aws.copy_file_to_s3(filename)
        self.remove_local_project_export(name, namespace, filename)
        os.chdir(self.app_path)
        return updated

    def update_project_export_members_for_local(self, name, namespace, filename):
        # generate_filepaths has an explicit call out for AWS work that we don't need
        # so don't use that
        file_path = self.get_file_path(filename)
        extract_path = self.get_extract_path(name, namespace)
        self.log.info(
            "name: {0} namespace: {1} filename: {2} file_path: {3} extract_path: {4}"
                .format(
                    name,
                    namespace,
                    filename,
                    file_path,
                    extract_path
                )
            )
        updated = self.__do_tar_and_rewrite(file_path, extract_path)
        shutil.rmtree(extract_path)
        os.chdir(self.app_path)
        return updated

    def get_file_path(self, filename):
        return "{0}/downloads/{1}".format(self.config.filesystem_path, filename)

    def get_extract_path(self, name, namespace):
        return "{0}/downloads/{1}_{2}".format(self.config.filesystem_path, name, namespace)

    def __do_tar_and_rewrite(self, file_path, extract_path):
        with tarfile.open(file_path, "r:gz") as tar:
            tar.extractall(path=extract_path)
        with tarfile.open(file_path, "w:gz") as tar:
            try:
                self.__rewrite_project_json(extract_path)
                tar.add(extract_path, arcname="")
                return True
            except ValueError, e:
                self.log.error("Failed to rewrite project JSON file {0}, with error:\n{1}".format(file_path, e))
                return False

    def remove_local_project_export(self, name, namespace, filename):
        file_path, extract_path = self.generate_filepaths(name, namespace, filename)
        os.remove(file_path)
        shutil.rmtree(extract_path)

    def generate_filepaths(self, name, namespace, filename):
        file_path = self.aws.get_local_file_path(filename)
        extract_path = "%s/downloads/%s_%s" % (self.config.filesystem_path, name, namespace)

        return file_path, extract_path

    def __rewrite_project_json(self, path):
        with open("%s/project.json" % path, "r") as f:
            data = json.load(f)

        # Build user map
        to_pop = []
        self.log.info("Building user map")
        for d in data["project_members"]:
            if d.get("user", None) is not None:
                if d["user"].get("email", None) is not None:
                    new_user = self.users.find_user_by_email_comparison_without_id(d["user"]["email"])
                    if new_user is not None:
                        d["user"]["id"] = new_user["id"]
                        self.users_map[d["user_id"]] = new_user["id"]
                        # We do the following to force the import tool to match on email
                        # Particularly useful when users have already been migrated ahead of project migration
                        # and may have a suffix on their username
                        d["user"]["username"] = "dont_have_this_username"
                    else:
                        self.log.warning("New user on destination was not found by email {0}".format(d))
                        d["user"]["id"] = self.config.import_user_id
                        self.users_map[d["user_id"]] = self.config.import_user_id
                        d["user"]['username'] = "This is invalid"
                else:
                    # No clue who this is, so set to import user
                    self.log.warning("Project member user entity had no email {0}".format(d))
                    d["user"]["id"] = self.config.import_user_id
                    self.users_map[d["user_id"]] = self.config.import_user_id
                    d["user"]['username'] = "This is invalid"
            # Members invited to group/project by other group/project members.
            # Not necessarily existing users on src nor dest instance.
            # Removing them rather than creating new user objects.
            elif d.get("invite_email", None) is not None:
                inviter = self.users.find_user_by_email_comparison_with_id(d.get("created_by_id"))
                self.log.warn("Skipping user {0}, invited by {1}".format(d.get("invite_email"), inviter))
                to_pop.append(data["project_members"].index(d))
            else:
                self.log.error("Project member has no user entity or invite email {0}. Skipping.".format(d))
                to_pop.append(data["project_members"].index(d))

        data["project_members"] = [i for j, i in enumerate(data["project_members"]) if j not in to_pop]

        # Update project_json
        self.__traverse_json(data)
        if data.get("merge_requests", None) is not None:
            self.__remove_notes_from_merge_requests(data["merge_requests"], "DiffNote")
            self.__remove_notes_from_merge_requests(data["merge_requests"], "Commit")
            self.__remove_suggestions_from_merge_requests(data["merge_requests"])
        if data.get("pipelines", None) is not None:
            self.__remove_notes_from_merge_requests(data["pipelines"], "DiffNote")
            self.__remove_notes_from_merge_requests(data["pipelines"], "Commit")
            # This line needs to be removed once https://gitlab.com/gitlab-org/gitlab-ce/issues/60121 is resolved
            data['pipelines'].reverse()
        if data.get("ci_pipelines", None) is not None:
            self.__remove_notes_from_merge_requests(data["ci_pipelines"], "DiffNote")
            self.__remove_notes_from_merge_requests(data["ci_pipelines"], "Commit")
            # This line needs to be removed once https://gitlab.com/gitlab-org/gitlab-ce/issues/60121 is resolved
            data['ci_pipelines'].reverse()
        if data.get("services", None) is not None:
            del data["services"]

        with open("%s/project.json" % path, "w") as f:
            json.dump(data, f, indent=4)

    def __traverse_json(self, data):
        if isinstance(data, dict):
            for k, v in data.items():
                if k in self.KEYS:
                    if v is not None:
                        data[k] = self.__find_or_create_id(v)
                else:
                    if isinstance(data[k], list):
                        for d in data[k]:
                            self.__traverse_json(d)
                    elif isinstance(data[k], dict):
                        self.__traverse_json(data[k])

    def __update_authors_and_events(self, data):
        for d in data:
            d["author_id"] = self.__find_or_create_id(d["author_id"])
            if d.get("closed_by_id", None) is not None:
                d["closed_by_id"] = self.__find_or_create_id(d["closed_by_id"])
            if d.get("issue_assignees", None) is not None:
                for a in d["issue_assignees"]:
                    self.__traverse_json(a)
            if d.get("events", None) is not None:
                for e in d["events"]:
                    self.__traverse_json(e)
            if d.get("notes", None) is not None:
                for n in d["notes"]:
                    self.__traverse_json(n)
            if d.get("resource_label_events", None) is not None:
                for r in d["resource_label_events"]:
                    self.__traverse_json(r)
            if d.get("metrics", None) is not None:
                self.__traverse_json(d["metrics"])

    def __update_project_members(self, data):
        for d in data:
            old_created_by_id = d["created_by_id"]
            if old_created_by_id is not None:
                new_created_by_id = self.__find_or_create_id(old_created_by_id)
                d["created_by_id"] = new_created_by_id
            old_user_id = d["user_id"]
            if old_user_id is not None:
                new_user_id = self.__find_or_create_id(old_user_id)
                d["user_id"] = new_user_id

    def __find_or_create_id(self, key):
        if self.users_map.get(key) is None:
            new_user = self.users.find_user_by_email_comparison_with_id(key)
            if new_user is not None:
                self.users_map[key] = new_user["id"]
                return new_user["id"]
            else:
                self.users_map[key] = self.config.import_user_id
        return self.users_map[key]

    def __remove_notes_from_merge_requests(self, mrs, comment_type):
        if mrs is not None:
            for i in range(0, len(mrs)):
                notes = []
                for x in range(0, len(mrs[i]["notes"])):
                    if mrs[i]["notes"][x].get("type", None) is not None:
                        if mrs[i]["notes"][x]["type"] == comment_type:
                            notes.append(x)
                    elif mrs[i]["notes"][x].get("noteable_type", None) is not None:
                        if mrs[i]["notes"][x]["noteable_type"] == comment_type:
                            notes.append(x)
                for d in reversed(notes):
                    del mrs[i]["notes"][d]

    def __remove_suggestions_from_merge_requests(self, mrs):
        for mr in mrs:
            mr["suggestions"] = []
