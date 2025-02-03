from dataclasses import dataclass, field, asdict
from typing import Optional, List

@dataclass
class DeployAccessLevel:
    access_level: Optional[int] = None
    user_id: Optional[int] = None
    group_id: Optional[int] = None

    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v is not None}

@dataclass
class ApprovalRule:
    access_level: Optional[int] = None
    user_id: Optional[int] = None
    group_id: Optional[int] = None
    required_approvals: int = 0
    group_inheritance_type: int = 0

    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v is not None}

@dataclass
class NewProjectProtectedEnvironmentPayload:
    name: str
    deploy_access_levels: List[DeployAccessLevel] = field(default_factory=list)
    approval_rules: List[ApprovalRule] = field(default_factory=list)

    def to_dict(self):
        return {
            "name": self.name,
            "deploy_access_levels": [dal.to_dict() for dal in self.deploy_access_levels],
            "approval_rules": [ar.to_dict() for ar in self.approval_rules]
        }
