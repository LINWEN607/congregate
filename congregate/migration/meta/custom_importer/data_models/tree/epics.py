from typing import Optional, List, Any
from dataclasses import dataclass, asdict, field
from gitlab_ps_utils.dict_utils import strip_none
from datetime import datetime
from congregate.migration.meta.custom_importer.data_models.tree.event import Event

@dataclass
class Epics:
    '''
        Dataclass for importing any epics
    '''
    id: Optional[int] = None
    group_id: Optional[int] = None
    author_id: Optional[int] = None
    iid: Optional[int] = None
    cached_markdown_version: Optional[int] = None
    updated_by_id: Optional[int] = None
    last_edited_by_id: Optional[int] = None
    lock_version: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    last_edited_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    title: Optional[str] = None
    title_html: Optional[str] = None
    description: Optional[str] = None
    description_html: Optional[str] = None
    start_date_sourcing_milestone_id: Optional[int] = None
    due_date_sourcing_milestone_id: Optional[int] = None
    start_date_fixed: Optional[str] = None
    due_date_fixed: Optional[str] = None
    start_date_is_fixed: Optional[bool] = None
    due_date_is_fixed: Optional[bool] = None
    closed_by_id: Optional[int] = None
    closed_at: Optional[str] = None
    parent_id: Optional[int] = None
    relative_position: Optional[int] = None
    start_date_sourcing_epic_id: Optional[int] = None
    due_date_sourcing_epic_id: Optional[int] = None
    confidential: Optional[bool] = None
    external_key: Optional[str] = None
    color: Optional[str] = None
    total_opened_issue_weight: Optional[int] = None
    total_closed_issue_weight: Optional[int] = None
    total_opened_issue_count: Optional[int] = None
    total_closed_issue_count: Optional[int] = None
    issue_id: Optional[int] = None
    imported: Optional[int] = None
    imported_from: Optional[str] = None
    work_item_parent_link_id: Optional[int] = None
    state: Optional[str] = None
    award_emoji: List[Any] = field(default_factory=list)
    events: List[Event] = field(default_factory=list)
    label_links: List[Any] = field(default_factory=list)
    notes: List[Any] = field(default_factory=list)
    resource_state_events: List[Any] = field(default_factory=list)

    def to_dict(self):
        return strip_none(asdict(self))
