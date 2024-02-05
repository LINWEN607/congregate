from io import BytesIO
from dataclasses import dataclass
from requests_toolbelt.multipart.encoder import MultipartEncoder

@dataclass
class PyPiPackageData:
    content: BytesIO
    package_name: str
    version: str

    def to_multipart_data(self):
        return MultipartEncoder(fields={
            "content": self.content,
            "name": self.package_name,
            "version": self.version
        })
