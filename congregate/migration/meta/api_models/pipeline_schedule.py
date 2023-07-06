from dataclasses import dataclass, asdict

@dataclass
class PipelineSchedulePayload():
    id: int
    description: str
    ref: str
    cron: str

    def to_dict(self):
        return asdict(self)
