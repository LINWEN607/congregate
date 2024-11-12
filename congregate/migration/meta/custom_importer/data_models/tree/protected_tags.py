from typing import Optional
from dataclasses import dataclass, asdict
from gitlab_ps_utils.dict_utils import strip_none
                    
'''
{
    "create_access_levels": "<class 'list'>",
    "created_at": "<class 'str'>",
    "name": "<class 'str'>",
    "project_id": "<class 'int'>",
    "updated_at": "<class 'str'>"
}             
'''

@dataclass
class ProtectedTags:
    create_access_levels: Optional[list] = []
    created_at: Optional[str] = None
    name: Optional[str] = None
    project_id: Optional[int] = None
    updated_at: Optional[str] = None

    def to_dict(self):
        return strip_none(asdict(self))
                    