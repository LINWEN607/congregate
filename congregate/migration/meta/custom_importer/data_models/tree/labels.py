from typing import Optional
from dataclasses import dataclass, asdict, field
from gitlab_ps_utils.dict_utils import strip_none
                    
@dataclass
class Labels:
    '''
        Dataclass for importing any labels from another source instance
    '''
    color: Optional[str] = None
    created_at: Optional[str] = None
    description: Optional[str] = None
    group_id: Optional[int] = None
    priorities: Optional[list] = field(default_factory=list)
    project_id: Optional[int] = None
    template: Optional[bool] = None
    textColor: Optional[str] = None
    title: Optional[str] = None
    type: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self):
        return strip_none(asdict(self))

                    