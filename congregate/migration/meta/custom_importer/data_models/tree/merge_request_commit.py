from dataclasses import dataclass, asdict
from typing import Optional
from gitlab_ps_utils.dict_utils import strip_none
from congregate.migration.meta.custom_importer.data_models.tree.author import Author

@dataclass
class MergeRequestCommit:
    authored_date: str
    committed_date: str
    relative_order: int
    sha: str
    message: str
    commit_author: Author
    committer: Author
    trailers: Optional[dict] = None

    def to_dict(self):
        return strip_none(asdict(self))
