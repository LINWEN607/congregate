
from dataclasses import dataclass, asdict
from gitlab_ps_utils.dict_utils import strip_none
                    
'''
{
    "created_at": "<class 'str'>",
    "project_id": "<class 'int'>",
    "updated_at": "<class 'str'>"
}             
'''

@dataclass
class SecuritySetting:
    
    created_at: str
    project_id: int
    updated_at: str

    def to_dict(self):
        return strip_none(asdict(self))

                    