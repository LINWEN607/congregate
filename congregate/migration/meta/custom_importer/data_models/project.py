from typing import Optional
from dataclasses import dataclass, asdict

@dataclass
class Project:
    '''
        Dataclass that represents what will go into the project.json file in the export

        This can be left completely default
    '''
    
    description: Optional[str] = None
    visibility_level: Optional[int] = 0
    archived: Optional[bool] = False
    merge_requests_template: Optional[str] = None
    merge_requests_rebase_enabled: Optional[bool] = False
    approvals_before_merge: Optional[int] = 0
    reset_approvals_on_push: Optional[bool] = True
    merge_requests_ff_only_enabled: Optional[bool] = False
    issues_template: Optional[str] = None
    shared_runners_enabled: Optional[bool] = True
    build_allow_git_fetch: Optional[bool] = True
    build_timeout: Optional[int] = 3600
    public_builds: Optional[bool] = True
    pending_delete: Optional[bool] = False
    last_repository_check_failed: Optional[bool] = None
    only_allow_merge_if_pipeline_succeeds: Optional[bool] = False
    has_external_issue_tracker: Optional[bool] = False
    request_access_enabled: Optional[bool] = True
    has_external_wiki: Optional[bool] = False
    only_allow_merge_if_all_discussions_are_resolved: Optional[bool] = False
    service_desk_enabled: Optional[bool] = True
    printing_merge_request_link_enabled: Optional[bool] = True
    auto_cancel_pending_pipelines: Optional[str] = "enabled"
    disable_overriding_approvers_per_merge_request: Optional[bool] = False
    delete_error: Optional[str] = None
    resolve_outdated_diff_discussions: Optional[bool] = False
    jobs_cache_index: Optional[int] = None
    external_authorization_classification_label: Optional[str] = ""
    pages_https_only: Optional[bool] = True
    merge_requests_author_approval: Optional[bool] = False
    merge_requests_disable_committers_approval: Optional[bool] = False
    require_password_to_approve: Optional[bool] = False
    remove_source_branch_after_merge: Optional[bool] = True
    suggestion_commit_message: Optional[str] = None
    autoclose_referenced_issues: Optional[bool] = True
    allow_merge_on_skipped_pipeline: Optional[bool] = None
    squash_option: Optional[str] = "default_off"
    merge_commit_template: Optional[str] = None
    squash_commit_template: Optional[str] = None

    def to_dict(self):
        return asdict(self)
