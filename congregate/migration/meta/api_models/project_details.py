from dataclasses import dataclass, asdict, field
from typing import Optional, List


@dataclass
class ProjectDetails():
    id: int
    archived: bool
    name: str
    path: str
    path_with_namespace: str
    shared_runners_enabled: bool
    namespace: str
    description: str
    jobs_enabled: bool
    packages_enabled: bool
    http_url_to_repo: str
    default_branch: str
    visibility: str
    merge_requests_template: Optional[str] = None
    forked_from_project: Optional[dict]  = field(default_factory=dict)
    members: Optional[List[dict]] = field(default_factory=list)
    shared_with_groups: Optional[List[dict]] = field(default_factory=list)

    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v}
