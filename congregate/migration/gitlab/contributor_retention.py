from congregate.helpers.base_class import BaseClass
from congregate.migration.gitlab.api.users import UsersApi
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.api.issues import IssuesApi
from congregate.migration.gitlab.api.merge_requests import MergeRequestsApi
from congregate.helpers.migrate_utils import find_user_by_email_comparison_without_id

class ContributorRetentionClient(BaseClass):
    GROUP_ELEMENTS = ['epics']
    PROJECT_ELEMENTS = ['commits', 'issues', 'merge_requests', 'snippets']
    NOTES_FIELDS = ['user_notes_count', 'notes']

    def __init__(self, host, token, asset_type='project'):
        self.users = UsersApi()
        self.projects = ProjectsApi()
        self.groups = GroupsApi()
        super().__init__()
        self.host = host
        self.token = token
        self.contributor_map = {}
        self.members = self.get_members(asset_type)

    def retrieve_contributors(self, project_element_list, project_element_notes):
        '''
            Retrieves contributors from a specific element of a project (see elements list above)
        '''
        # iterate over results from a listing API endpoint
        for el in project_element_list():
            # if the element has notes
            # pass in the element endpoint with '/notes' appended to it
            match = [el.get(field) for field in self.NOTES_FIELDS if el.get(field) is not None]
            if match:
                self.retrieve_contributors(project_element_notes)
            
            # Grab author metadata from response
            author = el.get('author')
            # If the author is not already a project member
            if author not in self.members:
                # Add the element/element note author to the contributor map
                author_email = self.users.get_user_email(author['id'], self.config.source_host, self.config.source_token)
                author['email'] = author_email
                self.contributor_map[author_email] = author

    def add_contributors_to_project(self, contributors, pid, host, token):
        '''
            Add contributors from contributor map to project
        '''
        for contributor in contributors.items():
            self.projects.add_member(pid, host, token, contributor)

    def remove_contributors_from_project(self):
        '''
            Remove all contributors who were not originally members from the project
        '''
        for contributor in self.contributor_map.items():
            dest_user = find_user_by_email_comparison_without_id(contributor.get('email'))
            self.projects.remove_member(dest_user['id'], self.config.destination_host, self.config.destination_token)
    
    def get_members(self, asset_type, id):
        if asset_type == 'project':
            return self.projects.get_members(id, self.config.source_host, self.config.source_token)
        elif asset_type == 'group':
            return self.groups.get_all_group_members(id, self.config.source_host, self.config.source_token)
        

    