from datetime import timedelta, date
import json
from uuid import uuid4

from congregate.helpers.base_class import BaseClass
from congregate.migration.gitlab.importexport import ImportExportClient
from congregate.migration.gitlab.variables import VariablesClient
from congregate.migration.gitlab.users import UsersClient
from congregate.migration.gitlab.api.users import UsersApi
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.projects import ProjectsClient
from congregate.migration.gitlab.pushrules import PushRulesClient
from congregate.migration.gitlab.branches import BranchesClient
from congregate.migration.gitlab.merge_request_approvals import MergeRequestApprovalsClient
from congregate.migration.gitlab.awards import AwardsClient
from congregate.migration.gitlab.registries import RegistryClient
from congregate.migration.gitlab.pipeline_schedules import PipelineSchedulesClient
from congregate.migration.mirror import MirrorClient
from congregate.migration.gitlab.deploy_keys import DeployKeysClient


class SeedDataGenerator(BaseClass):
    def __init__(self):
        self.ie = ImportExportClient()
        self.mirror = MirrorClient()
        self.variables = VariablesClient()
        self.users = UsersClient()
        self.users_api = UsersApi()
        self.groups = GroupsApi()
        self.projects = ProjectsClient()
        self.pushrules = PushRulesClient()
        self.branches = BranchesClient()
        self.awards = AwardsClient()
        self.mra = MergeRequestApprovalsClient()
        self.registries = RegistryClient()
        self.schedules = PipelineSchedulesClient()
        self.deploy_keys = DeployKeysClient()
        super(SeedDataGenerator, self).__init__()

    def generate_seed_data(self, dry_run=True):
        dry_log = "DRY-RUN: " if dry_run else ""
        users = self.generate_users(dry_log, dry_run)
        groups = self.generate_groups(dry_log, dry_run)
        self.add_group_members(users, groups, dry_log, dry_run)
        projects = self.generate_group_projects(groups, dry_log, dry_run)
        for project in projects:
            self.generate_dummy_environment(project["id"], dry_log, dry_run)
        projects += self.generate_user_projects(users, dry_log, dry_run)

        print "---Generated Users---"
        print json.dumps(users, indent=4)
        print "---Generated Groups---"
        print json.dumps(groups, indent=4)
        print "---Generated Projects---"
        print json.dumps(projects, indent=4)

    def generate_users(self, dry_log, dry_run=True):
        dummy_users = [
            {
                "username": "john_smith",
                "email": "john@example.com",
                "name": "John Smith",
                "reset_password": True,
                "skip_confirmation": True
            },
            {
                "username": "jack_smith",
                "email": "jack@example.com",
                "name": "Jack Smith",
                "reset_password": True,
                "skip_confirmation": True
            },
            {
                "username": "jane_doe",
                "email": "jane@example.com",
                "name": "Jane Doe",
                "reset_password": True,
                "skip_confirmation": True,
                "theme_id": 3,
                "color_scheme_id": 3
            }
        ]
        created_users = []
        for user in dummy_users:
            user_search = list(self.users_api.search_for_user_by_email(
                self.config.source_host, self.config.source_token, user["email"]))
            if len(user_search) > 0:
                if user_search[0]["email"] == user["email"]:
                    self.log.info(
                        "User {} already exists".format(user["email"]))
                    created_users.append(user_search[0])
                else:
                    self.log.info("{0}Creating user {1}".format(
                        dry_log, user["email"]))
                    if not dry_run:
                        created_users.append(self.users_api.create_user(
                            self.config.source_host, self.config.source_token, user).json())
            else:
                self.log.info("{0}Creating user {1}".format(
                    dry_log, user["email"]))
                if not dry_run:
                    created_users.append(self.users_api.create_user(
                        self.config.source_host, self.config.source_token, user).json())

        return created_users

    def generate_groups(self, dry_log, dry_run=True):
        dummy_groups = [
            {
                "name": "Dummy Group 1",
                "path": "dummy-group-1"
            },
            {
                "name": "Dummy Group 2",
                "path": "dummy-group-2"
            }
        ]
        created_groups = []
        for group in dummy_groups:
            group_search = list(self.groups.search_for_group(
                group["path"], self.config.source_host, self.config.source_token))
            if len(group_search) > 0:
                if group_search[0]["path"] == group["path"]:
                    self.log.info(
                        "Group {} already exists".format(group["name"]))
                    created_groups.append(group_search[0])
                else:
                    self.log.info("{0}Creating group {1}".format(
                        dry_log, group["name"]))
                    if not dry_run:
                        created_groups.append(self.groups.create_group(
                            self.config.source_host, self.config.source_token, group).json())
            else:
                self.log.info("{0}Creating group {1}".format(
                    dry_log, group["name"]))
                if not dry_run:
                    created_groups.append(self.groups.create_group(
                        self.config.source_host, self.config.source_token, group).json())

        return created_groups

    def add_group_members(self, created_users, created_groups, dry_log, dry_run=True):
        for user in created_users:
            data = {
                "user_id": user["id"],
                "access_level": 40
            }
            self.log.info("{0}Adding user {1} ({2}) to group {3}".format(
                dry_log,
                user["email"],
                data,
                created_groups[-1]["name"]))
            if not dry_run:
                self.groups.add_member_to_group(
                    created_groups[-1]["id"], self.config.source_host, self.config.source_token, data)

    def generate_group_projects(self, created_groups, dry_log, dry_run=True):
        dummy_projects = {
            "spring": "https://gitlab.com/gitlab-org/project-templates/spring.git",
            "react": "https://gitlab.com/gitlab-org/project-templates/react.git",
            "android": "https://gitlab.com/gitlab-org/project-templates/android.git"
        }

        created_projects = []

        for project_name, project_url in dummy_projects.items():
            data = {
                "import_url": project_url,
                "namespace_id": created_groups[-1]["id"]
            }
            self.log.info(
                "{0}Creating group project ({1})".format(dry_log, data))
            if not dry_run:
                created_projects.append(self.projects.projects_api.create_project(
                    self.config.source_host, self.config.source_token, project_name, data).json())

        return created_projects

    def generate_user_projects(self, created_users, dry_log, dry_run=True):
        dummy_project_data = [
            {
                "name": "my-project",
                "import_url": "https://gitlab.com/gitlab-org/project-templates/spring.git"
            },
            {
                "name": "my-awesome-project",
                "import_url": "https://gitlab.com/gitlab-org/project-templates/react.git",
            },
            {
                "name": "test",
                "import_url": "https://gitlab.com/gitlab-org/project-templates/android.git"
            }
        ]
        created_projects = []
        users_map = {}
        expiration_date = (date.today() + timedelta(days=1)
                           ).strftime('%Y-%m-%d')
        for i in range(0, len(created_users)):
            user = created_users[i]
            self.log.info(
                "{0}Creating user project ({1})".format(dry_log, user))
            if not dry_run:
                token = self.users.find_or_create_impersonation_token(
                    self.config.source_host, self.config.source_token, user, users_map, expiration_date)
                if token.get("token") is not None:
                    created_projects.append(self.projects.projects_api.create_project(
                        self.config.source_host, token, dummy_project_data[i]["name"], data=dummy_project_data[i]).json())
                else:
                    dummy_project_data[i]["namespace"] = user["username"]
                    self.projects.projects_api.create_project(
                        self.config.source_host, self.config.source_token, dummy_project_data[i]["name"], data=dummy_project_data[i]).json()

        return created_projects

    def generate_dummy_environment(self, project_id, dry_log, dry_run=True):
        data = {
            "name": "production",
            "external_url": "http://production-%s.site" % uuid4()
        }
        self.log.info(
            "{0}Creating project environment ({1})".format(dry_log, data))
        if not dry_run:
            return self.projects.projects_api.create_environment(self.config.source_host, self.config.source_token, project_id, data)
