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
    main: Optional[str] = ""
    scripts: Optional[Dict[str, str]] = field(default_factory=dict)
    repository: Optional[RepositoryType] = None
    keywords: Optional[List[str]] = field(default_factory=list)
    author: Optional[str] = ""
    license: Optional[str] = ""
    dependencies: Optional[Dict[str, str]] = field(default_factory=dict)
    devDependencies: Optional[Dict[str, str]] = field(default_factory=dict)

    def __post_init__(self):
        if isinstance(self.repository, dict):
            # If repository is given as a dict, convert it to a Repository object
            self.repository = Repository(**self.repository)
        elif isinstance(self.repository, str):
            # If repository is a string, directly use the string as the URL in a Repository object
            self.repository = Repository(url=self.repository)
        if type(self.content) is tuple:
            self.content = MultiPartContent(*self.content)

    def transform_to_multipart(self):
        # Convert dataclass to dictionary (excluding 'content' because it needs special handling)
        data_dict = {k: v for k, v in asdict(self).items() if k != 'content' and v is not None}

        # Prepare files for multipart encoding
        files = {'file': (self.content.file_name, self.content.content)}

        # Prepare other data as 'data' for multipart encoding
        # Convert complex objects (like lists or dictionaries) to JSON strings
        multipart_data = {}
        for key, value in data_dict.items():
            if isinstance(value, (list, dict)):
                # Convert list or dict to string for multipart form
                value = json.dumps(value)
            multipart_data[key] = value 

        return files, multipart_data
