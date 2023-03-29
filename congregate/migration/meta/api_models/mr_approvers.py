from dataclasses import dataclass, asdict
from typing import Optional, List

@dataclass
class MergeRequestApproverPayload():
    name: str
    approvals_required: int
    user_ids: Optional[List[int]] = []
    group_ids: Optional[List[int]] = []
    protected_branch_ids: Optional[List[int]] = []
    
    def to_dict(self):
        return { k:v for k, v in asdict(self).items() if v }
