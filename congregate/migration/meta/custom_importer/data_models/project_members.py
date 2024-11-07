
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
    
    access_level: int
    created_at: str
    created_by_id: int
    expires_at: str | None = None
    invite_accepted_at: str | None = None
    invite_email: str | None = None
    ldap: bool
    notification_level: int
    override: bool
    requested_at: str | None = None
    source_type: str
    updated_at: str
    user: dict
    user_id: int

    def to_dict(self):
        return strip_none(asdict(self))

                    