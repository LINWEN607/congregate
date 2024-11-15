from dataclasses import dataclass, asdict, field
from typing import Optional, List
from congregate.migration.meta.custom_importer.data_models.tree.note_author import NoteAuthor
from congregate.migration.meta.custom_importer.data_models.tree.system_note_metadata import SystemNoteMetadata


@dataclass
class Note:
    note: str
    author: NoteAuthor
    noteable_type: str
    author_id: int
    created_at: str
    project_id: str
    updated_at: Optional[str] = None
    attachment: Optional[dict] = field(default_factory=dict)
    line_code: Optional[str] = None
    commit_id: Optional[str] = None
    st_diff: Optional[str] = None
    system: Optional[bool] = None
    updated_by_id: Optional[int] = None
    type: Optional[str] = None
    position: Optional[int] =None
    original_position: Optional[int] = None
    resolved_at: Optional[str] = None
    resolved_by_id: Optional[int] = None
    discussion_id: Optional[str] = None
    change_position: Optional[int] = None
    resolved_by_push: Optional[bool] = None
    confidential: Optional[bool] = None
    last_edited_at: Optional[str] = None
    award_emoji: Optional[List] = field(default_factory=list)
    system_note_metadata: Optional[SystemNoteMetadata] = field(default_factory=dict)
    events: Optional[List] = field(default_factory=list)

    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v is not None}