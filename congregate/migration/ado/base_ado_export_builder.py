from copy import deepcopy as copy
from gitlab_ps_utils.dict_utils import dig
from gitlab_ps_utils.misc_utils import safe_json_response
from congregate.helpers.base_class import BaseClass
from congregate.migration.ado.api.pull_requests import PullRequestsApi


class BaseAdoExportBuilder(BaseClass):
    """
    Base class for ADO export builders containing shared functionality.
    
    This class provides common methods used by both project and group export builders
    to avoid code duplication.
    """
    
    def __init__(self):
        super().__init__()
        self.members_map = {}
        self.pull_requests_api = PullRequestsApi()
    
    def add_to_members_map(self, member):
        """Add a member to the members map with a new ID."""
        member_copy = copy(member)
        guid = member.get('descriptor', member.get('id'))
        member_copy['id'] = len(self.members_map.keys()) + 1
        self.members_map[guid] = member_copy

    def get_new_member_id(self, member):
        """Get or create a new member ID for the given member."""
        if not member:
            return None
        if mid := dig(self.members_map, member.get('descriptor'), 'id', default=dig(self.members_map, member['id'], 'id')):
            return mid
        self.add_to_members_map(member)
        return self.get_new_member_id(member)

    def get_merged_by_user(self, pr, project_id, repository_id):
        """Get the user who merged the pull request."""
        request = self.pull_requests_api.get_pull_request(project_id, repository_id, pr['pullRequestId'])
        return self.get_new_member_id(safe_json_response(request).get('closedBy'))

    def work_item_type_color(self, work_item_type):
        """Get the color for a work item type."""
        color_map = {
            'Epic':                 '#FF7F27',  # Orange
            'Feature':              '#B062FF',  # Purple
            'User Story':           '#00A2E8',  # Blue
            'Product Backlog Item': '#4BAF4F',  # Green
            'Requirement':          '#00A2E8',  # Blue
            'Bug':                  '#FF6666',  # Red
            'Task':                 '#FFF200',  # Yellow
            'Impediment':           '#BCD276',  # Light Green
            'Issue':                '#BCD276',  # Light Green
        }
        return color_map.get(work_item_type, '#CCCCCC')

    def label_links(self, workitem):
        """Generate label links for a work item."""
        label_links = []
        for label in workitem.get('fields', {}).get('System.Tags', '').split('; '):
            if label:
                label_links.append({
                    "target_type": "Issue",
                    "created_at": workitem['fields'].get('System.CreatedDate'),
                    "updated_at": workitem['fields'].get('System.ChangedDate'),
                    "label": {
                        "title": label.strip(),
                        "color": "#cccccc",
                    }
                })
        return label_links

    def convert_visibility_level(self, visibility):
        """Convert visibility string to GitLab visibility level."""
        return 20 if visibility == "public" else 0
