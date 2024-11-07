
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
    create_access_levels: list
    created_at: str
    name: str
    project_id: int
    updated_at: str

    def to_dict(self):
        return strip_none(asdict(self))
                    