from dataclasses import dataclass, asdict

@dataclass
class ProjectDetails():
    id: int
    archived: bool
    name: str
    path: str
    path_with_namespace: str
    shared_runners_enabled: bool
    namespace: dict

    def to_dict(self):
        return { k:v for k, v in asdict(self).items() if v }
