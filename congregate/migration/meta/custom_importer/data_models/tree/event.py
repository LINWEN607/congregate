from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict, field
from gitlab_ps_utils.dict_utils import strip_none
from datetime import datetime


@dataclass
class Event:
    '''
        Dataclass representing an event.
    '''
    project_id: Optional[int] = None
    author_id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    target_type: Optional[str] = None
    group_id: Optional[int] = None
    fingerprint: Optional[str] = None
    id: Optional[int] = None
    target_id: Optional[int] = None
    imported_from: Optional[str] = None
    personal_namespace_id: Optional[int] = None
    action: Optional[str] = None

    def to_dict(self):
        return strip_none(asdict(self))
