from dataclasses import dataclass

@dataclass
class ProjectMemberUser:
    id: int
    username: str
    public_email: str = None
