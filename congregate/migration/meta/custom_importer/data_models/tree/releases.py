from typing import Optional
from dataclasses import dataclass, asdict
from gitlab_ps_utils.dict_utils import strip_none
                    
'''
{
    "author_id": "<class 'int'>",
    "created_at": "<class 'str'>",
    "description": "<class 'str'>",
    "links": "<class 'list'>",
    "milestone_releases": "<class 'list'>",
    "name": "<class 'str'>",
    "project_id": "<class 'int'>",
    "released_at": "<class 'str'>",
    "sha": "<class 'str'>",
    "tag": "<class 'str'>",
    "updated_at": "<class 'str'>"
}             
'''

@dataclass
class Releases:
    author_id: Optional[int] = None
    created_at: Optional[str] = None
    description: Optional[str] = None
    links: Optional[list] = []
    milestone_releases: Optional[list] = []
    name: Optional[str] = None
    project_id: Optional[int] = None
    released_at: Optional[str] = None
    sha: Optional[str] = None
    tag: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self):
        return strip_none(asdict(self))
    
                    