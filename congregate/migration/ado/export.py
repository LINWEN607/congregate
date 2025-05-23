import re
import pprint
from copy import deepcopy as copy
from pathlib import Path
from gitlab_ps_utils.dict_utils import dig
from gitlab_ps_utils.string_utils import deobfuscate
from gitlab_ps_utils.misc_utils import safe_json_response
from congregate.migration.meta.custom_importer.export_builder import ExportBuilder
from congregate.migration.meta.custom_importer.group_export_builder import GroupExportBuilder
from congregate.migration.meta.custom_importer.data_models.tree.merge_requests import MergeRequests
from congregate.migration.meta.custom_importer.data_models.tree.issues import Issues
from congregate.migration.meta.custom_importer.data_models.tree.project_members import ProjectMembers
from congregate.migration.meta.custom_importer.data_models.tree.project_member_user import ProjectMemberUser
from congregate.migration.meta.custom_importer.data_models.project_export import ProjectExport
from congregate.migration.meta.custom_importer.data_models.project import Project
from congregate.migration.meta.custom_importer.data_models.group_export import GroupExport
from congregate.migration.meta.custom_importer.data_models.group import Group
from congregate.migration.meta.custom_importer.data_models.tree.note import Note
from congregate.migration.meta.custom_importer.data_models.tree.author import Author
from congregate.migration.meta.custom_importer.data_models.tree.system_note_metadata import SystemNoteMetadata
from congregate.migration.meta.custom_importer.data_models.tree.merge_request_diff_file import MergeRequestDiffFile
from congregate.migration.meta.custom_importer.data_models.tree.merge_request_commit import MergeRequestCommit
from congregate.migration.meta.custom_importer.data_models.tree.merge_request_diff import MergeRequestDiff
from congregate.migration.ado.api.base import AzureDevOpsApiWrapper
from congregate.migration.ado.api.repositories import RepositoriesApi
from congregate.migration.ado.api.pull_requests import PullRequestsApi
from congregate.migration.ado.api.teams import TeamsApi
from congregate.migration.ado.api.users import UsersApi as ADOUsersApi
from congregate.migration.ado.api.work_items import WorkItemsApi
from congregate.migration.ado.work_items import WorkItemsClient
from congregate.migration.gitlab.api.users import UsersApi as GitlabUsersApi 
from congregate.migration.meta import constants

import congregate.helpers.migrate_utils as mig_utils

