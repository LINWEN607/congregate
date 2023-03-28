from dataclasses import dataclass, asdict

@dataclass
class SharedWithGroupPayload():
    group_access: str
    group_id: int
    expires_at: str

    def to_dict(self):
        return asdict(self)
