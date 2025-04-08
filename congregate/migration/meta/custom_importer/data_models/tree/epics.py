from typing import Optional, List
from dataclasses import dataclass, asdict, field
from gitlab_ps_utils.dict_utils import strip_none
                    

@dataclass
class Epics:
    '''
        Dataclass for importing any epics
    '''
    created_at: Optional[str] = None

    def to_dict(self):
        return strip_none(asdict(self))
