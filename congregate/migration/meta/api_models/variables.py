from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class VariablePayload():
    key: str
    value: str
    variables_type: Optional[str] = None
    protected: Optional[bool] = False
    masked: Optional[bool] = False
    raw: Optional[bool] = False
    environment_scope: Optional[str] = '*'

    def to_dict(self):
        return { k:v for k, v in asdict(self).items() if v }
