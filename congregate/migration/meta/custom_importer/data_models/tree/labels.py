from typing import Optional
from dataclasses import dataclass, asdict
from gitlab_ps_utils.dict_utils import strip_none
                    
'''
{
    "color": "<class 'str'>",
    "created_at": "<class 'str'>",
    "description": "<class 'str'>",
    "group_id": "<class 'NoneType'>",
    "priorities": "<class 'list'>",
    "project_id": "<class 'int'>",
    "template": "<class 'bool'>",
    "textColor": "<class 'str'>",
    "title": "<class 'str'>",
    "type": "<class 'str'>",
    "updated_at": "<class 'str'>"
}             
'''

@dataclass
class Labels:
    
    color: Optional[str] = None
    created_at: Optional[str] = None
    description: Optional[str] = None
    group_id: Optional[int] = None
    priorities: Optional[list] = []
    project_id: Optional[int] = None
    template: Optional[bool] = None
    textColor: Optional[str] = None
    title: Optional[str] = None
    type: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self):
        return strip_none(asdict(self))

                    