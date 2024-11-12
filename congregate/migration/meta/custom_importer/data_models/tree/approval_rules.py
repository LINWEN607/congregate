from typing import Optional
from dataclasses import dataclass, asdict
from gitlab_ps_utils.dict_utils import strip_none

@dataclass
class ApprovalRules:
    
    applies_to_all_protected_branches: Optional[bool] = None
    approval_project_rules_protected_branches: Optional[list] = []
    approval_project_rules_users: Optional[list] = []
    approvals_required: Optional[int] = None
    name: Optional[str] = None
    orchestration_policy_idx: None = None
    report_type: None = None
    rule_type: Optional[str] = None
    scanners: Optional[list] = []
    severity_levels: Optional[list] = []
    vulnerabilities_allowed: Optional[int] = None
    vulnerability_states: Optional[list] = []

    def to_dict(self):
        return strip_none(asdict(self))

                    