
from dataclasses import dataclass, asdict, field
from typing import Optional, List

@dataclass
class ProjectLevelApproverPayload():
    approvals_before_merge: Optional[int] = 0
    reset_approvals_on_push: Optional[bool] = False
    selective_code_owner_removals: Optional[bool] = False
    disable_overriding_approvers_per_merge_request: Optional[bool] = False
    merge_requests_author_approval: Optional[bool] = False
    merge_requests_disable_committers_approval: Optional[bool] = False
    require_password_to_approve: Optional[bool] = False
    
    def to_dict(self):
        return { k:v for k, v in asdict(self).items() if v }
