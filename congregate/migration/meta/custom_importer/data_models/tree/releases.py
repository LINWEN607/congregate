
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
    author_id: int
    created_at: str
    description: str
    links: list
    milestone_releases: list
    name: str
    project_id: int
    released_at: str
    sha: str
    tag: str
    updated_at: str

    def to_dict(self):
        return strip_none(asdict(self))
    
                    