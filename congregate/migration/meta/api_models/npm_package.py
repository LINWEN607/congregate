from io import BytesIO
from dataclasses import dataclass, asdict

@dataclass
class NpmPackage:
    content: BytesIO
    file_name: str
    md5_digest: str

    def to_dict(self):
        return asdict(self)