from typing import Optional
from dataclasses import dataclass, asdict, field

@dataclass
class Group:
    '''
        Dataclass that represents what will go into the <id>.json (group) file in the export

        This can be left completely default
    '''

    # depth: Optional[int] = 1
    tree_path: Optional[list] = None
    # tree_cycle: Optional[bool] = False
    id: Optional[int] = None
    name: Optional[str] = None
    path: Optional[str] = None
    description: Optional[str] = None
    # avatar: Optional[dict] = None
    membership_lock: Optional[bool] = None
    # share_with_group_lock: Optional[bool] = False
    visibility_level: Optional[int] = 0
    # request_access_enabled: Optional[bool] = False
    # ldap_sync_status: Optional[str] = None
    # ldap_sync_error: Optional[str] = None
    # ldap_sync_last_update_at: Optional[str] = None
    # ldap_sync_last_successful_update_at: Optional[str] = None
    # ldap_sync_last_sync_at: Optional[str] = None
    # lfs_enabled: Optional[bool] = False
    description_html: Optional[str] = None
    # parent_id: Optional[int] = None
    # shared_runners_minutes_limit: Optional[int] = 50000
    # require_two_factor_authentication: Optional[bool] = False
    # two_factor_grace_period: Optional[int] = 48
    # cached_markdown_version: Optional[int] = 2162697
    # project_creation_level: Optional[int] = 2
    # file_template_project_id: Optional[int] = None
    # custom_project_templates_group_id: Optional[int] = None
    # auto_devops_enabled: Optional[bool] = None
    # last_ci_minutes_notification_at: Optional[str] = None
    # last_ci_minutes_usage_notification_level: Optional[int] = None
    # subgroup_creation_level: Optional[int] = 1
    # max_artifacts_size: Optional[int] = None
    # mentions_disabled: Optional[bool] = False
    # default_branch_protection: Optional[int] = 2
    # max_personal_access_token_lifetime: Optional[int] = None
    # push_rule_id: Optional[int] = None
    # shared_runners_enabled: Optional[bool] = True
    # allow_descendants_override_disabled_shared_runners: Optional[bool] = False
    # traversal_ids: Optional[list] = None
    # organization_id: Optional[int] = 1

    def to_dict(self):
        return asdict(self)
