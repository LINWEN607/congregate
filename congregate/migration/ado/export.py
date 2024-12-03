import re
import os
from copy import deepcopy as copy
from pathlib import Path
from gitlab_ps_utils.dict_utils import dig
from gitlab_ps_utils.json_utils import json_pretty
from gitlab_ps_utils.string_utils import deobfuscate
from gitlab_ps_utils.misc_utils import safe_json_response
from congregate.migration.meta.custom_importer.export_builder import ExportBuilder
from congregate.migration.meta.custom_importer.data_models.tree.merge_requests import MergeRequests
from congregate.migration.meta.custom_importer.data_models.tree.project_members import ProjectMembers
from congregate.migration.meta.custom_importer.data_models.project_export import ProjectExport
from congregate.migration.meta.custom_importer.data_models.project import Project
from congregate.migration.meta.custom_importer.data_models.tree.note import Note
from congregate.migration.meta.custom_importer.data_models.tree.author import Author
from congregate.migration.meta.custom_importer.data_models.tree.system_note_metadata import SystemNoteMetadata
from congregate.migration.meta.custom_importer.data_models.tree.merge_request_diff_file import MergeRequestDiffFile
from congregate.migration.meta.custom_importer.data_models.tree.merge_request_commit import MergeRequestCommit
from congregate.migration.meta.custom_importer.data_models.tree.merge_request_diff import MergeRequestDiff
from congregate.migration.ado.api.projects import ProjectsApi
from congregate.migration.ado.api.repositories import RepositoriesApi
from congregate.migration.ado.api.pull_requests import PullRequestsApi
from congregate.migration.ado.api.teams import TeamsApi


class AdoExportBuilder(ExportBuilder):
    def __init__(self, source_project):
        self.source_project = source_project
        self.projects_api = ProjectsApi()
        self.repositories_api = RepositoriesApi()
        self.pull_requests_api = PullRequestsApi()
        self.teams_api = TeamsApi()
        self.project_id = source_project['namespace']['id']
        self.repository_id = source_project['id']
        self.source_project = source_project
        self.members_map = {}
        self.project_metadata = Project(description=source_project['description'])
        # project_name = source_project['name']
        super().__init__(source_project, clone_url=None)
        # self.clone_url = self.source_project['http_url_to_repo']
        self.clone_url = self.build_clone_url(self.source_project)
        self.repo = self.clone_repo(self.project_path, self.clone_url)
        self.git_env = {
            'GIT_SSL_NO_VERIFY': '1',
            'GIT_ASKPASS': 'echo'
        }
    
    def build_ado_data(self):
        merge_requests = self.build_merge_requests()
        return ProjectExport(
            project_members=self.build_project_members(),
            merge_requests=merge_requests
        )

    def build_merge_requests(self):
        merge_requests = []
        for pr in self.pull_requests_api.get_all_pull_requests(project_id=self.project_id, repository_id=self.repository_id):
            # Convert Azure DevOps PR to GitLab MR format
            pr_id = pr['pullRequestId']
            merge_request_commits = self.build_mr_diff_commits(pr_id)
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
                description=pr['description'],
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
                author_id=self.get_new_member_id(pr['createdBy'])
            ))
        return merge_requests
    
    def build_project_members(self):
        project_members = []
        for team in self.teams_api.get_teams(self.project_id):
            for member in self.teams_api.get_team_members(self.project_id, team["id"]):
                project_members.append(ProjectMembers(
                    access_level=self.convert_access_level(member.get('accessLevel')),
                    user_id=member.get('id'),
                    # username=member.get('uniqueName'),
                    # name=member.get('displayName'),
                    expires_at=None  # ADO doesn't have an expiration concept for project members
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

    def add_assignee_ids(self, assignee_ids, source_project):
        assignee_ids = []
        for username in source_project["members"]:
            assignee_ids.append(self.get_new_member_id(username.get("id")))
        return assignee_ids

    def add_to_members_map(self, member):
        member_copy = copy(member)
        guid = member['id']
        member_copy['id'] = len(self.members_map.keys())+1
        self.members_map[guid] = member_copy
    
    def get_new_member_id(self, member):
        if mid := dig(self.members_map, member['id'], 'id'):
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
                notes.append(Note(
                    note=comment['content'],
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
                mode = re.search(r'100755|100644|100755', git_diff).group(0)
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
        if comment['commentType'] != 'text':
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
