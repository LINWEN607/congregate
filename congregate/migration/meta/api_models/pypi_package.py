from io import BytesIO
from dataclasses import dataclass, asdict

@dataclass
class PyPiPackage:
    content: BytesIO
    file_name: str
    sha256_digest: str
    md5_digest: str

    def to_dict(self):
        return asdict(self)