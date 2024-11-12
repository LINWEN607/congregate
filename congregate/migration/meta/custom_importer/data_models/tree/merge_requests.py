from typing import Optional
from dataclasses import dataclass, asdict
from gitlab_ps_utils.dict_utils import strip_none
                    
'''
{
    "allow_maintainer_to_push": "<class 'bool'>",
    "approvals": "<class 'list'>",
    "approvals_before_merge": "<class 'NoneType'>",
    "author_id": "<class 'int'>",
    "award_emoji": "<class 'list'>",
    "created_at": "<class 'str'>",
    "description": "<class 'str'>",
    "diff_head_sha": "<class 'str'>",
    "discussion_locked": "<class 'NoneType'>",
    "draft": "<class 'bool'>",
    "events": "<class 'list'>",
    "iid": "<class 'int'>",
    "in_progress_merge_commit_sha": "<class 'NoneType'>",
    "label_links": "<class 'list'>",
    "last_edited_at": "<class 'NoneType'>",
    "last_edited_by_id": "<class 'NoneType'>",
    "lock_version": "<class 'int'>",
    "merge_commit_sha": "<class 'NoneType'>",
    "merge_error": "<class 'NoneType'>",
    "merge_params": [
        "force_remove_source_branch"
    ],
    "merge_ref_sha": "<class 'NoneType'>",
    "merge_request_assignees": "<class 'list'>",
    "merge_request_diff": [
        "state",
        "created_at",
        "updated_at",
        "base_commit_sha",
        "real_size",
        "head_commit_sha",
        "start_commit_sha",
        "commits_count",
        "files_count",
        "sorted",
        "diff_type",
        "merge_request_diff_commits",
        "merge_request_diff_files"
    ],
    "merge_request_reviewers": "<class 'list'>",
    "merge_status": "<class 'str'>",
    "merge_user_id": "<class 'NoneType'>",
    "metrics": [
        "latest_build_started_at",
        "latest_build_finished_at",
        "first_deployed_to_production_at",
        "merged_at",
        "created_at",
        "updated_at",
        "merged_by_id",
        "latest_closed_by_id",
        "latest_closed_at",
        "first_comment_at",
        "first_commit_at",
        "last_commit_at",
        "diff_size",
        "modified_paths_size",
        "commits_count",
        "first_approved_at",
        "first_reassigned_at",
        "added_lines",
        "removed_lines",
        "target_project_id"
    ],
    "notes": "<class 'list'>",
    "rebase_commit_sha": "<class 'NoneType'>",
    "resource_label_events": "<class 'list'>",
    "resource_milestone_events": "<class 'list'>",
    "resource_state_events": "<class 'list'>",
    "source_branch": "<class 'str'>",
    "source_branch_sha": "<class 'str'>",
    "source_project_id": "<class 'int'>",
    "squash": "<class 'bool'>",
    "squash_commit_sha": "<class 'NoneType'>",
    "state": "<class 'str'>",
    "target_branch": "<class 'str'>",
    "target_branch_sha": "<class 'str'>",
    "target_project_id": "<class 'int'>",
    "time_estimate": "<class 'int'>",
    "timelogs": "<class 'list'>",
    "title": "<class 'str'>",
    "updated_at": "<class 'str'>",
    "updated_by_id": "<class 'NoneType'>"
}             
'''

@dataclass
class MergeRequests:
    allow_maintainer_to_push: Optional[bool] = None
    approvals: Optional[list] = []
    approvals_before_merge: Optional[str] = None
    author_id: Optional[str] = None
    award_emoji: Optional[list] = []
    created_at: Optional[str] = None
    description: Optional[str] = None
    diff_head_sha: Optional[str] = None
    discussion_locked: Optional[bool] = None
    draft: Optional[bool] = None
    events: Optional[list] = []
    iid: Optional[str] = None
    in_progress_merge_commit_sha: Optional[str] = None
    label_links: Optional[list] = []
    last_edited_at: Optional[str] = None
    last_edited_by_id: Optional[str] = None
    lock_version: Optional[str] = None
    merge_commit_sha: Optional[str] = None
    merge_error: Optional[str] = None
    merge_params: Optional[dict] = {}
    merge_ref_sha: Optional[str] = None
    merge_request_assignees: Optional[list] = []
    merge_request_diff: Optional[dict] = {}
    merge_request_reviewers: Optional[list] = []
    merge_status: Optional[str] = None
    merge_user_id: Optional[str] = None
    metrics: Optional[dict] = {}
    notes: Optional[list] = []
    rebase_commit_sha: Optional[str] = None
    resource_label_events: Optional[list] = []
    resource_milestone_events: Optional[list] = []
    resource_state_events: Optional[list] = []
    source_branch: Optional[str] = None
    source_branch_sha: Optional[str] = None
    source_project_id: Optional[str] = None
    squash: Optional[bool] = None
    squash_commit_sha: Optional[str] = None
    state: Optional[str] = None
    target_branch: Optional[str] = None
    target_branch_sha: Optional[str] = None
    target_project_id: Optional[str] = None
    time_estimate: Optional[str] = None
    timelogs: Optional[list] =[]
    title: Optional[str] = None
    updated_at: Optional[str] = None
    updated_by_id: Optional[str] = None

    def to_dict(self):
        return strip_none(asdict(self))

                    