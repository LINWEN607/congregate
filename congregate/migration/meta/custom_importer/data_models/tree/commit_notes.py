
from dataclasses import dataclass, asdict
from gitlab_ps_utils.dict_utils import strip_none
                    

@dataclass
class CommitNotes:
    attachment: list
    author: list
    author_id: int
    change_position: None | str
    commit_id: str
    confidential: None | bool
    created_at: str
    discussion_id: str
    events: list
    id: int
    imported_from: str
    internal: bool
    last_edited_at: str
    line_code: None | str
    note: str
    noteable_type: str
    original_position: None | str
    position: None | str
    project_id: int
    resolved_at: None | str
    resolved_by_id: None | int
    resolved_by_push: None | bool
    st_diff: None | str
    system: bool
    type: None | str
    updated_at: str
    updated_by_id: None | int

    def to_dict(self):
        return strip_none(asdict(self))

                    