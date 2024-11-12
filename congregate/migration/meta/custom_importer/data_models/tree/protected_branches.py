from typing import Optional
from dataclasses import dataclass, asdict
from gitlab_ps_utils.dict_utils import strip_none
                    
'''
{
    "allow_force_push": "<class 'bool'>",
    "code_owner_approval_required": "<class 'bool'>",
    "created_at": "<class 'str'>",
    "merge_access_levels": "<class 'list'>",
    "name": "<class 'str'>",
    "project_id": "<class 'int'>",
    "push_access_levels": "<class 'list'>",
    "unprotect_access_levels": "<class 'list'>",
    "updated_at": "<class 'str'>"
}             
'''

@dataclass
class ProtectedBranches:
    
    allow_force_push: Optional[bool] = None
    code_owner_approval_required: Optional[bool] = None
    created_at: Optional[str] = None
    merge_access_levels: Optional[list] = []
    name: Optional[str] = None
    project_id: Optional[int] = None
    push_access_levels: Optional[list] = []
    unprotect_access_levels: Optional[list] = []
    updated_at: Optional[str] = None

    def to_dict(self):
        return strip_none(asdict(self))

                    