
from dataclasses import dataclass, asdict
from gitlab_ps_utils.dict_utils import strip_none
                    
'''
{
    "applies_to_all_protected_branches": "<class 'bool'>",
    "approval_project_rules_protected_branches": "<class 'list'>",
    "approval_project_rules_users": "<class 'list'>",
    "approvals_required": "<class 'int'>",
    "name": "<class 'str'>",
    "orchestration_policy_idx": "<class 'NoneType'>",
    "report_type": "<class 'NoneType'>",
    "rule_type": "<class 'str'>",
    "scanners": "<class 'list'>",
    "severity_levels": "<class 'list'>",
    "vulnerabilities_allowed": "<class 'int'>",
    "vulnerability_states": "<class 'list'>"
}             
'''

@dataclass
class ApprovalRules:
    
    applies_to_all_protected_branches: bool
    approval_project_rules_protected_branches: list
    approval_project_rules_users: list
    approvals_required: int
    name: str
    orchestration_policy_idx: None = None
    report_type: None = None
    rule_type: str
    scanners: list
    severity_levels: list
    vulnerabilities_allowed: int
    vulnerability_states: list

    def to_dict(self):
        return strip_none(asdict(self))

                    