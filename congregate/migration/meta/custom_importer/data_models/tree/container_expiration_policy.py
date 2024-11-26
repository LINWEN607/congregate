from typing import Optional
from dataclasses import dataclass, asdict
from gitlab_ps_utils.dict_utils import strip_none

@dataclass
class ContainerExpirationPolicy:
    '''
        Dataclass for importing any container expiration policies from another source instance

        This dataclass is only applicable when migrating container registry data from a system
        that uses an existing container registry with an expiration policy
    '''
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

                    