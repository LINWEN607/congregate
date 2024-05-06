from dataclasses import dataclass, asdict, field
from typing import Optional, List

@dataclass
class ProjectFeatureFlagsUserListsPayload():
    id: int
    iid: int
    name: str
    user_xids: str

    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v not in ["", [], None]}
