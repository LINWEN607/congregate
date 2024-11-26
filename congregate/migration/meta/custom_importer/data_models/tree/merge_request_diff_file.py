from dataclasses import dataclass, asdict
from gitlab_ps_utils.dict_utils import strip_none

@dataclass
class MergeRequestDiffFile:
    '''
        Dataclass for importing any merge/pull request diffs from another source instance

        This is a subset of the MergeRequestDiff Dataclass and is needed for displaying diffs in the UI
        You only need the overall diffs for this dataclass, not a diff per commit in the MR
    '''
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
