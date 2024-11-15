from typing import Optional, List
from dataclasses import dataclass, asdict, field
from gitlab_ps_utils.dict_utils import strip_none
                    
@dataclass
class MergeRequests:
    allow_maintainer_to_push: Optional[bool] = None
    approvals: Optional[List] = field(default_factory=[])
    approvals_before_merge: Optional[str] = None
    author_id: Optional[str] = None
    award_emoji: Optional[List] = field(default_factory=[])
    created_at: Optional[str] = None
    description: Optional[str] = None
    diff_head_sha: Optional[str] = None
    discussion_locked: Optional[bool] = None
    draft: Optional[bool] = None
    events: Optional[List] = field(default_factory=[])
    iid: Optional[str] = None
    in_progress_merge_commit_sha: Optional[str] = None
    label_links: Optional[List] = field(default_factory=[])
    last_edited_at: Optional[str] = None
    last_edited_by_id: Optional[str] = None
    lock_version: Optional[str] = None
    merge_commit_sha: Optional[str] = None
    merge_error: Optional[str] = None
    merge_params: Optional[dict] = field(default_factory=dict)
    merge_ref_sha: Optional[str] = None
    merge_request_assignees: Optional[List] = field(default_factory=[])
    merge_request_diff: Optional[dict] = field(default_factory=dict)
    merge_request_reviewers: Optional[List] = field(default_factory=[])
    merge_status: Optional[str] = None
    merge_user_id: Optional[str] = None
    metrics: Optional[dict] = field(default_factory=dict)
    notes: Optional[List] = field(default_factory=[])
    rebase_commit_sha: Optional[str] = None
    resource_label_events: Optional[List] = field(default_factory=[])
    resource_milestone_events: Optional[List] = field(default_factory=[])
    resource_state_events: Optional[List] = field(default_factory=[])
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
    timelogs: Optional[List] = field(default_factory=[])
    title: Optional[str] = None
    updated_at: Optional[str] = None
    updated_by_id: Optional[str] = None

    def to_dict(self):
        return strip_none(asdict(self))

                    