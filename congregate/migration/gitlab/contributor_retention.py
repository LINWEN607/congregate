import json
from gitlab_ps_utils.dict_utils import dig
from gitlab_ps_utils.api import GitLabApi
from gitlab_ps_utils.misc_utils import safe_json_response
from congregate.helpers.base_class import BaseClass
from congregate.migration.gitlab.users import UsersClient
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.api.issues import IssuesApi
from congregate.migration.gitlab.api.merge_requests import MergeRequestsApi
from congregate.migration.meta.api_models.new_member import NewMember
from congregate.helpers.migrate_utils import find_user_by_email_comparison_without_id

class ContributorRetentionClient(BaseClass):
    GROUP_ELEMENTS = ['epics']
    PROJECT_ELEMENTS = ['issues', 'mergeRequests', 'snippets']

    def __init__(self, id, full_path, asset_type='project'):
        super().__init__()
        self.api = GitLabApi()
        self.users = UsersClient()
        self.projects = ProjectsApi()
        self.groups = GroupsApi()
        self.issues = IssuesApi()
        self.mr = MergeRequestsApi()
        self.id = id
        self.full_path = full_path
        self.members = self.get_members(asset_type)
        self.contributor_map = {}

    def build_map(self):
        for element in self.PROJECT_ELEMENTS:
            self.retrieve_contributors(element)
    
    def retrieve_contributors(self, element):
        hasNextPage = True
        cursor = ""
        while hasNextPage:
            query = self.generate_contributors_query(element, cursor)
            if data := safe_json_response(
                self.api.generate_post_request(self.config.source_host, self.config.source_token, None, json.dumps(query), graphql_query=True)):
                print(f"Retrieved {len(dig(data, 'data', 'project', element, 'nodes', default=[]))} {element}")
                for node in dig(data, 'data', 'project', element, 'nodes', default=[]):
                    author = dig(node, 'author')
                    self.add_contributor_to_map(author)
                    for commenter in dig(node, 'commenters', 'nodes', default=[]):
                        self.add_contributor_to_map(commenter)
                cursor = dig(data, 'data', 'project', element, 'pageInfo', 'endCursor')
                hasNextPage = dig(data, 'data', 'project', element,'pageInfo', 'hasNextPage', default=False)
            else:
                print("Request failed")

    def add_contributor_to_map(self, author):
        if author:
            author_email = author.get('username')
        # if not author:
        #     author_email = element.get('author_email')
        # If the author is not already a project member
        if author not in self.members:
            # Add the element/element note author to the contributor map
            # author_email = self.users.users_api.get_user_email(author['id'], self.config.source_host, self.config.source_token)
            # author['email'] = author_email
            self.contributor_map[author_email] = author

    def add_contributors_to_project(self, contributors, pid, host, token):
        '''
            Add contributors from contributor map to source project
        '''
        for contributor in contributors.items():
            new_member_payload = NewMember(user_id=contributor['id'], access_level=10)
            self.projects.add_member(pid, host, token, new_member_payload.to_dict())
    
    def add_contributors_to_group(self, contributors, pid, host, token):
        '''
            Add contributors from contributor map to source group
        '''
        for contributor in contributors.items():
            new_member_payload = NewMember(user_id=contributor['id'], access_level=10)
            self.groups.add_member_to_group(pid, host, token, new_member_payload.to_dict())

    def remove_contributors_from_project(self):
        '''
            Remove all contributors who were not originally members from the project
        '''
        for contributor in self.contributor_map.items():
            dest_user = find_user_by_email_comparison_without_id(contributor.get('email'))
            self.projects.remove_member(self.id, dest_user['id'], self.config.destination_host, self.config.destination_token)
    
    def get_members(self, asset_type):
        if asset_type == 'project':
            return self.projects.get_members(self.id, self.config.source_host, self.config.source_token)
        elif asset_type == 'group':
            return self.groups.get_all_group_members(self.id, self.config.source_host, self.config.source_token)
        
    def generate_contributors_query(self, element, cursor):
        return {
                "query": """
                    query {
                        project(fullPath: "%s"){
                        %s(after: "%s") {
                            nodes {
                                author{
                                    id
                                    username
                                },
                                commenters {
                                    nodes {
                                        id
                                        username
                                    }
                                }
                            }
                            pageInfo {
                                endCursor,
                                hasNextPage
                            }
                        }
                        }
                    }
                """ % (self.full_path, element, cursor)
            }

    