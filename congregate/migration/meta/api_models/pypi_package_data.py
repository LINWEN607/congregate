from io import BytesIO
from dataclasses import dataclass
from requests_toolbelt.multipart.encoder import MultipartEncoder
from congregate.helpers.utils import guess_file_type

@dataclass
class PyPiPackageData:
    content: BytesIO
    file_name: str
    package_name: str
    version: str

    def to_multipart_data(self):
        return MultipartEncoder(fields={
            "content": (self.file_name, self.content, guess_file_type(self.file_name)),
            "name": self.package_name,
            "version": self.version
        })
