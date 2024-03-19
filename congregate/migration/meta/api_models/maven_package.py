from io import BytesIO
from dataclasses import dataclass, asdict

@dataclass
class MavenPackage:
    content: BytesIO
    file_name: str

    def to_dict(self):
        return asdict(self)