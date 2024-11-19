from dataclasses import dataclass
from typing import Optional

@dataclass
class Author:
    name: str
    email: Optional[str] = None
