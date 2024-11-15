from typing import Optional, List
from dataclasses import dataclass, asdict, field
from gitlab_ps_utils.dict_utils import strip_none
                    

@dataclass
class CiPipelines:
    
    before_sha: Optional[str] = None
    committed_at: Optional[str] = None
    config_source: Optional[str] = None
    created_at: Optional[str] = None
    duration: Optional[int] = None
    failure_reason: Optional[str] = None
    finished_at: Optional[str] = None
    iid: Optional[int] = None
    lock_version: Optional[int] = None
    merge_request: Optional[dict] = field(default_factory=dict)
    project_id: Optional[int] = None
    protected: Optional[bool] = None
    ref: Optional[str] = None
    sha: Optional[str] = None
    source: Optional[str] = None
    source_sha: Optional[str] = None
    stages: Optional[List[dict]] = field(default_factory=list)
    started_at: Optional[str] = None
    status: Optional[str] = None
    tag: Optional[bool] = None
    target_sha: Optional[str] = None
    updated_at: Optional[str] = None
    user_id: Optional[int] = None
    yaml_errors: Optional[str] = None

    def to_dict(self):
        return strip_none(asdict(self))

                    