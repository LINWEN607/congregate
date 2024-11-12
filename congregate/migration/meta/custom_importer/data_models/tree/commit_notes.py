from typing import Optional
from dataclasses import dataclass, asdict
from gitlab_ps_utils.dict_utils import strip_none
                    

@dataclass
class CommitNotes:
    attachment: Optional[list] = []
    author: Optional[list] = []
    author_id: Optional[int] = None
    change_position: None | str
    commit_id: Optional[str] = None
    confidential: None | bool
    created_at: Optional[str] = None
    discussion_id: Optional[str] = None
    events: Optional[list] = []
    id: Optional[int] = None
    imported_from: Optional[str] = None
    internal: Optional[bool] = None
    last_edited_at: Optional[str] = None
    line_code: None | str
    note: Optional[str] = None
    noteable_type: Optional[str] = None
    original_position: None | str
    position: None | str
    project_id: Optional[int] = None
    resolved_at: None | str
    resolved_by_id: None | int
    resolved_by_push: None | bool
    st_diff: None | str
    system: Optional[bool] = None
    type: None | str
    updated_at: Optional[str] = None
    updated_by_id: None | int

    def to_dict(self):
        return strip_none(asdict(self))

                    