class AdoExportBuilder(ExportBuilder):
    def __init__(self, source_project):
        self.source_project = source_project
        self.repositories_api = RepositoriesApi()
        self.pull_requests_api = PullRequestsApi()
        self.teams_api = TeamsApi()
        self.ado_api = AzureDevOpsApiWrapper()
        self.ado_users_api = ADOUsersApi()
        self.work_items_api = WorkItemsApi()
        self.work_items_client = WorkItemsClient()
        self.gitlab_users_api = GitlabUsersApi()
        self.project_id = source_project['project_id']
        self.repository_id = source_project['id']
        self.members_map = {}
        self.project_metadata = Project(description=source_project['description'])
        super().__init__(source_project, clone_url=None)
        self.clone_url = self.build_clone_url(self.source_project)
        self.repo = self.clone_repo(self.project_path, self.clone_url)
        self.git_env = {
            'GIT_SSL_NO_VERIFY': '1',
            'GIT_ASKPASS': 'echo'
        }
    
    def create(self):
        tree = self.build_ado_data()
        self.build_export(tree, self.project_metadata)
        filename = self.create_export_tar_gz()
        self.delete_cloned_repo()
        return filename
    
    def build_ado_data(self):
        merge_requests = self.build_merge_requests()
        issues = self.build_issues()
        return ProjectExport(
            project_members=self.build_project_members(),
            merge_requests=merge_requests,
            issues=issues
        )

    def build_merge_requests(self):
        merge_requests = []
        for pr in self.pull_requests_api.get_all_pull_requests(project_id=self.project_id, repository_id=self.repository_id):
            # Convert Azure DevOps PR to GitLab MR format
            pr_id = pr['pullRequestId']
            merge_request_commits = self.build_mr_diff_commits(pr_id)
            if not merge_request_commits:
                continue
            start_sha = merge_request_commits[-1].sha
            target_sha = dig(pr, 'lastMergeSourceCommit', 'commitId')
            merge_request_diffs = self.build_mr_diff_files(start_sha, target_sha)
            merge_requests.append(MergeRequests(
                author=Author(name=dig(pr, 'createdBy', 'displayName')),
                iid=pr_id,
                source_branch=pr['sourceRefName'].replace("refs/heads/", ""),
                target_branch=pr['targetRefName'].replace("refs/heads/", ""),
                source_branch_sha=dig(pr, 'lastMergeSourceCommit', 'commitId') if self.pull_request_status(pr) == 'opened' else None,
                target_branch_sha=dig(pr, 'lastMergeTargetCommit', 'commitId'),
                merge_commit_sha=dig(pr, 'lastMergeCommit', 'commitId'),
                squash_commit_sha=dig(pr, 'lastMergeCommit', 'commitId') if pr.get('mergeStrategy') == 'squash' else None,
                title=pr['title'],
                description=pr.get('description', ''),
                state=self.pull_request_status(pr),
                draft=pr['isDraft'],
                created_at=pr['creationDate'],
                updated_at=pr.get('lastMergeSourceUpdateTime'),
                source_project_id=1,
                target_project_id=1,
                merge_request_diff=MergeRequestDiff(
                    state='collected' if len(merge_request_diffs) > 0 else 'empty',
                    created_at=pr['creationDate'],
                    updated_at=pr.get('lastMergeSourceUpdateTime', pr['creationDate']),
                    head_commit_sha=dig(pr, 'lastMergeSourceCommit', 'commitId') if self.pull_request_status(pr) == 'opened' else None,
                    base_commit_sha=dig(pr, 'lastMergeTargetCommit', 'commitId'),
                    start_commit_sha=dig(pr, 'lastMergeSourceCommit', 'commitId') if self.pull_request_status(pr) == 'opened' else None,
                    commits_count=len(merge_request_commits),
                    real_size=str(len(merge_request_diffs)),
                    files_count=len(merge_request_diffs),
                    sorted=True,
                    diff_type='regular',
                    merge_request_diff_commits=merge_request_commits,
                    merge_request_diff_files=merge_request_diffs
                ),
                # merged_at=dig(pr, 'lastMergeCommit', 'committer', 'date') if pr.get('lastMergeCommit') else None,
                # closed_at=pr.get('lastMergeTargetUpdateTime') if pr.get('lastMergeCommit') else None,
                notes=self.build_mr_notes(pr_id),
                author_id=self.get_new_member_id(pr['createdBy']),
                merge_request_assignees=self.add_merge_request_assignees([], pr),
                merge_request_reviewers=self.add_merge_request_reviewers([], pr),
                label_links=self.add_label_links([], pr),
                metrics=self.add_metrics(pr)
            ))
        return merge_requests

    def build_project_members(self):
        project_members = []
        staged_projects = mig_utils.get_staged_projects()
        for project in staged_projects:
            for member in project['members']:
                user_id = self.get_new_member_id(member)
                project_members.append(ProjectMembers(
                    access_level=30,
                    user_id=user_id,
                    user=ProjectMemberUser(
                        id=user_id,
                        username=member.get('username'),
                        public_email=member.get('email')
                    ),
                    expires_at=None
                ))
        return project_members

    def convert_access_level(self, ado_access_level):
        # ADO access levels: https://learn.microsoft.com/en-us/azure/devops/organizations/security/access-levels?view=azure-devops

        # Convert ADO access levels to GitLab access levels
        if ado_access_level == 'Stakeholder':
            return 10  # Guest
        elif ado_access_level == 'Basic':
            return 30  # Developer
        elif ado_access_level == 'Visual Studio Subscriber':
            return 40  # Maintainer
        elif ado_access_level == 'Advanced':
            return 50  # Owner
        else:
            return 20  # Reporter (default)

    def pull_request_status(self, pr):
        # ADO: https://learn.microsoft.com/en-us/rest/api/azure/devops/git/pull-requests/get-pull-request-by-id?view=azure-devops-rest-7.1&tabs=HTTP#pullrequeststatus
        # GitLab: https://docs.gitlab.com/ee/api/merge_requests.html#list-merge-requests
        if pr["status"] == "active":
            return "opened"
        elif pr["status"] == "completed":
            return "merged"
        elif pr["status"] == "abandoned":
            return "closed"
        else:
            return "unknown"

    def add_merge_request_assignees(self, assignee_ids, pr):
        assignee_ids = [{
            "user_id": self.get_new_member_id(pr['createdBy']),
            "created_at": pr['creationDate'],
        }]
        return assignee_ids

    def add_merge_request_reviewers(self, reviewer_ids, pr):
        reviewer_ids = []
        
        for reviewer in self.pull_requests_api.get_all_pull_request_reviewers(self.project_id, self.repository_id, pr.get('pullRequestId')):
            if reviewer.get('isContainer'):
                # This is situation of Group
                team_id = reviewer.get('id')
                team = self.teams_api.get_team(self.project_id, team_id)
                if not team:
                    self.log.error(f"Failed to get team for team_id={team_id}. Most likely the team is deleted, but has references from an old PR.")
                    continue
                else:
                    for group_member in self.teams_api.get_team_members(self.project_id, team_id):
                        if group_member:
                            reviewer_ids.append({
                                "user_id": self.get_new_member_id(group_member.get('identity')),
                                "created_at": pr['creationDate'],
                                "state": "unreviewed" # we don't know yet
                            })
            else:
                # This is situation of User
                state = 'approved' if reviewer['vote'] == 10 else 'unreviewed'
                # get descriptor from avatar link 🤷‍♂️
                reviewer["descriptor"] = reviewer.get('_links', {}).get('avatar', {}).get('href').split('/')[-1]
                reviewer_ids.append({
                    "user_id": self.get_new_member_id(reviewer),
                    "created_at": pr['creationDate'],
                    "state": state
                })
        # Deduplicating and taking "approved" state only
        result = {}
        for reviewer in reviewer_ids:
            user_id = reviewer.get('user_id')
            if user_id not in result or reviewer.get('state') == 'approved':
                result[user_id] = reviewer
            
        return list(result.values())

    def add_label_links(self, label_links, pr):
        # GitLab Sea Buckthorn
        # Hex: #fca326
        # RGB: 252, 163, 38

        # GitLab Orange
        # Hex: #fc6d26
        # RGB: 252, 109, 38

        # GitLab Cinnabar
        # Hex: #e24329
        # RGB: 226, 67, 41

        # GitLab Victoria
        # Hex: #554488
        # RGB: 85, 68, 136

        label_links = []
        for label in pr.get('labels', []):
            label_links.append({
                "target_type": "MergeRequest",
                "created_at": pr['creationDate'],
                "updated_at": pr['creationDate'],
                "label": {
                    "title": label['name'],
                    "color": "#fc6d26",
                }
            })
        return label_links

    def add_metrics(self, pr):
        metrics = {
            "merged_by_id": self.get_merged_by_user(pr) if self.pull_request_status(pr) == 'merged' else None,
        }
        return metrics

    def add_assignee_ids(self, assignee_ids, source_project):
        assignee_ids = []
        for username in source_project["members"]:
            assignee_ids.append(self.get_new_member_id(username.get("id")))
        return assignee_ids

    def add_to_members_map(self, member):
        member_copy = copy(member)
        guid = member.get('descriptor', member.get('id'))
        member_copy['id'] = len(self.members_map.keys())+1
        self.members_map[guid] = member_copy

    def get_merged_by_user(self, pr):
        request = self.pull_requests_api.get_pull_request(self.project_id, self.repository_id, pr['pullRequestId'])
        return self.get_new_member_id(safe_json_response(request).get('closedBy'))

    def get_new_member_id(self, member):
        if not member:
            return None
        if mid := dig(self.members_map, member.get('descriptor'), 'id', default=dig(self.members_map, member['id'], 'id')):
            return mid
        else:
            self.add_to_members_map(member)
            return self.get_new_member_id(member)

    def build_clone_url(self, source_project):
        clone_url = source_project['http_url_to_repo']
        decoded_token = deobfuscate(self.config.source_token)
        return clone_url.replace("@", f"{decoded_token}@")

    def build_mr_notes(self, pr_id):
        notes = []
        for thread in self.pull_requests_api.get_all_pull_request_threads(project_id=self.project_id, repository_id=self.repository_id, pull_request_id=pr_id):
            for comment in thread['comments']:
                # Format the comment content before adding it as a note.
                formatted_note = self.replace_ado_user_mentions(comment.get('content', ''))
                notes.append(Note(
                    note=formatted_note,
                    author_id=self.get_new_member_id(comment['author']),
                    project_id=1,
                    created_at=comment['publishedDate'],
                    updated_at=comment['publishedDate'],
                    noteable_type="MergeRequest",
                    author=Author(
                        name=comment['author']['displayName']
                    ),
                    system_note_metadata=self.generate_system_metadata(comment)
                ))
        return notes

    def build_mr_diff_commits(self, pr_id):
        commits = []
        count = 0
        for commit in self.pull_requests_api.get_all_pull_request_commits(self.project_id, self.repository_id, pr_id):
            commits.append(MergeRequestCommit(
                authored_date=dig(commit, 'author', 'date'),
                committed_date=dig(commit, 'committer', 'date'),
                commit_author=Author(
                    name=dig(commit, 'author', 'name'),
                    email=dig(commit, 'author', 'email'),
                ),
                committer=Author(
                    name=dig(commit, 'committer', 'name'),
                    email=dig(commit, 'committer', 'email'),
                ),
                relative_order=count,
                sha=commit['commitId'],
                message=commit['comment']
            ))
            count += 1
        return commits

    def build_mr_diff_files(self, source_sha, target_sha):
        diff_files = []
        count = 0
        req = self.pull_requests_api.get_pull_request_diffs(self.project, self.repository_id, source_sha, target_sha)
        if diffs := safe_json_response(req):
            for change in diffs.get('changes', []):
                filename = dig(change, 'item', 'path', default='').lstrip('/')
                git_diff = self.repo.git.diff(source_sha, target_sha, '--', f"{filename}")
                diff_string = '@@' + '@@'.join(git_diff.split('@@')[1:])
                mode_match = re.search(r'100755|100644|100755', git_diff)
                mode = mode_match.group(0) if mode_match else '100644'  # Default to 100644 if no match found
                diff_files.append(MergeRequestDiffFile(
                    relative_order=count,
                    utf8_diff=diff_string,
                    old_path=filename,
                    new_path=filename,
                    renamed_file=False,
                    deleted_file=False,
                    too_large=False,
                    binary=True if Path(filename).suffix in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.bmp', '.webp'] else False,
                    encoded_file_path=False,
                    new_file=True if change.get('changeType') == 'add' else False,
                    a_mode=mode,
                    b_mode=mode
                ))
                count += 1
        return diff_files
    
    def generate_system_metadata(self, comment):
        if comment.get('commentType', 'text') != 'text':
            action = None
            commit_count = None
            content = comment['content']
            if any(x in content for x in ['as a reviewer', 'required reviewer', 'from the reviewers']):
                action = 'reviewer'
            elif 'reference' in content:
                action = 'commit'
                commit_count = 1
            return SystemNoteMetadata(
                created_at=comment['publishedDate'],
                updated_at=comment['publishedDate'],
                commit_count=commit_count,
                action=action,
            )
        return None

    def replace_ado_user_mentions(self, text):
        """
        Finds GUID user mentions in the form @<GUID> and replaces them with GitLab-style mentions by:
        1. Looking up the ADO user by GUID.
        2. Retrieving the user's email.
        3. Querying GitLab to get the username corresponding to that email.
        """
        def repl(match):
            guid = match.group(1)
            response = safe_json_response(self.ado_users_api.get_user_by_guid(guid))
            if not response:
                self.log.error(f"ADO user not found for GUID: {guid}")
                return f"@{guid}"
            email = self.get_user_email(response)
            if not email:
                self.log.error(f"Email not found for ADO user with GUID: {guid}")
                return f"@{guid}"
            
            # Query GitLab to get the username using the email
            username_response = safe_json_response(self.gitlab_users_api.search_for_user_by_email(self.config.destination_host, self.config.destination_token, email))
            if not username_response or not isinstance(username_response, list):
                self.log.warning(f"GitLab user not found for email: {email}. Using GUID instead.")
                return f"@{guid}"
            
            gitlab_username = username_response[0].get("username")
            if not gitlab_username:
                self.log.warning(f"GitLab user exists for email {email}, but no username found. Using GUID instead.")
                return f"@{guid}"
            
            return f"@{gitlab_username}"
        
        # Regex pattern assuming GUID mentions are in the form @<GUID>
        return re.sub(constants.GUID_PATTERN, repl, text)
        
    def get_user_email(self, ado_user):
        """
        Extracts the email address from an Azure DevOps user object.

        :param ado_user: (dict) The user data retrieved from Azure DevOps Graph API.
        :return: (str) The user's email address if found, otherwise None.
        """
        try:
            return ado_user.get("properties", {}).get("Mail", {}).get("$value")
        except Exception as e:
            self.log.error(f"Failed to extract email from ADO user: {e}")
            return None

    def build_issues(self):
        issues = []
        for wi in self.work_items_client.get_all_work_items(self.project):
            workitem = self.work_items_api.get_work_item(self.project_id, wi.get('id')).json()
            pprint.pprint(workitem)
            author = workitem['fields'].get('System.CreatedBy', {})
            assignee = workitem['fields'].get('System.AssignedTo', {})
            issues.append(Issues(
                author_id=self.get_new_member_id(author),
                project_id=1,
                title=workitem['fields'].get('System.Title', 'No Title'),
                description=workitem['fields'].get('System.Description', 'No Description'),
                created_at=workitem['fields'].get('System.CreatedDate', 'No Created Date'),
                # updated_at=workitem['fields'].get('System.ChangedDate'),
                # updated_by_id=gl_author,
                # state=workitem['fields'].get('System.State', 'No State'),
                state=self.issue_state(workitem['fields'].get('System.State', 'No State')),
                iid=workitem['id'],
                issue_assignees=[{"user_id": self.get_new_member_id(assignee)}],
                # notes=self.build_issue_notes(wi['id']),
                label_links=self.label_links(workitem),
            ))
        return issues

    def issue_state(self, state):
        if state == 'New':
            return 'opened'
        elif state == 'Active':
            return 'opened'
        elif state == 'Resolved':
            return 'closed'
        elif state == 'Closed': 
            return 'closed'
        else:
            return 'opened'


    def label_links(self, workitem):
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

class AdoGroupExportBuilder(GroupExportBuilder):
    def __init__(self, source_group):
        self.source_group = source_group
        self.group_metadata = Group(
            id=1,
            name=source_group['name'],
            path=source_group['path'],
            description=source_group['description'],
            membership_lock=True,
            # https://docs.gitlab.com/development/permissions/predefined_roles/#general-permissions
            visibility_level=self.convert_visibility_level(source_group.get('visibility')),
            tree_path=[1]
        )
        super().__init__(source_group)

    def create(self):
        tree = self.build_ado_data()
        self.build_export(tree, self.group_metadata)
        filename = self.create_export_tar_gz()
        return filename

    def build_ado_data(self):
        namespace_settings = self.namespace_settings()
        return GroupExport(
            namespace_settings=namespace_settings
        )

    def namespace_settings(self):
        return {"prevent_sharing_groups_outside_hierarchy":True}
    
    def convert_visibility_level(self, visibility):
        if visibility == "private":
            return 0
        elif visibility == "public":
            return 20
        return 0


