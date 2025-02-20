from dataclasses import dataclass, asdict
from typing import Optional
from gitlab_ps_utils.dict_utils import strip_none

@dataclass
class NewMember:
    user_id: int
    access_level: int
    # Empty string can return as invalid on older GitLab versions
    # expires_at: Optional[str] = ""
    invite_source: Optional[str] = ""

    def to_dict(self):
        """
            Returns the dataclass as dictionary with all the values set to None
            stripped out to make sure we send a clean API request and avoid any
            possible validation errors when making the direct transfer request
        """
        return strip_none(asdict(self))
