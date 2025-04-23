from typing import Optional
from dataclasses import dataclass, asdict
from gitlab_ps_utils.dict_utils import strip_none
                    

@dataclass
class NameSpaceSettings:
    '''
        Dataclass for importing any Namespace Settings
    '''
    prevent_sharing_groups_outside_hierarchy: Optional[str] = False

    def to_dict(self):
        return strip_none(asdict(self))
