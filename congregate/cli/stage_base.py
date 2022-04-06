"""
Congregate - GitLab instance migration utility

Copyright (c) 2022 - GitLab
"""

import json

from gitlab_ps_utils.misc_utils import get_dry_log, strip_netloc
from gitlab_ps_utils.list_utils import remove_dupes_with_keys, remove_dupes
from gitlab_ps_utils.dict_utils import dig
from gitlab_ps_utils.json_utils import json_pretty

from congregate.helpers.base_class import BaseClass
from congregate.helpers.migrate_utils import validate_name, is_gl_version_older_than


class BaseStageClass(BaseClass):
    def __init__(self):
        self.staged_users = []
        self.staged_projects = []
        self.staged_groups = []
        self.rewritten_users = {}
        self.rewritten_projects = {}
        self.rewritten_groups = {}
        super().__init__()

    def open_projects_file(self, scm_source=None):
        """
            Open project.json file to read, turning JSON encoded data to projects.

            :return: projects object
        """
        if scm_source is not None:
            with open(f'%s/data/projects-{scm_source}.json' % self.app_path, "r") as f:
                return json.load(f)
        else:
            with open('%s/data/projects.json' % self.app_path, "r") as f:
                return json.load(f)

    def open_groups_file(self, scm_source=None):
        """
            Open group.json file to read, turning JSON encoded data to groups object.

            :return: groups object
        """
        if scm_source is not None:
            with open(f"%s/data/groups-{scm_source}.json" % self.app_path, "r") as f:
                return json.load(f)
        else:
            with open("%s/data/groups.json" % self.app_path, "r") as f:
                return json.load(f)

    def open_users_file(self, scm_source=None):
        """
            Open users.json file to read, turning JSON encoded data to users object.

            :return: users object
        """
        if scm_source is not None:
            with open(f"{self.app_path}/data/users-{scm_source}.json", "r") as f:
                return json.load(f)
        else:
            with open("%s/data/users.json" % self.app_path, "r") as f:
                return json.load(f)

    def write_staging_files(self, skip_users=False):
        """
            Write all staged projects, users and groups objects into JSON files

            :param: staging: (dict) staged projects
            :param: staged_users:(dict) staged users
            :param: staged_groups: (dict) staged groups
        """
        with open("%s/data/staged_groups.json" % self.app_path, "w") as f:
            if self.config.wave_spreadsheet_path:
                f.write(json.dumps(remove_dupes_with_keys(
                    self.staged_groups, ["id", "full_path"]), indent=4))
            else:
                f.write(json.dumps(remove_dupes(self.staged_groups), indent=4))
        with open("%s/data/staged_projects.json" % self.app_path, "w") as f:
            f.write(json.dumps(remove_dupes(self.staged_projects), indent=4))
        with open("%s/data/staged_users.json" % self.app_path, "w") as f:
            f.write(json.dumps([] if skip_users else remove_dupes(
                self.staged_users), indent=4))

    def append_member_to_members_list(
            self, members_list, member, dry_run=True):
        """
            Appends the members found in the /members endpoint to the staged asset object

            params: rewritten_users: object containing the various users from the instance
            params: staged_users:  object containing the specific users to be staged
            params: member_users: object containing the specific members of the group or project
            params: rewritten_users: object containing the specific member to be added to the group or project
        """
        if isinstance(member, dict):
            if member.get("id") is not None:
                self.log.info("{0}Staging user {1} (ID: {2})".format(
                    get_dry_log(dry_run), member["username"], member["id"]))
                if self.rewritten_users.get(member['id']):
                    self.staged_users.append(
                        self.rewritten_users[member["id"]])
                    members_list.append(member)
        else:
            self.log.error(member)

    def get_project_metadata(self, project, group=False):
        """
            Get the object data providing project information

            :param project: (str) project information
            :return: obj object
        """
        try:
            # If group=True a project IDs is passed
            project = self.rewritten_projects[project] if group else project
            obj = {
                "id": project["id"],
                "name": validate_name(project["name"]),
                "namespace": dig(project, 'namespace', 'full_path'),
                "path": project["path"],
                "path_with_namespace": project["path_with_namespace"],
                "visibility": project["visibility"],
                "description": project["description"],
                # Will be deprecated in favor of builds_access_level
                "jobs_enabled": project.get("jobs_enabled"),
                "project_type": dig(project, 'namespace', 'kind'),
                "members": project["members"],
                "http_url_to_repo": project["http_url_to_repo"]
            }
            if project.get("ci_sources"):
                obj["ci_sources"] = project["ci_sources"]
            if self.config.source_type == "gitlab":
                obj["shared_runners_enabled"] = project["shared_runners_enabled"]
                obj["archived"] = project["archived"]
                obj["shared_with_groups"] = project["shared_with_groups"]
                if mr_template := project.get("merge_requests_template"):
                    obj["merge_requests_template"] = mr_template
                if fork_origin := project.get("forked_from_project"):
                    obj["forked_from_project"] = fork_origin
            if self.config.source_type in ["gitlab", "bitbucket server"]:
                # In case of projects without repos (e.g. Wiki)
                if branch := project.get("default_branch"):
                    obj["default_branch"] = branch
        except KeyError as ke:
            self.log.error(
                f"Failed to retrieve project details for project {project['path_with_namespace']} (ID: {project['id']}), with key error\n{ke}")
            return {}
        return obj

    def the_number_of_instance(self, scm_source):
        for i, single_source in enumerate(
                self.config.list_multiple_source_config("github_source")):
            if scm_source == strip_netloc(
                    single_source.get("src_hostname", "")):
                return i
        return -1

    @classmethod
    def format_group(cls, group):
        # Decrease size of staged_groups.json
        group.pop("projects", None)
        group.pop("desc_groups", None)
        group["name"] = validate_name(group["name"], is_group=True)
        return group

    def list_staged_users_without_public_email(self):
        if is_gl_version_older_than(14, self.config.source_host, self.config.source_token, "SKIP: Not mandatory to set 'public_email' field for staged users"):
            return
        if self.staged_users:
            no_public_email = [{
                "email": u.get("email"),
                "public_email": u.get("public_email")
            } for u in remove_dupes(self.staged_users) if u.get("email") != u.get("public_email")]
            if no_public_email:
                self.log.warning(
                    f"Staged users with incorrect (not primary email) or no `public_email` field set ({len(no_public_email)}):\n{json_pretty(no_public_email)}")
