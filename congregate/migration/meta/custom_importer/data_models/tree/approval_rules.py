from typing import Optional, List
from dataclasses import dataclass, asdict, field
from gitlab_ps_utils.dict_utils import strip_none

@dataclass
class ApprovalRules:
    
    applies_to_all_protected_branches: Optional[bool] = None
    approval_project_rules_protected_branches: Optional[List[dict]] = field(default_factory=list)
    approval_project_rules_users: Optional[List[dict]] = field(default_factory=list)
    approvals_required: Optional[int] = None
    name: Optional[str] = None
    orchestration_policy_idx: None = None
    report_type: None = None
    rule_type: Optional[str] = None
    scanners: Optional[List[dict]] = field(default_factory=list)
    severity_levels: Optional[List[dict]] = field(default_factory=list)
    vulnerabilities_allowed: Optional[int] = None
    vulnerability_states: Optional[List[dict]] = field(default_factory=list)

    def to_dict(self):
        return strip_none(asdict(self))

                    