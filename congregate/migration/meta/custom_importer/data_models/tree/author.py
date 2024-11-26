from dataclasses import dataclass
from typing import Optional

@dataclass
class Author:
    '''
        Dataclass for handling any author reference

        This is currently used in Notes, Merge Requests, and Merge Request Commits
    '''
    name: str
    email: Optional[str] = None
