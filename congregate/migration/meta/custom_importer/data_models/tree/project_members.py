from typing import Optional
from dataclasses import dataclass, asdict
from gitlab_ps_utils.dict_utils import strip_none
                    
'''
{
    "access_level": "<class 'int'>",
    "created_at": "<class 'str'>",
    "created_by_id": "<class 'int'>",
    "expires_at": "<class 'NoneType'>",
    "invite_accepted_at": "<class 'NoneType'>",
    "invite_email": "<class 'NoneType'>",
    "ldap": "<class 'bool'>",
    "notification_level": "<class 'int'>",
    "override": "<class 'bool'>",
    "requested_at": "<class 'NoneType'>",
    "source_type": "<class 'str'>",
    "updated_at": "<class 'str'>",
    "user": [
        "id",
        "username",
        "public_email"
    ],
    "user_id": "<class 'int'>"
}             
'''

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
    user: Optional[dict] = {}
    user_id: Optional[int] = None

    def to_dict(self):
        return strip_none(asdict(self))

                    