from typing import Optional
from dataclasses import dataclass, asdict
from typing import Optional
from gitlab_ps_utils.dict_utils import strip_none
                    
@dataclass
class Issues:
    author_id: Optional[int] = None
    award_emoji: Optional[list] = []
    closed_at: Optional[str] = None
    closed_by_id: Optional[int] = None
    confidential: Optional[bool] = None
    created_at: Optional[str] = None
    description: Optional[str] = None
    design_versions: Optional[list] = []
    designs: Optional[list] = []
    discussion_locked: Optional[bool] = None
    due_date: Optional[str] = None
    epic_issue: Optional[dict] = {}
    events: Optional[list] = []
    external_key: Optional[str] = None
    health_status: Optional[str] = None
    iid: Optional[int] = None
    issue_assignees: Optional[list] = []
    label_links: Optional[list] = []
    last_edited_at: Optional[str] = None
    last_edited_by_id: Optional[int] = None
    lock_version: Optional[int] = None
    notes: Optional[list] = []
    project_id: Optional[int] = None
    relative_position: Optional[int] = None
    resource_iteration_events: Optional[list] = []
    resource_label_events: Optional[list] = []
    resource_milestone_events: Optional[list] = []
    resource_state_events: Optional[list] = []
    state: Optional[str] = None
    time_estimate: Optional[int] = None
    timelogs: Optional[list] = []
    title: Optional[str] = None
    updated_at: Optional[str] = None
    updated_by_id: Optional[int] = None
    weight: Optional[int] = None
    work_item_type: Optional[dict] = {}
    zoom_meetings: Optional[list] = None

    def to_dict(self):
        return strip_none(asdict(self))

                    