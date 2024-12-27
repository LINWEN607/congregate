from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class SystemNoteMetadata:
    '''
        Dataclass for any additional metadata associated with a note

        commit_count is only needed for merge requests

        optional actions are:
        - approvals_reset
        - approved
        - assignee
        - branch
        - commit
        - cross_reference
        - description
        - designs_added
        - designs_removed
        - discussion
        - locked
        - merge
        - outdated
        - relate
        - relate_to_child
        - relate_to_parent
        - reviewer
        - task
        - title
        - unlocked
        - unrelate
    '''
    
    commit_count: Optional[int] = None
    action: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v is not None}
