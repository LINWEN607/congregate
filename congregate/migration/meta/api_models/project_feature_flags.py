from dataclasses import dataclass, asdict, field
from typing import Optional, List

@dataclass
class ProjectFeatureFlagPayload():
    name: str
    description: str
    active: bool
    strategies: Optional[List[dict]] = field(default_factory=list)
    version: str = "new_version_flag"  # Note this must be new_version_flag

    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v not in ["", [], None]}
