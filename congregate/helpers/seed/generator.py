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

from datetime import timedelta, date
import json

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
            "skip_confirmation": True
        }
    ]
    created_users = []
    for user in dummy_users:
        user_search = list(users.search_for_user_by_email(b.config.source_host, b.config.source_token, user["email"]))
        if user_search[0]["email"] == user["email"]:
            b.log.info("%s already exists" % user["name"])
            created_users.append(user_search[0])
        else:
            b.log.info("Creating %s" % user["name"])
            created_users.append(users.create_user(b.config.source_host, b.config.source_token, user).json())

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
        group_search = list(groups.search_for_group(group["path"], b.config.source_host, b.config.source_token))
        if group_search[0]["path"] == group["path"]:
            b.log.info("%s already exists" % group["name"])
            created_groups.append(group_search[0])
        else:
            b.log.info("Creating %s" % group["name"])
            created_groups.append(groups.create_group(b.config.source_host, b.config.source_token, group).json())
    
    return created_groups

def add_group_members(created_users, created_groups):
    for user in created_users:
        print user
        data = {
            "user_id": user["id"],
            "access_level": 40
        }
        print created_groups[-1]
        groups.add_member_to_group(created_groups[-1]["id"], b.config.source_host, b.config.source_token, data)
        
def generate_group_projects(created_groups):
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
        created_projects.append(projects.create_project(b.config.source_host, b.config.source_token, project_name, data).json())

    return created_projects

def generate_user_projects(created_users):
    dummy_project_data = [
        {
            "name":"my-project",
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
    expiration_date = (date.today() + timedelta(days=1)).strftime('%Y-%m-%d')
    for i in range(0, len(created_users)):
        user = created_users[i]
        token = users.find_or_create_impersonation_token(b.config.source_host, b.config.source_token, user, users_map, expiration_date)["token"]
        created_projects.append(projects.create_project(b.config.source_host, token, dummy_project_data[i]["name"], data=dummy_project_data[i]).json())

    return created_projects

def generate_seed_data():
    users = generate_users()
    groups = generate_groups()
    add_group_members(users, groups)
    projects = generate_group_projects(groups)
    projects += generate_user_projects(users)

    print "---Generated Users---"
    print json.dumps(users, indent=4)
    print "---Generated Groups---"
    print json.dumps(groups, indent=4)
    print "---Generated Projects---"
    print json.dumps(projects, indent=4)

