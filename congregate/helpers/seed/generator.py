from congregate.helpers import base_module as b
from congregate.migration.gitlab.importexport import ImportExportClient
from congregate.migration.gitlab.variables import VariablesClient
from congregate.migration.gitlab.users import UsersClient
from congregate.migration.gitlab.groups import GroupsClient
from congregate.migration.gitlab.projects import ProjectsClient
from congregate.migration.gitlab.pushrules import PushRulesClient
from congregate.migration.gitlab.branches import BranchesClient
from congregate.migration.gitlab.merge_request_approvers import MergeRequestApproversClient
from congregate.migration.gitlab.awards import AwardsClient
from congregate.migration.gitlab.registries import RegistryClient
from congregate.migration.gitlab.pipeline_schedules import PipelineSchedulesClient
from congregate.migration.mirror import MirrorClient
from congregate.migration.gitlab.deploy_keys import DeployKeysClient

ie = ImportExportClient()
mirror = MirrorClient()
variables = VariablesClient()
users = UsersClient()
groups = GroupsClient()
projects = ProjectsClient()
pushrules = PushRulesClient()
branches = BranchesClient()
awards = AwardsClient()
mr = MergeRequestApproversClient()
registries = RegistryClient()
schedules = PipelineSchedulesClient()
deploy_keys = DeployKeysClient()

def generate_users():
    dummy_users = [
        {
            "username": "john_smith",
            "email": "john@example.com",
            "name": "John Smith"
        },
        {
            "username": "jack_smith",
            "email": "jack@example.com",
            "name": "Jack Smith"
        },
        {
            "username": "jane_doe",
            "email": "jane@example.com",
            "name": "Jane Doe"
        }
    ]
    created_users = []
    for user in dummy_users:
        b.log.info("Creating %s" % user["name"])
        created_users.append(users.create_user(b.config.source_host, b.config.source_token, user))

    return created_users

def generate_groups():
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
        b.log.info("Creating %s" % group["name"])
        created_groups.append(groups.create_group(b.config.source_host, b.config.source_token, group))
    
    return created_groups

def add_group_members(created_users, created_groups):
    for user in created_users:
        data = {
            "user_id": user["id"],
            "access_level": 40
        }
        groups.add_member_to_group(created_groups[-1], b.config.source_host, b.config.source_token, data)
        
def generate_projects(created_users, created_groups):
    dummy_projects = {
        "spring": "git@gitlab.com:gitlab-org/project-templates/spring.git",
        "react": "git@gitlab.com:gitlab-org/project-templates/react.git",
        "android": "git@gitlab.com:gitlab-org/project-templates/android.git"
    }

    created_projects = []
    
    return created_projects


def generate_seed_data():
    users = generate_users()
    groups = generate_groups()
    add_group_members(users, groups)
    projects = generate_projects(users, groups)
