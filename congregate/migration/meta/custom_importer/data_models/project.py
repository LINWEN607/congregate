from dataclasses import dataclass, asdict
from gitlab_ps_utils.dict_utils import strip_none

@dataclass
class Project:
    description: str
    visibility_level: int
    archived: bool
    merge_requests_template: str
    merge_requests_rebase_enabled: bool
    approvals_before_merge: int
    reset_approvals_on_push: bool
    merge_requests_ff_only_enabled: bool
    issues_template: str | None
    shared_runners_enabled: bool
    build_allow_git_fetch: bool
    build_timeout: int
    public_builds: bool
    pending_delete: bool
    last_repository_check_failed: bool | None
    only_allow_merge_if_pipeline_succeeds: bool
    has_external_issue_tracker: bool
    request_access_enabled: bool
    has_external_wiki: bool
    only_allow_merge_if_all_discussions_are_resolved: bool
    service_desk_enabled: bool
    printing_merge_request_link_enabled: bool
    auto_cancel_pending_pipelines: str
    disable_overriding_approvers_per_merge_request: bool
    delete_error: str | None
    resolve_outdated_diff_discussions: bool
    jobs_cache_index: int
    external_authorization_classification_label: str
    pages_https_only: bool
    merge_requests_author_approval: bool
    merge_requests_disable_committers_approval: bool
    require_password_to_approve: bool
    remove_source_branch_after_merge: bool
    suggestion_commit_message: str
    autoclose_referenced_issues: bool
    allow_merge_on_skipped_pipeline: bool
    squash_option: str
    merge_commit_template: str | None
    squash_commit_template: str | None

    def to_dict(self):
        return strip_none(asdict(self))
