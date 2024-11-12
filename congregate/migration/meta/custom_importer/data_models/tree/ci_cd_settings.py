from typing import Optional
from dataclasses import dataclass, asdict
from gitlab_ps_utils.dict_utils import strip_none
                    
'''
{
    "default_git_depth": "<class 'int'>",
    "group_runners_enabled": "<class 'bool'>",
    "runner_token_expiration_interval": "<class 'NoneType'>"
}             
'''

@dataclass
class CiCdSettings:
    default_git_depth: Optional[int] = None
    group_runners_enabled: Optional[bool] = None
    runner_token_expiration_interval: Optional[int] = None

    def to_dict(self):
        return strip_none(asdict(self))

                    