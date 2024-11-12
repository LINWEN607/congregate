from typing import Optional
from dataclasses import dataclass, asdict
from gitlab_ps_utils.dict_utils import strip_none
                    

@dataclass
class Boards:
    created_at: Optional[str] = None
    group_id: Optional[int] = None
    hide_backlog_list: Optional[bool] = None
    hide_closed_list: Optional[bool] = None
    lists: Optional[list] = []
    name: Optional[str] = None
    project_id: Optional[int] = None
    updated_at: Optional[str] = None
    weight: Optional[int] = None

    def to_dict(self):
        return strip_none(asdict(self))

                    