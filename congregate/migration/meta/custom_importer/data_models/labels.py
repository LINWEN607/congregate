
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
    
    color: str
    created_at: str
    description: str
    group_id: int | None = None
    priorities: list
    project_id: int
    template: bool
    textColor: str
    title: str
    type: str
    updated_at: str

    def to_dict(self):
        return strip_none(asdict(self))

                    