from io import BytesIO
from typing import Optional
from dataclasses import dataclass, asdict, astuple
from requests_toolbelt.multipart.encoder import MultipartEncoder
from gitlab_ps_utils.dict_utils import strip_none
from congregate.migration.meta.api_models.multipart_content import MultiPartContent

@dataclass
class PyPiPackageData:
    content: MultiPartContent
    name: str
    version: str
    requires_python: Optional[str] = ""
    md5_digest: Optional[str] = ""
    sha256_digest: Optional[str] = ""
    metadata_version: Optional[str] = ""
    author_email: Optional[str] = ""
    description: Optional[str] = ""
    description_content_type: Optional[str] = ""
    summary: Optional[str] = ""
    keywords: Optional[str] = ""

    def __post_init__(self):
        self.content = MultiPartContent(*self.content)

    def to_multipart_data(self):
        as_dict = strip_none(asdict(self))
        as_dict['content'] = astuple(self.content)
        return MultipartEncoder(fields=as_dict)
