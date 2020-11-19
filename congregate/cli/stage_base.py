"""
Congregate - GitLab instance migration utility

Copyright (c) 2020 - GitLab
"""

import json
from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import get_dry_log, remove_dupes


class BaseStageClass(BaseClass):
    def __init__(self):
        self.staged_users = []
        self.staged_projects = []
        self.staged_groups = []
        self.rewritten_users = {}
        self.rewritten_projects = {}
        self.rewritten_groups = {}
        super(BaseStageClass, self).__init__()

    def open_projects_file(self, i, scm_source=None):
        """
            Open project.json file to read, turning JSON encoded data to projects.

            :return: projects object
        """
        if scm_source is not None:
            with open(f'%s/data/projects-{i}.json' % self.app_path, "r") as f:
                return json.load(f)
        else:
            with open('%s/data/projects.json' % self.app_path, "r") as f:
                return json.load(f)

    def open_groups_file(self, i, scm_source=None):
        """
            Open group.json file to read, turning JSON encoded data to groups object.

            :return: groups object
        """
        if scm_source is not None:
            with open(f"%s/data/groups-{i}.json" % self.app_path, "r") as f:
                return json.load(f)
        else:
            with open("%s/data/groups.json" % self.app_path, "r") as f:
                return json.load(f)

    def open_users_file(self, i, scm_source=None):
        """
            Open users.json file to read, turning JSON encoded data to users object.

            :return: users object
        """
        if scm_source is not None:
            with open(f"{self.app_path}/data/users-{i}.json", "r") as f:
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
            f.write(json.dumps(remove_dupes(self.staged_groups), indent=4))
        with open("%s/data/staged_projects.json" % self.app_path, "w") as f:
            f.write(json.dumps(remove_dupes(self.staged_projects), indent=4))
        with open("%s/data/staged_users.json" % self.app_path, "w") as f:
            f.write(json.dumps([] if skip_users else remove_dupes(
                self.staged_users), indent=4))

    def append_member_to_members_list(self, members_list, member, dry_run=True):
        """
            Appends the members found in the /members endpoint to the staged asset object

            params: rewritten_users: object containing the various users from the instance
            params: staged_users:  object containing the specific users to be staged
            params: member_users: object containing the specific members of the group or project
            params: rewritten_users: object containing the specific member to be added to the group or project
        """
        if isinstance(member, dict):
            if member.get("id", None) is not None:
                self.log.info("{0}Staging user {1} (ID: {2})".format(
                    get_dry_log(dry_run), member["username"], member["id"]))
                self.staged_users.append(
                    self.rewritten_users[member["id"]])
                members_list.append(member)
        else:
            self.log.error(member)

    def get_project_metadata(self, project):
        """
            Get the object data providing project information

            :param project: (str) project information
            :return: obj object
        """
        obj = {
            "id": project["id"],
            "name": project["name"],
            "namespace": project["namespace"]["full_path"],
            "path": project["path"],
            "path_with_namespace": project["path_with_namespace"],
            "visibility": project["visibility"],
            "description": project["description"],
            # Will be deprecated in favor of builds_access_level
            "jobs_enabled": project.get("jobs_enabled", None),
            "project_type": project["namespace"]["kind"],
            # Project members are not listed when listing group projects
            "members": project["members"] if project.get("members", None) else self.rewritten_projects[project["id"]]["members"]
        }
        if project.get("ci_sources", None):
            obj["ci_sources"] = project["ci_sources"]
        if self.config.source_type == "gitlab":
            obj["http_url_to_repo"] = project["http_url_to_repo"]
            obj["shared_runners_enabled"] = project["shared_runners_enabled"]
            obj["archived"] = project["archived"]
            obj["shared_with_groups"] = project["shared_with_groups"]

        if self.config.source_type == "gitlab" or self.config.source_type == "bitbucket server":
            # In case of projects without repos (e.g. Wiki)
            if "default_branch" in project:
                obj["default_branch"] = project["default_branch"]
        return obj

    def the_number_of_instance(self, scm_source):
        for i, single_source in enumerate(self.config.list_multiple_source_config("github_source")):
            if scm_source == single_source.get("src_hostname", None):
                return i
        return -1