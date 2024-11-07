
from dataclasses import dataclass, asdict
from gitlab_ps_utils.dict_utils import strip_none
                    
@dataclass
class Issues:
    author_id: int
    award_emoji: list
    closed_at: str | None = None
    closed_by_id: int | None = None
    confidential: bool
    created_at: str
    description: str
    design_versions: list
    designs: list
    discussion_locked: bool | None = None
    due_date: str | None = None
    epic_issue: dict
    events: list
    external_key: str | None = None
    health_status: str | None = None
    iid: int
    issue_assignees: list
    label_links: list
    last_edited_at: str | None = None
    last_edited_by_id: int | None = None
    lock_version: int
    notes: list
    project_id: int
    relative_position: int
    resource_iteration_events: list
    resource_label_events: list
    resource_milestone_events: list
    resource_state_events: list
    state: str
    time_estimate: int
    timelogs: list
    title: str
    updated_at: str
    updated_by_id: int | None = None
    weight: int | None = None
    work_item_type: dict
    zoom_meetings: list

    def to_dict(self):
        return strip_none(asdict(self))

                    