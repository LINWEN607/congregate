
from dataclasses import dataclass, asdict
from gitlab_ps_utils.dict_utils import strip_none
                    

@dataclass
class Boards:
    created_at: str
    group_id: int | None = None
    hide_backlog_list: bool
    hide_closed_list: bool
    lists: list
    name: str
    project_id: int
    updated_at: str
    weight: int | None = None

    def to_dict(self):
        return strip_none(asdict(self))

                    