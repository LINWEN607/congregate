from typing import Optional, List
from dataclasses import dataclass, asdict, field
from gitlab_ps_utils.dict_utils import strip_none
                    
@dataclass
class Releases:
    author_id: Optional[int] = None
    created_at: Optional[str] = None
    description: Optional[str] = None
    links: Optional[List] = field(default_factory=[])
    milestone_releases: Optional[List] = field(default_factory=[])
    name: Optional[str] = None
    project_id: Optional[int] = None
    released_at: Optional[str] = None
    sha: Optional[str] = None
    tag: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self):
        return strip_none(asdict(self))
    
                    