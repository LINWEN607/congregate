
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
    
    allow_force_push: bool
    code_owner_approval_required: bool
    created_at: str
    merge_access_levels: list
    name: str
    project_id: int
    push_access_levels: list
    unprotect_access_levels: list
    updated_at: str

    def to_dict(self):
        return strip_none(asdict(self))

                    