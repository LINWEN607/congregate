
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
    
    allow_maintainer_to_push: bool
    approvals: list
    approvals_before_merge: int | None = None
    author_id: int
    award_emoji: list
    created_at: str
    description: str
    diff_head_sha: str
    discussion_locked: bool | None = None
    draft: bool
    events: list
    iid: int
    in_progress_merge_commit_sha: str | None = None
    label_links: list
    last_edited_at: str | None = None
    last_edited_by_id: int | None = None
    lock_version: int
    merge_commit_sha: str | None = None
    merge_error: str | None = None
    merge_params: dict
    merge_ref_sha: str | None = None
    merge_request_assignees: list
    merge_request_diff: dict
    merge_request_reviewers: list
    merge_status: str
    merge_user_id: int | None = None
    metrics: dict
    notes: list
    rebase_commit_sha: str | None = None
    resource_label_events: list
    resource_milestone_events: list
    resource_state_events: list
    source_branch: str
    source_branch_sha: str
    source_project_id: int
    squash: bool
    squash_commit_sha: str | None = None
    state: str
    target_branch: str
    target_branch_sha: str
    target_project_id: int
    time_estimate: int
    timelogs: list
    title: str
    updated_at: str
    updated_by_id: int | None = None

    def to_dict(self):
        return strip_none(asdict(self))

                    