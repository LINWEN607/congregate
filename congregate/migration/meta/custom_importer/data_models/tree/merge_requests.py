from typing import Optional, List
from dataclasses import dataclass, asdict, field
from gitlab_ps_utils.dict_utils import strip_none
from congregate.migration.meta.custom_importer.data_models.tree.author import Author
from congregate.migration.meta.custom_importer.data_models.tree.system_note_metadata import SystemNoteMetadata
from congregate.migration.meta.custom_importer.data_models.tree.merge_request_commit import MergeRequestCommit
from congregate.migration.meta.custom_importer.data_models.tree.merge_request_diff import MergeRequestDiff
                    
@dataclass
class MergeRequests:
    # Required
    author: Author
    author_id: int
    iid: str
    source_branch: str
    source_branch_sha: str
    source_project_id: str
    target_branch: str
    target_branch_sha: str
    target_project_id: str
    title: str
    created_at: str
    merge_request_diff_commits: List[MergeRequestCommit] = field(default_factory=list)
    merge_request_diff_files: List[MergeRequestDiff] = field(default_factory=list)

    # Optional
    system_note_metadata: Optional[SystemNoteMetadata] = None
    allow_maintainer_to_push: Optional[bool] = None
    approvals: Optional[List] = field(default_factory=list)
    approvals_before_merge: Optional[str] = None
    award_emoji: Optional[List] = field(default_factory=list)
    description: Optional[str] = None
    diff_head_sha: Optional[str] = None
    discussion_locked: Optional[bool] = None
    draft: Optional[bool] = False
    events: Optional[List] = field(default_factory=list)
    in_progress_merge_commit_sha: Optional[str] = None
    label_links: Optional[List] = field(default_factory=list)
    last_edited_at: Optional[str] = None
    last_edited_by_id: Optional[str] = None
    lock_version: Optional[str] = None
    merge_commit_sha: Optional[str] = None
    merge_error: Optional[str] = None
    merge_params: Optional[dict] = field(default_factory=dict)
    merge_ref_sha: Optional[str] = None
    merge_request_assignees: Optional[List] = field(default_factory=list)
    merge_request_diff: Optional[dict] = field(default_factory=dict)
    merge_request_reviewers: Optional[List] = field(default_factory=list)
    merge_status: Optional[str] = None
    merge_user_id: Optional[str] = None
    metrics: Optional[dict] = field(default_factory=dict)
    notes: Optional[List] = field(default_factory=list)
    rebase_commit_sha: Optional[str] = None
    resource_label_events: Optional[List] = field(default_factory=list)
    resource_milestone_events: Optional[List] = field(default_factory=list)
    resource_state_events: Optional[List] = field(default_factory=list)
    squash: Optional[bool] = None
    squash_commit_sha: Optional[str] = None
    state: Optional[str] = None
    time_estimate: Optional[str] = None
    timelogs: Optional[List] = field(default_factory=list)
    updated_at: Optional[str] = None
    updated_by_id: Optional[str] = None

    def to_dict(self):
        return strip_none(asdict(self))

                    