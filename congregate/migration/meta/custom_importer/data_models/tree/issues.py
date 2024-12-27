from typing import Optional, List
from dataclasses import dataclass, asdict, field
from typing import Optional
from gitlab_ps_utils.dict_utils import strip_none
from congregate.migration.meta.custom_importer.data_models.tree.note import Note


@dataclass
class Issues:
    '''
        Dataclass for importing any issues/tickets from another source instance
    '''

    # Required
    title: str
    author_id: int
    project_id: int
    created_at: str
    description: str
    state: str
    iid: int
    notes: List[Note] = field(default_factory=list)

    # Optional and present in import_export.yml
    confidential: bool = False
    due_date: Optional[str] = None
    lock_version: Optional[int] = None
    weight: Optional[int] = None
    time_estimate: Optional[int] = None
    updated_at: Optional[str] = None
    updated_by_id: Optional[int] = None
    closed_at: Optional[str] = None
    closed_by_id: Optional[int] = None
    last_edited_at: Optional[str] = None
    last_edited_by_id: Optional[int] = None
    relative_position: Optional[int] = None

    # Optional and not present in import_export.yml
    award_emoji: Optional[List] = field(default_factory=list)
    design_versions: Optional[List] = field(default_factory=list)
    designs: Optional[List] = field(default_factory=list)
    discussion_locked: Optional[bool] = None
    epic_issue: Optional[dict]  = field(default_factory=dict)
    events: Optional[List] = field(default_factory=list)
    external_key: Optional[str] = None
    health_status: Optional[str] = None
    issue_assignees: Optional[List] = field(default_factory=list)
    label_links: Optional[List] = field(default_factory=list)
    resource_iteration_events: Optional[List] = field(default_factory=list)
    resource_label_events: Optional[List] = field(default_factory=list)
    resource_milestone_events: Optional[List] = field(default_factory=list)
    resource_state_events: Optional[List] = field(default_factory=list)
    timelogs: Optional[List] = field(default_factory=list)
    work_item_type: Optional[dict]  = field(default_factory=dict)
    zoom_meetings: Optional[List] = None

    def to_dict(self):
        return strip_none(asdict(self))

                    