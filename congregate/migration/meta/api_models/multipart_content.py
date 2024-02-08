from io import BytesIO
from dataclasses import dataclass

@dataclass
class MultiPartContent:
    file_name: str
    content: BytesIO
    content_type: str
