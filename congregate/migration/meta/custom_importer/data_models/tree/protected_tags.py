from typing import Optional, List
from dataclasses import dataclass, asdict, field
from gitlab_ps_utils.dict_utils import strip_none
                    
@dataclass
class ProtectedTags:
    create_access_levels: Optional[List] = field(default_factory=[])
    created_at: Optional[str] = None
    name: Optional[str] = None
    project_id: Optional[int] = None
    updated_at: Optional[str] = None

    def to_dict(self):
        return strip_none(asdict(self))
                    