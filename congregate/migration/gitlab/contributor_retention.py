import json
from gitlab_ps_utils.dict_utils import dig, rewrite_list_into_dict
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

    def __init__(self, src_id, dest_id, full_path, asset_type='project', dry_run=True):
        super().__init__()
        self.api = GitLabApi()
        self.users = UsersClient()
        self.projects = ProjectsApi()
        self.groups = GroupsApi()
        self.src_id = src_id
        self.dest_id = dest_id
        self.full_path = full_path
        self.members = self.get_members(asset_type)
        self.contributor_map = {}
        self.dry_run = dry_run

    def build_map(self):
        for element in self.PROJECT_ELEMENTS:
            self.retrieve_contributors(element)
    
    def retrieve_contributors(self, element):
        hasNextPage = True
        cursor = ""
        count = 0
        while hasNextPage:
            query = self.generate_contributors_query(element, cursor)
            if data := safe_json_response(
                self.api.generate_post_request(self.config.source_host, self.config.source_token, None, json.dumps(query), graphql_query=True)):
                count += len(dig(data, 'data', 'project', element, 'nodes', default=[]))
                self.log.info(f"Retrieved {count} {element}")
                for node in dig(data, 'data', 'project', element, 'nodes', default=[]):
                    author = dig(node, 'author')
                    self.add_contributor_to_map(author)
                    for commenter in dig(node, 'commenters', 'nodes', default=[]):
                        self.add_contributor_to_map(commenter)
                cursor = dig(data, 'data', 'project', element, 'pageInfo', 'endCursor')
                hasNextPage = dig(data, 'data', 'project', element,'pageInfo', 'hasNextPage', default=False)
            else:
                self.log.error("Request failed")

    def add_contributor_to_map(self, author):
        # If the author is not already a project member
        if author['username'] not in self.members:
            # extracting ID from GQL string 'gid://gitlab/user/<id>'
            author['id'] = author['id'].split("/")[-1]
            # Add the element/element note author to the contributor map
            if author.get('publicEmail'):
                author_email = author['publicEmail']
            else:
                author_email = self.users.users_api.get_user_email(author['id'], self.config.source_host, self.config.source_token)
            author['email'] = author_email
            self.contributor_map[author_email] = author

    def add_contributors_to_project(self):
        '''
            Add contributors from contributor map to source project
        '''
        for contributor, data in self.contributor_map.items():
            new_member_payload = NewMember(user_id=data['id'], access_level=10)
            if self.dry_run:
                self.log.info(f"DRY_RUN: Adding contributor {contributor} to project {self.full_path}")
            else:
                self.log.info(f"Adding contributor {contributor} to project {self.full_path}")
                self.projects.add_member(self.src_id, self.config.source_host, self.config.source_token, new_member_payload.to_dict())
    
    def add_contributors_to_group(self):
        '''
            Add contributors from contributor map to source group
        '''
        for contributor in self.contributor_map.items():
            new_member_payload = NewMember(user_id=contributor['id'], access_level=10)
            self.groups.add_member_to_group(self.src_id, self.config.source_host, self.config.source_token, new_member_payload.to_dict())

    def remove_contributors_from_project(self, source=False):
        '''
            Remove all contributors who were not originally members from the project
        '''
        if source:
            host = self.config.source_host
            token = self.config.source_token
            pid = self.src_id
        else:
            host = self.config.destination_host
            token = self.config.destination_token
            pid = self.dest_id
        for contributor, data in self.contributor_map.items():
            if source:
                user = data
            else:
                user = find_user_by_email_comparison_without_id(data.get('email'))
            if self.dry_run:
                self.log.info(f"DRY_RUN: Removing contributor {contributor} from project {self.full_path}")
            else:
                self.log.info(f"Removing contributor {contributor} from project {self.full_path}")
                self.projects.remove_member(pid, user['id'], host, token)
    
    def get_members(self, asset_type):
        if asset_type == 'project':
            return rewrite_list_into_dict(list(self.projects.get_members(self.src_id, self.config.source_host, self.config.source_token)), "email")
        elif asset_type == 'group':
            return rewrite_list_into_dict(list(self.groups.get_all_group_members(self.src_id, self.config.source_host, self.config.source_token)), "email")
        
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
                                    publicEmail
                                },
                                commenters {
                                    nodes {
                                        id
                                        username
                                        publicEmail
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

    