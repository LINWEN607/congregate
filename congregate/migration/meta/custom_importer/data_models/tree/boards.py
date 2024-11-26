from typing import Optional, List
from dataclasses import dataclass, asdict, field
from gitlab_ps_utils.dict_utils import strip_none
                    

@dataclass
class Boards:
    '''
        Dataclass for importing any issues boards
    '''
    created_at: Optional[str] = None
    group_id: Optional[int] = None
    hide_backlog_list: Optional[bool] = None
    hide_closed_list: Optional[bool] = None
    lists: Optional[List] = field(default_factory=list)
    name: Optional[str] = None
    project_id: Optional[int] = None
    updated_at: Optional[str] = None
    weight: Optional[int] = None

    def to_dict(self):
        return strip_none(asdict(self))

                    