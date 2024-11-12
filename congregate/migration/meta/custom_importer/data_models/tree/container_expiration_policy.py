from typing import Optional
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
    cadence: Optional[str] = None
    created_at: Optional[str] = None
    enabled: Optional[bool] = None
    keep_n: Optional[int] = None
    name_regex: Optional[str] = None
    name_regex_keep: Optional[str] = None
    next_run_at: Optional[str] = None
    older_than: Optional[str] = None
    project_id: Optional[int] = None
    updated_at: Optional[str] = None

    def to_dict(self):
        return strip_none(asdict(self))

                    