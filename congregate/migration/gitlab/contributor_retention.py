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
    PROJECT_ELEMENTS = ['commits', 'issues', 'merge_requests', 'snippets']
    NOTES_FIELDS = ['user_notes_count', 'notes']

    def __init__(self, host, token, id, asset_type='project'):
        self.users = UsersClient()
        self.projects = ProjectsApi()
        self.groups = GroupsApi()
        self.issues = IssuesApi()
        self.mr = MergeRequestsApi()
        self.host = host
        self.token = token
        self.id = id
        self.members = self.get_members(asset_type)
        self.contributor_map = {}
        self.project_elements = {
            'commits': {
                'list_function': self.projects.get_project_repository_commits,
                'notes_function': self.projects.get_project_repository_commit_comments
            },
            'issues': {
                'list_function': self.issues.get_all_project_issues,
                'notes_function': self.issues.get_all_project_issue_notes
            },
            'merge_requests': {
                'list_function': self.mr.get_all_project_merge_requests,
                'notes_function': self.mr.get_merge_request_notes
            },
            'snippets': {
                'list_function': self.projects.get_all_project_snippets,
                'notes_function': self.projects.get_project_snippet_notes
            }
        }
        super().__init__()

    def build_map(self):
        for element, functions in self.project_elements.items():
            self.log.info(f"Retrieving contributors in {element}")
            self.retrieve_contributors(functions['list_function'], functions['notes_function'])

    def retrieve_contributors(self, project_element_list, project_element_notes):
        '''
            Retrieves contributors from a specific element of a project (see elements list above)
        '''
        # iterate over results from a listing API endpoint
        for el in project_element_list(self.id, self.host, self.token):
            # if the element has notes
            # pass in the element endpoint with '/notes' appended to it
            # match = [el.get(field) for field in self.NOTES_FIELDS if el.get(field) is not None]
            # if match:
            #     self.retrieve_contributors(project_element_notes, None)
            
            # Grab author metadata from response
            author = el.get('author')
            if not author:
                author_email = el.get('author_email')
            # If the author is not already a project member
            if author not in self.members:
                # Add the element/element note author to the contributor map
                author_email = self.users.users_api.get_user_email(author['id'], self.config.source_host, self.config.source_token)
                author['email'] = author_email
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
        

    