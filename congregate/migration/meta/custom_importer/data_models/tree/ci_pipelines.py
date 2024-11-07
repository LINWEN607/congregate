
from dataclasses import dataclass, asdict
from gitlab_ps_utils.dict_utils import strip_none
                    

@dataclass
class CiPipelines:
    
    before_sha: str
    committed_at: str | None = None
    config_source: str
    created_at: str
    duration: int
    failure_reason: str | None = None
    finished_at: str
    iid: int
    lock_version: int
    merge_request: dict
    project_id: int
    protected: bool
    ref: str
    sha: str
    source: str
    source_sha: str | None = None
    stages: list
    started_at: str
    status: str
    tag: bool
    target_sha: str | None = None
    updated_at: str
    user_id: int
    yaml_errors: str | None = None

    def to_dict(self):
        return strip_none(asdict(self))

                    