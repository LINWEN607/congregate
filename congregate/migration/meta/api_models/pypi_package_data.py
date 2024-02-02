from io import BytesIO
from dataclasses import dataclass
from requests_toolbelt.multipart.encoder import MultipartEncoder

@dataclass
class PyPiPackageData:
    filename: str
    file: BytesIO
    package_name: str
    version: str

    def to_multipart_data(self):
        return MultipartEncoder(fields={
            "file": (self.filename, self.file),
            "name": self.package_name,
            "version": self.version
        })
