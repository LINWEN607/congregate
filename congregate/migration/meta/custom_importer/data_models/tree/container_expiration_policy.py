
from dataclasses import dataclass, asdict
from gitlab_ps_utils.dict_utils import strip_none
                    
'''
{
    "cadence": "<class 'str'>",
    "created_at": "<class 'str'>",
    "enabled": "<class 'bool'>",
    "keep_n": "<class 'int'>",
    "name_regex": "<class 'str'>",
    "name_regex_keep": "<class 'NoneType'>",
    "next_run_at": "<class 'str'>",
    "older_than": "<class 'str'>",
    "project_id": "<class 'int'>",
    "updated_at": "<class 'str'>"
}             
'''

@dataclass
class ContainerExpirationPolicy:
    cadence: str
    created_at: str
    enabled: bool
    keep_n: int
    name_regex: str
    name_regex_keep: str | None = None
    next_run_at: str
    older_than: str
    project_id: int
    updated_at: str

    def to_dict(self):
        return strip_none(asdict(self))

                    