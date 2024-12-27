from typing import Optional
from dataclasses import dataclass, asdict
from gitlab_ps_utils.dict_utils import strip_none
                    
@dataclass
class CiCdSettings:
    '''
        Dataclass for importing any CI/CD settings

        This dataclass is pretty GitLab-specific, but could be used when migrating CI/CD data
    '''
    default_git_depth: Optional[int] = None
    group_runners_enabled: Optional[bool] = None
    runner_token_expiration_interval: Optional[int] = None

    def to_dict(self):
        return strip_none(asdict(self))

                    