from dataclasses import dataclass, asdict, field
from typing import Optional, List

@dataclass
class MergeRequestLevelApproverPayload():
    name: str
    approvals_required: int
    user_ids: Optional[List[int]] = field(default_factory=list)
    group_ids: Optional[List[int]] = field(default_factory=list)
    protected_branch_ids: Optional[List[int]] = field(default_factory=list)
    
    def to_dict(self):
        return { k:v for k, v in asdict(self).items() if v }
