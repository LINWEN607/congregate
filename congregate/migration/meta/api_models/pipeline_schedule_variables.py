from dataclasses import dataclass, asdict, field
from typing import Optional, List

from congregate.migration.meta.api_models.variables import VariablePayload

@dataclass
class PipelineScheduleVariablesPayload():
    id: int
    variables: Optional[List[VariablePayload]] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)
