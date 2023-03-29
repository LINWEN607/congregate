from dataclasses import dataclass, asdict
from typing import List, Optional

from congregate.migration.meta.api_models.variables import VariablePayload

@dataclass
class PipelineScheduleVariablesPayload():
    id: int
    variables: Optional[List[VariablePayload]] = []

    def to_dict(self):
        return asdict(self)