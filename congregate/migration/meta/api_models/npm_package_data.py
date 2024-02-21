import json
from dataclasses import dataclass, field, asdict, astuple
from typing import Union, Any, List, Dict, Optional
from requests_toolbelt.multipart.encoder import MultipartEncoder
from gitlab_ps_utils.dict_utils import strip_none
from congregate.migration.meta.api_models.multipart_content import MultiPartContent

@dataclass
class Repository:
    type: Optional[str] = ""
    url: str = ""
    directory: Optional[str] = ""

RepositoryType = Union[Repository, str, Dict[str, Any]]

@dataclass
class NpmPackageData:
    content: MultiPartContent
    name: str
    version: str
    description: Optional[str] = ""

    def __post_init__(self):
        if type(self.content) is tuple:
            self.content = MultiPartContent(*self.content)
