from typing import Optional, List
from dataclasses import dataclass, asdict, field
from gitlab_ps_utils.dict_utils import strip_none
                    
@dataclass
class ProtectedBranches:
    
    allow_force_push: Optional[bool] = None
    code_owner_approval_required: Optional[bool] = None
    created_at: Optional[str] = None
    merge_access_levels: Optional[List] = field(default_factory=list)
    name: Optional[str] = None
    project_id: Optional[int] = None
    push_access_levels: Optional[List] = field(default_factory=list)
    unprotect_access_levels: Optional[List] = field(default_factory=list)
    updated_at: Optional[str] = None

    def to_dict(self):
        return strip_none(asdict(self))

                    