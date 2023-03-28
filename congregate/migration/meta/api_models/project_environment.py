from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class NewProjectEnvironmentPayload():
    name: str
    external_url: Optional[str] = None
    tier: Optional[str] = None

    def to_dict(self):
        return { k:v for k, v in asdict(self).items() if v }
