from dataclasses import dataclass, asdict

@dataclass
class JobTaskResponse():
    id: str
    name: str
    status: str

    def to_dict(self):
        return asdict(self)


