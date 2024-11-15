from typing import Optional
from dataclasses import dataclass, asdict, field
from gitlab_ps_utils.dict_utils import strip_none
                    
@dataclass
class ProjectMembers:
    
    access_level: Optional[int] = None
    created_at: Optional[str] = None
    created_by_id: Optional[int] = None
    expires_at: Optional[str] = None
    invite_accepted_at: Optional[str] = None
    invite_email: Optional[str] = None
    ldap: Optional[bool] = None
    notification_level: Optional[int] = None
    override: Optional[bool] = None
    requested_at: Optional[str] = None
    source_type: Optional[str] = None
    updated_at: Optional[str] = None
    user: Optional[dict] = field(default_factory=dict)
    user_id: Optional[int] = None

    def to_dict(self):
        return strip_none(asdict(self))

                    