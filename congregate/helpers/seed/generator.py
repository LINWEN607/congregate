from datetime import timedelta, date
import json
from uuid import uuid4

from gitlab_ps_utils.misc_utils import get_dry_log
from congregate.helpers.base_class import BaseClass
from congregate.migration.gitlab.importexport import ImportExportClient
from congregate.migration.gitlab.variables import VariablesClient
from congregate.migration.gitlab.users import UsersClient
from congregate.migration.gitlab.api.users import UsersApi
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.api.instance import InstanceApi
from congregate.migration.gitlab.api.settings import SettingsAPI
from congregate.migration.gitlab.projects import ProjectsClient
from congregate.migration.gitlab.pushrules import PushRulesClient
from congregate.migration.gitlab.branches import BranchesClient
from congregate.migration.gitlab.merge_request_approvals import MergeRequestApprovalsClient
from congregate.migration.gitlab.registries import RegistryClient
from congregate.migration.gitlab.keys import KeysClient
from congregate.migration.mirror import MirrorClient


class SeedDataGenerator(BaseClass):
    HOOKS_DATA = [
        {
            "url": "http://example.com",
            "push_events": True,
            "tag_push_events": False,
            "merge_requests_events": True,
            "repository_update_events": False,
            "enable_ssl_verification": False,
            "issues_events": False,
            "confidential_issues_events": False,
            "note_events": True,
            "confidential_note_events": None,
            "pipeline_events": False,
            "wiki_page_events": False,
            "job_events": False
        },
        {
            "url": "http://example2.com",
            "push_events": True,
            "tag_push_events": False,
            "merge_requests_events": False,
            "repository_update_events": False,
            "enable_ssl_verification": True,
            "issues_events": False,
            "confidential_issues_events": True,
            "note_events": False,
            "confidential_note_events": None,
            "pipeline_events": False,
            "wiki_page_events": False,
            "job_events": False
        }
    ]
    VARIABLES_DATA = [
        {
            "key": "NEW_VARIABLE",
            "value": "updated value",
            "variable_type": "env_var",
            "protected": True,
            "masked": False,
            "environment_scope": "staging"
        },
        {
            "key": "NEWER_VARIABLE",
            "value": "this is another variable",
            "variable_type": "env_var",
            "protected": True,
            "masked": False,
            "environment_scope": "production"
        }
    ]
    CLUSTERS_DATA = [
        {
            "name": "test-cluster-1",
            "domain": "test1.com",
            "environment_scope": "test1",
            "platform_kubernetes_attributes": {
                "api_url": "https://36.111.51.20",
                "token": "test1",
                "namespace": None,
                "authorization_type": "rbac",
                "ca_cert": "-----BEGIN CERTIFICATE-----\nMIIFDjCCAvYCCQDoZqaTnuVIMzANBgkqhkiG9w0BAQsFADBJMQswCQYDVQQGEwJO\nTDELMAkGA1UECAwCU0gxDzANBgNVBAoMBkdpdExhYjEcMBoGCSqGSIb3DQEJARYN\ndGVzdEB0ZXN0LmNvbTAeFw0yMDEwMzAxNzEzMjNaFw0yMTEwMzAxNzEzMjNaMEkx\nCzAJBgNVBAYTAk5MMQswCQYDVQQIDAJTSDEPMA0GA1UECgwGR2l0TGFiMRwwGgYJ\nKoZIhvcNAQkBFg10ZXN0QHRlc3QuY29tMIICIjANBgkqhkiG9w0BAQEFAAOCAg8A\nMIICCgKCAgEAxYESkMcdZM0/ZwyKC83+1uqdROkk2T4AaH0dWtWRvG3X+nO3pUeS\nzCJ5fgOvdtelJAxEmUUCPlD+BApwjJDE6Tl/qNNv44uHM7QAGigXbD4urBzRFzQh\nsZ9mEseaUfLH1QAb6vk/LdgxDkbeaovTUeMafvE467OWTO4iLaApDZTk6gdsO2gi\nQkPaAqf1XhKFowWQrO4GnZVbN66/ja8ZSOXi8wWzJKTwN5ZQR9oCPbetIDBD6KK6\nkKom7ht2zLcxMx/g0bodnSaResMXbPTYKB+Lou4ja4lSRfUGyGa6x1GSQsIcyr12\nbm4xcQylEQEsy9XgCJGsmXfJ8PnEKp2Fu4HwhTsE3dXIeE/x+OAOiDUoc6BT/LDW\nqWchExV/jUkHmPlii3dJ/NXsuCA/5RBga3ES9pEI/+HzYvXhiUBFaJEOhiU887uJ\nk9mGB2uJD/No7RtA579oTOHMLsplNmH7i3lAzKGtL7tMmRmvFa/BCvekpr0FJr17\nr7dU+T/8JtJ5hg0TUOgOTBL57X8E6SvXJ3ZdV0Ml5BpZCtpZbD7Xu7xBXX1jdlR+\nKyN2y8yq9kv86eq0SdSQ3VJ6sXd8RLiSzdtL85QPVC5NyBW5QfbIAC81I0lBBpgc\nLKISJi8UM0EdgmSGFK9JwO+AQqyVi7WMyMo1vW1B01hWWft5bhyW/MkCAwEAATAN\nBgkqhkiG9w0BAQsFAAOCAgEAEUlKdRDNsXpxTJrOhb2fSiylm4Cm/jsmSRrpK53Q\n73rpMzf0xy3C6pSjQGR4d7GP/3bLeYiJLHQma+oYorKv5pgyoInwZkYArcLiqfLu\npapI9NIYVwrI3QO60p0kwc+Tmj0m2sFEbH9Oj8qCu6DxOxaZ1llmzq0zS/AdzyZ0\nw0jEn391y9aYYWiOUzNBLo95CT/DZSrIDXKigsQn5sBXnTF2xtMyV3BSoz/hv5rX\njTjCcCFajzgvxl0z3zsjlDWV7t5kWbTLMxALlkpKjMPE0eSsZdeBQTAC51VBT3xc\nbDefR0snQctYdlrUxEIx9nC6QVecjgjKHWzG8SgiuItMvgZHM40gdPDUaAml6svg\n/1e0wxaJnmndT9acwSCFCQswlgQmso8yh4HILhO9ZaC9G5d+nr2mPs68gn69L/Mi\nEzMqwG8hZ860z+KWQs/S2RufzKOfwIy0/SXTq5f6WrxKTln46CMjHSueaenoMr1Q\n8q/koh/zx5f8HDAhaieQM7LUkTVoZTbjof+m82aveqxXgFlEITA3ciVqUrOAaWZb\n8U48lwlB/xOtEXrgL7sMF2bwk5AeNtGjZG7lpBhiHFP3NGj+fs97UItjV73NqulQ\nrSYVvsu9fWIyWx0Z2Izi10wq9V0R3uAwbAthLB3JK/iNC/0mK5+kIWxn8QafZlwK\nkpM=\n-----END CERTIFICATE-----"
            },
            "management_project_id": 1
        },
        {
            "name": "test-cluster-2",
            "domain": "test2.com",
            "environment_scope": "test2",
            "platform_kubernetes_attributes": {
                "api_url": "https://36.111.51.20",
                "token": "test2",
                "namespace": None,
                "authorization_type": "rbac",
                "ca_cert": "-----BEGIN CERTIFICATE-----\nMIIFDjCCAvYCCQDoZqaTnuVIMzANBgkqhkiG9w0BAQsFADBJMQswCQYDVQQGEwJO\nTDELMAkGA1UECAwCU0gxDzANBgNVBAoMBkdpdExhYjEcMBoGCSqGSIb3DQEJARYN\ndGVzdEB0ZXN0LmNvbTAeFw0yMDEwMzAxNzEzMjNaFw0yMTEwMzAxNzEzMjNaMEkx\nCzAJBgNVBAYTAk5MMQswCQYDVQQIDAJTSDEPMA0GA1UECgwGR2l0TGFiMRwwGgYJ\nKoZIhvcNAQkBFg10ZXN0QHRlc3QuY29tMIICIjANBgkqhkiG9w0BAQEFAAOCAg8A\nMIICCgKCAgEAxYESkMcdZM0/ZwyKC83+1uqdROkk2T4AaH0dWtWRvG3X+nO3pUeS\nzCJ5fgOvdtelJAxEmUUCPlD+BApwjJDE6Tl/qNNv44uHM7QAGigXbD4urBzRFzQh\nsZ9mEseaUfLH1QAb6vk/LdgxDkbeaovTUeMafvE467OWTO4iLaApDZTk6gdsO2gi\nQkPaAqf1XhKFowWQrO4GnZVbN66/ja8ZSOXi8wWzJKTwN5ZQR9oCPbetIDBD6KK6\nkKom7ht2zLcxMx/g0bodnSaResMXbPTYKB+Lou4ja4lSRfUGyGa6x1GSQsIcyr12\nbm4xcQylEQEsy9XgCJGsmXfJ8PnEKp2Fu4HwhTsE3dXIeE/x+OAOiDUoc6BT/LDW\nqWchExV/jUkHmPlii3dJ/NXsuCA/5RBga3ES9pEI/+HzYvXhiUBFaJEOhiU887uJ\nk9mGB2uJD/No7RtA579oTOHMLsplNmH7i3lAzKGtL7tMmRmvFa/BCvekpr0FJr17\nr7dU+T/8JtJ5hg0TUOgOTBL57X8E6SvXJ3ZdV0Ml5BpZCtpZbD7Xu7xBXX1jdlR+\nKyN2y8yq9kv86eq0SdSQ3VJ6sXd8RLiSzdtL85QPVC5NyBW5QfbIAC81I0lBBpgc\nLKISJi8UM0EdgmSGFK9JwO+AQqyVi7WMyMo1vW1B01hWWft5bhyW/MkCAwEAATAN\nBgkqhkiG9w0BAQsFAAOCAgEAEUlKdRDNsXpxTJrOhb2fSiylm4Cm/jsmSRrpK53Q\n73rpMzf0xy3C6pSjQGR4d7GP/3bLeYiJLHQma+oYorKv5pgyoInwZkYArcLiqfLu\npapI9NIYVwrI3QO60p0kwc+Tmj0m2sFEbH9Oj8qCu6DxOxaZ1llmzq0zS/AdzyZ0\nw0jEn391y9aYYWiOUzNBLo95CT/DZSrIDXKigsQn5sBXnTF2xtMyV3BSoz/hv5rX\njTjCcCFajzgvxl0z3zsjlDWV7t5kWbTLMxALlkpKjMPE0eSsZdeBQTAC51VBT3xc\nbDefR0snQctYdlrUxEIx9nC6QVecjgjKHWzG8SgiuItMvgZHM40gdPDUaAml6svg\n/1e0wxaJnmndT9acwSCFCQswlgQmso8yh4HILhO9ZaC9G5d+nr2mPs68gn69L/Mi\nEzMqwG8hZ860z+KWQs/S2RufzKOfwIy0/SXTq5f6WrxKTln46CMjHSueaenoMr1Q\n8q/koh/zx5f8HDAhaieQM7LUkTVoZTbjof+m82aveqxXgFlEITA3ciVqUrOAaWZb\n8U48lwlB/xOtEXrgL7sMF2bwk5AeNtGjZG7lpBhiHFP3NGj+fs97UItjV73NqulQ\nrSYVvsu9fWIyWx0Z2Izi10wq9V0R3uAwbAthLB3JK/iNC/0mK5+kIWxn8QafZlwK\nkpM=\n-----END CERTIFICATE-----"
            },
            "management_project_id": 2
        }
    ]

    BRANCH_DATA = [
        {
            "branch": "test-branch",
            "ref": "master"
        },
        {
            "branch": "test-branch2",
            "ref": "master"
        },
        {
            "branch": "test-branch3",
            "ref": "master"
        }
    ]

    def __init__(self):
        self.ie = ImportExportClient()
        self.mirror = MirrorClient()
        self.variables = VariablesClient()
        self.users = UsersClient()
        self.users_api = UsersApi()
        self.groups_api = GroupsApi()
        self.projects = ProjectsClient()
        self.projects_api = ProjectsApi()
        self.instance_api = InstanceApi()
        self.settings_api = SettingsAPI()
        self.pushrules = PushRulesClient()
        self.branches = BranchesClient()
        self.mra = MergeRequestApprovalsClient()
        self.registries = RegistryClient()
        self.keys = KeysClient()
        super().__init__()

    def generate_seed_data(self, dry_run=True):
        users = self.generate_users(dry_run)
        users.append({
            'id': 1,
            'email': 'admin@example.com'
        })
        groups = self.generate_groups(dry_run)
        for u in users:
            self.generate_dummy_user_keys(u["id"], dry_run)
        for g in groups:
            self.add_group_members(users, g["id"], dry_run)
            self.generate_dummy_group_variables(g["id"], dry_run)
            self.generate_dummy_group_hooks(g["id"], dry_run)
            self.generate_dummy_group_clusters(g["id"], dry_run)
            self.generate_bot_user(g["id"], "group", dry_run)
        projects = self.generate_group_projects(groups, dry_run)
        for p in projects:
            self.add_project_members(users, p["id"], dry_run)
            self.generate_dummy_branches(p["id"], dry_run)
            self.generate_dummy_environment(p["id"], dry_run)
            self.generate_dummy_project_hooks(p["id"], dry_run)
            self.generate_dummy_project_deploy_keys(p["id"], dry_run)
            self.generate_dummy_project_push_rules(p["id"], dry_run)
            self.generate_dummy_project_variables(p["id"], dry_run)
            self.generate_shared_with_group_data(p["id"], groups, dry_run)
            self.generate_dummy_project_clusters(p["id"], dry_run)
            self.generate_bot_user(p["id"], "project", dry_run)
        projects += self.generate_user_projects(users, dry_run)
        self.generate_instance_clusters(dry_run)
        self.generate_instance_hooks(dry_run)
        self.enable_importers()

        print("---Generated Users---")
        print(json.dumps(users, indent=4))
        print("---Generated Groups---")
        print(json.dumps(groups, indent=4))
        print("---Generated Projects---")
        print(json.dumps(projects, indent=4))

    def generate_instance_clusters(self, dry_run=True):
        for d in self.CLUSTERS_DATA:
            self.log.info(
                f"{get_dry_log(dry_run)}Creating instance cluster ({d})")
            if not dry_run:
                self.instance_api.add_instance_cluster(
                    self.config.source_host, self.config.source_token, d)

    def generate_instance_hooks(self, dry_run=True):
        for d in self.HOOKS_DATA:
            self.log.info(
                f"{get_dry_log(dry_run)}Creating instance hook ({d})")
            if not dry_run:
                self.instance_api.add_instance_hook(
                    self.config.source_host, self.config.source_token, d)

    def generate_users(self, dry_run=True):
        dummy_users = [
            {
                "username": "john_smith",
                "email": "john@example.com",
                "name": "John Smith",
                "reset_password": True,
                "skip_confirmation": True,
                "using_license_seat": True
            },
            {
                "username": "jack_smith",
                "email": "jack@example.com",
                "name": "Jack Smith",
                "reset_password": True,
                "skip_confirmation": True,
                "using_license_seat": True
            },
            {
                "username": "jane_doe",
                "email": "jane@example.com",
                "name": "Jane Doe",
                "reset_password": True,
                "skip_confirmation": True,
                "using_license_seat": True
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
                        get_dry_log(dry_run), user["email"]))
                    if not dry_run:
                        created_users.append(self.users_api.create_user(
                            self.config.source_host, self.config.source_token, user).json())
            else:
                self.log.info("{0}Creating user {1}".format(
                    get_dry_log(dry_run), user["email"]))
                if not dry_run:
                    created_users.append(self.users_api.create_user(
                        self.config.source_host, self.config.source_token, user).json())

        return created_users

    def generate_bot_user(self, oid, token_type, dry_run=True):
        """
            Generate a group and project access token i.e. bot user
        """
        host = self.config.source_host
        token = self.config.source_token
        data = {
            "name": f"test_{token_type}_access_token",
            "scopes": ["read_api"],
            "expires_at": "2049-01-01",
            "access_level": 10
        }
        self.log.info(
            f"{get_dry_log(dry_run)}Creating {token_type} {oid} access token")
        if not dry_run:
            if token_type == "group":
                self.groups_api.create_group_access_token(
                    oid, host, token, data)
            if token_type == "project":
                self.projects_api.create_project_access_token(
                    oid, host, token, data)

    def generate_groups(self, dry_run=True):
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
            group_search = list(self.groups_api.search_for_group(
                group["path"], self.config.source_host, self.config.source_token))
            if len(group_search) > 0:
                if group_search[0]["path"] == group["path"]:
                    self.log.info(
                        "Group {} already exists".format(group["name"]))
                    created_groups.append(group_search[0])
                else:
                    self.log.info("{0}Creating group {1}".format(
                        get_dry_log(dry_run), group["name"]))
                    if not dry_run:
                        created_groups.append(self.groups_api.create_group(
                            self.config.source_host, self.config.source_token, group).json())
            else:
                self.log.info("{0}Creating group {1}".format(
                    get_dry_log(dry_run), group["name"]))
                if not dry_run:
                    created_groups.append(self.groups_api.create_group(
                        self.config.source_host, self.config.source_token, group).json())

        return created_groups

    def add_group_members(self, created_users, gid, dry_run=True):
        for user in created_users:
            data = {
                "user_id": user["id"]
            }
            if user['id'] == 1:
                data["access_level"] = 50
            else:
                data["access_level"] = 30
            self.log.info("{0}Adding user {1} ({2}) to group {3}".format(
                get_dry_log(dry_run), user["email"], data, gid))
            if not dry_run:
                self.groups_api.add_member_to_group(
                    gid, self.config.source_host, self.config.source_token, data)

    def add_project_members(self, created_users, pid, dry_run=True):
        for user in created_users:
            data = {
                "user_id": user["id"],
                "access_level": 40
            }
            self.log.info("{0}Adding user {1} ({2}) to project {3}".format(
                get_dry_log(dry_run), user["email"], data, pid))
            if not dry_run:
                self.projects_api.add_member(
                    pid, self.config.source_host, self.config.source_token, data)

    def generate_group_projects(self, created_groups, dry_run=True):
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
                "{0}Creating group project ({1})".format(get_dry_log(dry_run), data))
            if not dry_run:
                created_projects.append(self.projects.projects_api.create_project(
                    self.config.source_host, self.config.source_token, project_name, data).json())

        return created_projects

    def generate_user_projects(self, created_users, dry_run=True):
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
        for i, _ in enumerate(created_users):
            user = created_users[i]
            self.log.info(f"{dry_run}Creating user project ({user})")
            if not dry_run:
                token = self.users.find_or_create_impersonation_token(
                    user, users_map, expiration_date)
                for project_data in dummy_project_data:
                    if token and token.get("token") is not None:
                        created_projects.append(self.projects.projects_api.create_project(
                            self.config.source_host, token['token'], project_data["name"], data=project_data).json())
                    else:
                        project_data["namespace"] = user["username"]
                        self.projects.projects_api.create_project(
                            self.config.source_host, self.config.source_token, project_data["name"], data=project_data).json()

        return created_projects

    def generate_dummy_branches(self, pid, dry_run=True):
        for d in self.BRANCH_DATA:
            self.log.info(
                f"{get_dry_log(dry_run)}Creating project {pid} branch ({d})")
            if not dry_run:
                self.projects_api.create_branch(
                    self.config.source_host, self.config.source_token, pid, data=d)

    def generate_dummy_environment(self, pid, dry_run=True):
        data = {
            "name": "production",
            "external_url": "http://production-%s.site" % uuid4()
        }
        self.log.info(
            "{0}Creating project {1} environment ({2})".format(get_dry_log(dry_run), pid, data))
        if not dry_run:
            return self.projects.projects_api.create_environment(
                self.config.source_host, self.config.source_token, pid, data)

    def generate_dummy_project_hooks(self, pid, dry_run=True):
        for d in self.HOOKS_DATA:
            self.log.info(
                f"{get_dry_log(dry_run)}Creating project {pid} hook ({d})")
            if not dry_run:
                self.projects_api.add_project_hook(
                    self.config.source_host, self.config.source_token, pid, d)

    def generate_dummy_project_clusters(self, pid, dry_run=True):
        for d in self.CLUSTERS_DATA:
            self.log.info(
                f"{get_dry_log(dry_run)}Creating project {pid} cluster ({d})")
            if not dry_run:
                self.projects_api.add_project_cluster(
                    pid, self.config.source_host, self.config.source_token, d)

    def generate_dummy_project_variables(self, pid, dry_run=True):
        for d in self.VARIABLES_DATA:
            self.log.info(
                f"{get_dry_log(dry_run)}Creating project {pid} variable ({d})")
            if not dry_run:
                self.projects_api.create_project_variable(
                    pid, self.config.source_host, self.config.source_token, d)

    def generate_dummy_project_push_rules(self, pid, dry_run=True):
        data = [
            {
                "commit_message_regex": "",
                "commit_message_negative_regex": "",
                "branch_name_regex": "",
                "deny_delete_tag": True,
                "member_check": True,
                "prevent_secrets": True,
                "author_email_regex": "",
                "file_name_regex": "testingfile",
                "max_file_size": 1000000,
                "commit_committer_check": True,
                "reject_unsigned_commits": None
            }
        ]

        self.log.info("{0}Creating project {1} push rules ({2})".format(
            get_dry_log(dry_run), pid, data))
        self.projects_api.create_project_push_rule(
            pid, self.config.source_host, self.config.source_token, data)

    def generate_dummy_group_variables(self, gid, dry_run=True):
        for d in self.VARIABLES_DATA:
            self.log.info(
                f"{get_dry_log(dry_run)}Creating group {gid} variable ({d})")
            if not dry_run:
                self.groups_api.create_group_variable(
                    gid, self.config.source_host, self.config.source_token, d)

    def generate_dummy_group_hooks(self, gid, dry_run=True):
        for d in self.HOOKS_DATA:
            self.log.info(
                f"{get_dry_log(dry_run)}Creating group {gid} hook ({d})")
            if not dry_run:
                self.groups_api.add_group_hook(
                    self.config.source_host, self.config.source_token, gid, d)

    def generate_dummy_group_clusters(self, gid, dry_run=True):
        for d in self.CLUSTERS_DATA:
            self.log.info(
                f"{get_dry_log(dry_run)}Creating group {gid} cluster ({d})")
            if not dry_run:
                self.groups_api.add_group_cluster(
                    gid, self.config.source_host, self.config.source_token, d)

    def generate_shared_with_group_data(self, pid, groups, dry_run):
        for group in groups:
            data = {
                "group_access": 30,
                "group_id": group["id"],
                "expires_at": None
            }
            self.log.info(
                "{0}Sharing project {1} with group:\n{2}".format(get_dry_log(dry_run), pid, data))
            if not dry_run:
                self.projects_api.add_shared_group(
                    self.config.source_host, self.config.source_token, pid, data)

    def generate_dummy_user_keys(self, uid, dry_run=True):
        ssh_data = [
            {
                "title": "test_ssh_key_1",
                "key": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDg4xhni5/yedcCRfemTFdK5SgjvZtnDb3YtLNssXg+BAkdPiK9VRrtSRffG4n80HeorRv1bS0ppl3DuILvpuLaI0cXarDqAsxp/+SQGq+5aVOM+A7/lfoGWmBz68KjlxkAs6F2vS9P04DCXN0wvk4Egz1ywzZvPaB7pFQSPo7ZlyMl0BgKW9BFNQ8zRen0MwCqfiH04R6VB1Vcj3YcTPIcLoaN+OhrDRyDpvVFj3HnYnEgew318EHWJEl6I0TDkmHarjj3MvwR3f5j6KqJLwbbOHVbXSF94YCfEz3ZcVhxtcXXHS1Adp2Mra+s1UtQJtNcas16Xwtxlu2AB4m17G+qB2jO8J6DuwzvAlYseAt5gS1XVrfv6a6yqRV1yp+WfVEOIzW9CpJpGVEsORaOSVKeoa2MCfElBmi4yBcXclC2vitY8aBP8R9wblsG9MALRXFydgfLNle2jveO/YAlzG7I4Or9EzMRdVwPO551t9zoIYBSi/hW0DXj47eH03DMZxM= petarprokic@Petar-MBP.local",
                "expires_at": "6666-06-06T00:00:00.000Z"
            },
            {
                "title": "test_ssh_key_2",
                "key": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQCnNg7lEKsUynd3cARWAgSkMh9OqlggfVi7lnpUFDVtiGaOleABExMPEbeOJ8M4wXyFi1ptcYLQwO0zEh6y4ksJqHrz6jbJeeI76HEebfURNSxxF73Po21KGDZIBu5XT3yOzskimK4B/dxgx7RGuC6D5yg4VnGsSzxw0pWt5yEDEa5P1Y9UrcYuRmxTlKzdDLfQcD0VyIFRMnGdwMALBhw7uY045IeMGQziics+HfyNjLCEWkKEfVch74deXpYxGijMFwCMERVQS+E/jgAWc0ruQtoeDWCpwZRNvUiig9Q5ZryrSuh0ive/Iwl3qHfqNTSN6jzNSlvjgger/iypfUqQZwceqhY8LXjriRvqTPOu3eWlMAW+TZ0ubz/wQUdr9O6aHnTThudi7Vdyi2MVPNJRUKG3rXSsUYCzQ6Pr0eNTGys1N64kElqgoeBH6g2jcgzB/xnY3UXlBO4BrHA/COuGXHJCTM8cjJInGLXrCMrOmIMcjb59b5kACmPog4VpG3E= petarprokic@Petar-MBP.local",
                "expires_at": "5555-05-05T00:00:00.000Z"
            }
        ]
        gpg_data = [
            {
                "key": "-----BEGIN PGP PUBLIC KEY BLOCK-----\r\n\r\nmQENBF7P1IMBCAC0k/J3bxmRU9d/nEgDF8KqOVbBV04YtNVYJjWZbAoXCFT9An/J\r\n5828xa5MvSlqJDG8M7KY1zjmvShkBNRGyqWJgpNzC8g0AIHMzD/w3BjkRo7s8CSj\r\n7JpmN96/y3QsuKvNV2aecVE8if58Dqv71J53re9bP/LDjSYuqYWnKTFJp18DDaHc\r\nPaSZqCexPTLfa8VnRL1PiXvNWfp+yNcwnD+7r1GrZIyHLRp/xoWLHA/1aF2rcNJ/\r\nXiuBn+YrZEpr8Xlm/TpDEgvrJgOkWr3+6Fwm25VJjfTFOVglCDqYFxoD/t5gHyWh\r\nImTcRgJl79MQsNY5BfUBQbN5X96UM8dOWmVrABEBAAG0GHRlc3Q0IDx0ZXN0NEBn\r\naXRsYWIuY29tPokBVAQTAQgAPhYhBAAbmx3VMrUyI0UkmQ8Fpb3bS3luBQJez9SD\r\nAhsDBQkDwmcABQsJCAcCBhUKCQgLAgQWAgMBAh4BAheAAAoJEA8Fpb3bS3lukiAH\r\n+weqosN9YMHPLp/pPqKisyjWVxVEcB6I8ni7sNYNYQORJuO6sehQolsHEeVZ8RCX\r\nsMo8+Y9CA7TbB7q5svyTbZ0cITEVaxsYwg/1avWBB1m9uCDBm+oLN+4Y/U1ZPLek\r\ndMkZ8AMAGqHuX5wtWtwVUdoxDyirMzXegvYQxRnQKGCXyzLkN3f/BnEwIcOwB253\r\nQOb/N7cDeUZAssZSmTyvG+QKUYa6et88znDno2ybWBc9E5RBOw8QHj8xvzjFDgAv\r\n7VpcGFo+nmFj47fcC6sj2ivxfl/iaT4IfxMsIvKjjcIg1+8Y9jJOnX+aQJC3OCyI\r\nf1XNhQaEq+7GaOBoZLW1FNy5AQ0EXs/UgwEIAL4lZXfJI36G4OxU00Yv0PXDxy6m\r\nF6gOb8BG4TQ1zj5Pk4ZSK6fNNUW8aVwkeoG9EFI27RzstENQVz0QRAT3rj+v7/9y\r\nGOHTb9K09d00lPxXRQyiVkqldG3885MWgKl3MTL7Uj3aF2YZ701wiWC36L5cwnoK\r\nsaXOWlRmmRvT2X8YCPL+tWS6D/57eibONM+dzBDPjZcKfGxF5h+m8AVDr9gyIV/O\r\nCBHO00qIGX8decfEUGSy+n26cY/FE/DYJ6wgO/1Wy6L0hBTQA3mlrmzZm7atzoaR\r\njUc5Y1Teq+RO6PoZx0Q4M5nblENSFV8j/7Txf/8+oCyepvvULVz0j55MeCMAEQEA\r\nAYkBPAQYAQgAJhYhBAAbmx3VMrUyI0UkmQ8Fpb3bS3luBQJez9SDAhsMBQkDwmcA\r\nAAoJEA8Fpb3bS3lu5esIAKkOXRfHpFLXzHuJoAo3papFRBCrNjJqNBwgKpbwSrXW\r\nQI6fSVeSL7mWmGp5Tvl5XA7mvUMiOnMTG810yUkkANf8dQjgkaawf+vATxzynZdr\r\nSUMiBGAU1IUvTb4ckiCWQimSKuemza9Y4Om/dBWuktzwOdsPuzBXIRLK5qBH3zQT\r\newZQ/muig+9mI7A3f8Rr5pzhNvP14wCgMDaSAI3g05S2zQINWsPxbYarrb41V2CC\r\n9ZQAjG5vkkA1ksooP5BV7WmrUZylrxmg110aJcdOkzIPnWyfdXzcBL8IjIVYlYDW\r\nICB9n45nweWn0ypjqEVK6mkPPRpX2L++NZDJhGV3Dw4=\r\n=IS+Y\r\n-----END PGP PUBLIC KEY BLOCK-----"
            },
            {
                "key": "-----BEGIN PGP PUBLIC KEY BLOCK-----\r\n\r\nmQENBF7P1SwBCACiKPkwiWATNRnAQqiyF0HX9ITqFV3iRwEZ3hc2QHHSCoijybpI\r\n6xIRJwlsSYXelFj7rt1zVra/yqze6rfCgudBj5rMf5DtmWgcj83lgSMsW6GJHsxH\r\nSvkqyODuOhFjzoJXml8Ts3ThzW5QdasfnDjOfXKO1DSVgACkKlcozjHTjv2/g0up\r\n1/7YNMzvWFhiOBIp2+2+5NLFZhD5x2py+QL32dSvYjuS0gQxJKYJaVoSAPYrHIji\r\n+shC+0QjSk8lKUF9zx/ylpVVnUFkqwrIqEp0TaN5cvGLQTphX6jFT/sUNR9un8g5\r\nxA11TvqG2qR0etxtWOmulaGM7/KcY7BMHqP9ABEBAAG0GHRlc3Q0IDx0ZXN0NEBn\r\naXRsYWIuY29tPokBVAQTAQgAPhYhBGDRW7TfZpb6AVVCbaaScvAIYq4qBQJez9Us\r\nAhsDBQkDwmcABQsJCAcCBhUKCQgLAgQWAgMBAh4BAheAAAoJEKaScvAIYq4qoQAH\r\n/01cLElZmZyQEdUBnJ7E3ImVvdsYV9I65gUs0fCKgY1LYqHi3TNWCsM4WomA5gfp\r\nrIWd9JrpOjEv+8H7JrmZj6RPn7WjgLJtWXdqeFIdyN6Jvy+Qy1QvrZ94YsCwhLp4\r\nDb/EAIcPsWDjOYpbRHrWQ8WScRdPP8xiaJR7ZdC/G8xI9he/5cKjPjNiFThpzDlO\r\n539gOaAqIfI+KNFzaBHm1AeU2eaUZeh2FZ1446a4x083WKH9LW34GwBMXHmPhQ/L\r\ndjPgB+3UwslK0ZL7pZjOcZCMmo9WywYnTsWoGz1o7DV/OFRWeJgagBGlJH8L2u4q\r\nDbuR9Rf3GGPMRu/lMJ02gj25AQ0EXs/VLAEIAMvJCrnF2jedQ9rlO/D9R8U0MQTq\r\nBS79PXLzzBw1ux9Rial62SOK87k+b9cY3FHVUumv0M63wZXzLcdWHNDFBku3egIk\r\nOobYkEC/TyhLyordAsUVKf96KVZ1H8h7yhUCv3tlZ3Nw07FTattdYAD2ps52USZN\r\nxwqlWeBeFu6bZdf9ZupCKwJvz/WvjAN++AuHAziqdvM8LkdMhgq3Zr2jT07LypcH\r\nBOWhL1vRU45VETcWTrkDqACbnrwg3rcZZXFpvdeKXly4eCBXvtX3sjOZyiZZR9mh\r\n5JNmmNwX2cw2sWOEPL3oqIks+aGrkBa0hCa9r51NvHp/3gmIBHPlp0ErmjUAEQEA\r\nAYkBPAQYAQgAJhYhBGDRW7TfZpb6AVVCbaaScvAIYq4qBQJez9UsAhsMBQkDwmcA\r\nAAoJEKaScvAIYq4qWWYH/1Px/XbnQaeNmGFK810ToKYSdrbZYaGifT/QHQDRdHJf\r\nXm4jjcYh1diB5vzUsug7OkehZLT+HsEq3qLeiY+yzvMumdgHzh3KvFiATPRg7ILr\r\njFnlBKpK3cpaJFj9V3tGVankCf31/09cK4qWIQB1APISVFhcp3//4iVyasF4nH5v\r\nApeNMZgAbgffExQLrqw4/omDzAPiuctW9qPvWkQRzX+CwH0J/SmGeWueskLv3Fgp\r\nHjVy8ZT63VtZqjtR0MTyO5GI4QMO3xiekQHkAeOu6aVpKWHrmyKcX5C7nFj0vVTo\r\nwCnE6vhr7tKo/E3YqNxeMZjWeNY+x4lPA2AVLRM1u8k=\r\n=Xnn0\r\n-----END PGP PUBLIC KEY BLOCK-----"
            }
        ]
        for s in ssh_data:
            self.log.info(
                "{0}Creating user {1} SSH key ({2})".format(get_dry_log(dry_run), uid, s))
            if not dry_run:
                self.users_api.create_user_ssh_key(
                    self.config.source_host, self.config.source_token, uid, s)
        for g in gpg_data:
            self.log.info(
                "{0}Creating user {1} GPG key ({2})".format(get_dry_log(dry_run), uid, g))
            self.users_api.create_user_gpg_key(
                self.config.source_host, self.config.source_token, uid, g)

    def generate_dummy_project_deploy_keys(self, pid, dry_run=True):
        keys = [
            {
                "title": "test_deploy_key_1",
                "key": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDfZiGd1bXM35/lwUBBCd5HmIaR5oUN+N0eEzyiXiSP7/N/GCI1JeW1I9j2Ugz2ek7nP0QJroD/aNjnVv4evmZfA87fHJejAPmKlgzS34hwPh+vSh0TNxwwMzTdZdWK8OEAMZ9nwpIDrN4E3ly3lw4sqgs0fqvm3mdJOA8wl6p/w4bHv/HZeAwl4M7idFdV3c4UAiAKwWSzyPfuPSYkF/TAloUv28YbjL4pNSNUzX5S2rwyZakPUwQi/5TZB8S8fL8aDwhvvFVLO6Fkd51EOy2MWHuKRjppD63M7kQ3JopeqT8r7P7B9nuG6/Tv6GFda132VH7CU2vDExe7+4dGjV3eFmI6kgYs6+PXc4y58OKr7ey6g+jVwE+BqlueXiqQtsrhhSbSd3IQzlDvN7+PptQLF/tbJCmnNtnFlh/cek9Kvei0R2ym9oQNsaz+lYtniLHwlguv43ZJQtXhDSm+htL45K25Q/56tRr/05XAcA1hNkswFO0n9vC3KXqkpFvKrx8= petarprokic@Petar-MBP.local"
            },
            {
                "title": "test_deploy_key_2",
                "key": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDQ249uJUE+AsmbrfsKKmGe5NOdaOa1DAwv7GOaoMIC3KqcyCr7/Ud3aAcjxVXTXa30jAPk8P2IOqiQe2XVeR89UUuIeRembYpV+xdHoqrLqHX8OsnCeZroddb2M3XZYSPaV+Yq14CUuBqeucB3iBZO/C3oDRRKgBZUig3Ef0Vdv5nL8zqCCEoKDsEZTuYbvoqMjdrbUb5XYOU2RONvU84qP73JFvCXgbdaskg6yP7uVt7c6Iq/ShrrKq3J1ORYVutfH6PWiE26VB3i3K0UDquEfFJ6lHFM3ZNKp8E/HJ35pMG5nRYQkN3TDrh6q7O7YrUAFdmYdpCFEPekiMAaLgetsQp2NiP9UPlydQIBMBiKxyRnGirIunP1YRKL9c0y7JhAphMaxkrW31t3pPCPvUgvouMma+BhkzaokNHfR/i9qsaVLbyGgSOAJiSW2b0GegmT+xdObjmbheRErnoFohGsB+UFfWpONVK5dZaJLWhDeW9aNRqTnV4kXh4tCj03qiM= petarprokic@Petar-MBP.local"
            }
        ]
        for k in keys:
            self.log.info(f"{dry_run}Creating project {pid} deploy key ({k})")
            if not dry_run:
                self.projects_api.create_new_project_deploy_key(
                    pid, self.config.source_host, self.config.source_token, k)

    def enable_importers(self):
        settings = {
            'import_sources': [
                'github',
                'bitbucket_server',
                'git',
                'gitlab_project'
            ]
        }
        self.settings_api.set_application_settings(self.config.destination_host, self.config.destination_token, settings)
