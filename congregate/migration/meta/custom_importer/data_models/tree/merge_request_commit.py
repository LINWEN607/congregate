from dataclasses import dataclass, asdict
from gitlab_ps_utils.dict_utils import strip_none

@dataclass
class MergeRequestCommit():
    relative_order: int
    new_file: bool
    renamed_file: bool
    deleted_file: bool
    too_large: bool
    a_mode: str
    b_mode: str
    new_path: str
    old_path: str
    binary: bool
    encoded_file_path: bool
    utf8_diff: str

    def to_dict(self):
        return strip_none(asdict)
