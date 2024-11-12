from typing import Optional
from dataclasses import dataclass, asdict
from gitlab_ps_utils.dict_utils import strip_none

'''
Set every property in the dataclass to Optional
'''

@dataclass
class Project:
    description: Optional[str] = None
    visibility_level: Optional[int] = None
    archived: Optional[bool] = None
    merge_requests_template: Optional[str] = None
    merge_requests_rebase_enabled: Optional[bool] = None
    approvals_before_merge: Optional[int] = None
    reset_approvals_on_push: Optional[bool] = None
    merge_requests_ff_only_enabled: Optional[bool] = None
    issues_template: Optional[str] = None
    shared_runners_enabled: Optional[bool] = None
    build_allow_git_fetch: Optional[bool] = None
    build_timeout: Optional[int] = None
    public_builds: Optional[bool] = None
    pending_delete: Optional[bool] = None
    last_repository_check_failed: Optional[bool] = None | None
    only_allow_merge_if_pipeline_succeeds: Optional[bool] = None
    has_external_issue_tracker: Optional[bool] = None
    request_access_enabled: Optional[bool] = None
    has_external_wiki: Optional[bool] = None
    only_allow_merge_if_all_discussions_are_resolved: Optional[bool] = None
    service_desk_enabled: Optional[bool] = None
    printing_merge_request_link_enabled: Optional[bool] = None
    auto_cancel_pending_pipelines: Optional[str] = None
    disable_overriding_approvers_per_merge_request: Optional[bool] = None
    delete_error: Optional[str] = None
    resolve_outdated_diff_discussions: Optional[bool] = None
    jobs_cache_index: Optional[int] = None
    external_authorization_classification_label: Optional[str] = None
    pages_https_only: Optional[bool] = None
    merge_requests_author_approval: Optional[bool] = None
    merge_requests_disable_committers_approval: Optional[bool] = None
    require_password_to_approve: Optional[bool] = None
    remove_source_branch_after_merge: Optional[bool] = None
    suggestion_commit_message: Optional[str] = None
    autoclose_referenced_issues: Optional[bool] = None
    allow_merge_on_skipped_pipeline: Optional[bool] = None
    squash_option: Optional[str] = None
    merge_commit_template: Optional[str] = None
    squash_commit_template: Optional[str] = None

    def to_dict(self):
        return strip_none(asdict(self))
