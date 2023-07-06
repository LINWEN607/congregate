from dataclasses import dataclass, asdict

@dataclass
class PipelineScheduleVariablePayload():
    schedule_id: int
    key: str
    value: str
    variable_type: str
    
    def to_dict(self):
        return asdict(self)
