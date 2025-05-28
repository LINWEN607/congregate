import re
import os
from urllib.parse import quote_plus
from copy import deepcopy as copy
from pathlib import Path
from gitlab_ps_utils.dict_utils import dig
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
from congregate.migration.codecommit.api.base import CodeCommitApiWrapper



class CodeCommitExportBuilder(ExportBuilder):
    def __init__(self, source_project):
        self.source_project = source_project
        self.base_api = CodeCommitApiWrapper()
        self.project_id = source_project['namespace']
        self.repository_id = source_project['id']
        self.members_map = {}
        self.project_metadata = Project(description=source_project['description'])
        super().__init__(project=source_project, clone_url=None)
        self.clone_url = self.build_clone_url()
        self.repo = self.clone_repo(self.project_path, self.clone_url)
        self.git_env = {
            'GIT_SSL_NO_VERIFY': '1',
            'GIT_ASKPASS': 'echo'
        }

    def create(self):
        tree = self.build_codecommit_data()
        self.build_export(tree, self.project_metadata)
        filename = self.create_export_tar_gz()
        self.delete_cloned_repo()
        return filename
    
    def build_codecommit_data(self):
        merge_requests = self.build_merge_requests()
        return ProjectExport(
            project_members=[],
            merge_requests=merge_requests
        )
    
    def build_mr_diff_files(self, source_sha, target_sha):
        diff_files = []
        count = 0
        req = self.base_api.get_pull_request_diffs(self.project_name, self.repository_id, source_sha, target_sha)
        if diffs := safe_json_response(req):
            for change in diffs:
                filename = change["afterBlob"]["path"].lstrip('/')
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

    def build_merge_requests(self):
        merge_requests = []
        for pr in self.base_api.get_detailed_pull_requests(project_id=self.project_id, repository_id=self.repository_id):
            # Convert CodeCommit PR to GitLab MR format
            pr_id = pr["pullRequestId"]
            
            # CodeCommit API doesn't support direct mr commit lookup
            # merge_request_commits = self.build_mr_diff_commits(pr_id)

            # The AWS CodeCommit API returns a list of PR targets.
            # However, it seems to be impossible to create more than one target, so we're looking at the [0] list element only.
            start_sha = pr["pullRequestTargets"][0]["sourceCommit"]
            target_sha = pr["pullRequestTargets"][0]["destinationCommit"]
            merge_request_diffs = self.build_mr_diff_files(start_sha, target_sha)
            merge_requests.append(MergeRequests(
                author=self.base_api.get_user_from_arn(pr["authorArn"]),
                iid=pr_id,
                source_branch=pr["pullRequestTargets"][0]["sourceReference"].replace("refs/heads/", ""),
                target_branch=pr["pullRequestTargets"][0]["destinationReference"].replace("refs/heads/", ""),
                source_branch_sha=start_sha,
                target_branch_sha=target_sha,
                merge_commit_sha=pr["pullRequestTargets"][0]["mergeMetadata"]["mergeCommitId"],
                squash_commit_sha= pr["pullRequestTargets"][0]["mergeMetadata"]["mergeCommitId"] if pr["pullRequestTargets"][0]["mergeMetadata"]["mergeOption"].lower() == 'squash_merge' else None,
                title=pr['title'],
                description=pr['description'],
                state=self.pull_request_status(pr),
                # draft status is not supported by CodeCommit pull requests
                draft=False,
                created_at=pr['creationDate'],
                updated_at=pr.get('lastActivityDate'),
                source_project_id=1,
                target_project_id=1,
                merge_request_diff=MergeRequestDiff(
                    state='collected' if len(merge_request_diffs) > 0 else 'empty',
                    created_at=pr['creationDate'],
                    updated_at=pr.get('lastMergeSourceUpdateTime', pr['creationDate']),
                    head_commit_sha=dig(pr, 'lastMergeSourceCommit', 'commitId') if self.pull_request_status(pr) == 'opened' else None,
                    base_commit_sha=dig(pr, 'lastMergeTargetCommit', 'commitId'),
                    start_commit_sha=dig(pr, 'lastMergeSourceCommit', 'commitId') if self.pull_request_status(pr) == 'opened' else None,
                    commits_count=1, # TBD len(merge_request_commits)
                    real_size=str(len(merge_request_diffs)),
                    files_count=len(merge_request_diffs),
                    sorted=True,
                    diff_type='regular',
                    #merge_request_diff_commits=merge_request_commits,
                    merge_request_diff_files=merge_request_diffs
                ),
                # merged_at=dig(pr, 'lastMergeCommit', 'committer', 'date') if pr.get('lastMergeCommit') else None,
                # closed_at=pr.get('lastMergeTargetUpdateTime') if pr.get('lastMergeCommit') else None,
                notes=self.build_mr_notes(pr_id),
                author_id=self.get_new_member_id(pr['createdBy'])
            ))
        return merge_requests

    def pull_request_status(self, pr):
        # CodeCommit: https://docs.aws.amazon.com/cli/latest/reference/codecommit/update-pull-request-status.html
        # GitLab: https://docs.gitlab.com/ee/api/merge_requests.html#list-merge-requests
        if pr["pullRequestStatus"].lower() == "open":
            return "opened"
        elif pr["status"].lower() == "closed":
            return "closed"
        else:
            return "unknown"

    def build_clone_url(self):
        src_aws_codecommit_username = self.config.src_aws_codecommit_username
        src_aws_codecommit_password = quote_plus(self.config.src_aws_codecommit_password, safe='=')
        src_aws_region = self.config.src_aws_region
        
        # clone_url = source_project['http_url_to_repo']
        # decoded_token = deobfuscate(self.config.source_token)
        return f"https://{src_aws_codecommit_username}:{src_aws_codecommit_password}@git-codecommit.{src_aws_region}.amazonaws.com/v1/repos/{self.source_project.get('name')}"
    
    def build_mr_notes(self, pr_id):
        notes = []
        for comment in self.base_api.get_all_pull_request_threads(project_id=self.project_id, repository_id=self.repository_id, pull_request_id=pr_id):
            notes.append(Note(
                note=comment['content'],
                author_id=self.get_new_member_id(comment['author']),
                project_id=1,
                created_at=comment['creationDate'],
                updated_at=comment['lastModifiedDate'],
                noteable_type="MergeRequest",
                author=self.base_api.get_user_from_arn(comment['authorArn']),
                system_note_metadata=self.generate_system_metadata(comment)
                ))
        return notes
    
    def generate_system_metadata(self, comment):
        # CodeCommit supports simple commenting only
        """ if comment['commentType'] != 'text':
            action = None
            commit_count = None
            content = comment['content']
            if any(x in content for x in ['as a reviewer', 'required reviewer', 'from the reviewers']):
                action = 'reviewer'
            elif 'reference' in content:
                action = 'commit'
                commit_count = 1
            return SystemNoteMetadata(
                created_at=comment['creationDate'],
                updated_at=comment['lastModifiedDate'],
                commit_count=0,
                action='reviewer'
            ) """
        return None
