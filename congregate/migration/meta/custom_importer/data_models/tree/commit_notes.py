from typing import Optional, List
from dataclasses import dataclass, asdict, field
from gitlab_ps_utils.dict_utils import strip_none
                    

@dataclass
class CommitNotes:
    '''
        Dataclass for importing any commit notes from another source instance

        Commit notes are any comments applied to a specific commit.
    '''

    attachment: Optional[List] = field(default_factory=list)
    author: Optional[List] = field(default_factory=list)
    author_id: Optional[int] = None
    change_position: Optional[str] = None
    commit_id: Optional[str] = None
    confidential: Optional[bool] = None
    created_at: Optional[str] = None
    discussion_id: Optional[str] = None
    events: Optional[List] = field(default_factory=list)
    id: Optional[int] = None
    imported_from: Optional[str] = None
    internal: Optional[bool] = None
    last_edited_at: Optional[str] = None
    line_code: Optional[str] = None
    note: Optional[str] = None
    noteable_type: Optional[str] = None
    original_position: Optional[str] = None
    position: Optional[str] = None
    project_id: Optional[int] = None
    resolved_at: Optional[str] = None
    resolved_by_id: Optional[int] = None
    resolved_by_push: Optional[bool] = None
    st_diff: Optional[str] = None
    system: Optional[bool] = None
    type: Optional[str] = None
    updated_at: Optional[str] = None
    updated_by_id: Optional[int] = None

    def to_dict(self):
        return strip_none(asdict(self))

                    