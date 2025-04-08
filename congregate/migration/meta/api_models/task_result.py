import json
from dataclasses import dataclass, asdict
from typing import List, Optional, Any, Dict
from dacite import from_dict


@dataclass
class TaskResult:
    """Data class for post-migration task results"""
    id: int
    shared_with_groups: Any = False
    environments: Any = False
    cicd_variables: Any = False
    pipeline_schedule_variables: Any = False
    deploy_keys: Any = False
    container_registry: Optional[Any] = None
    package_registry: List[Any] = None
    project_hooks: Any = False
    project_feature_flags: Any = False
    project_feature_flags_users_lists: Optional[Any] = None
    src_id: Optional[int] = None
    src_path: str = ""
    src_url: str = ""

    def __post_init__(self):
        """Initialize default values for list/dict fields"""
        if self.package_registry is None:
            self.package_registry = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation for JSON serialization"""
        return asdict(self)

    @classmethod
    def from_json(cls, json_str: str) -> 'TaskResult':
        """Create TaskResult object from JSON string"""
        try:
            data = json.loads(json_str)
            return from_dict(data_class=cls, data=data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON data: {e}")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskResult':
        """Create TaskResult object from dictionary"""
        return from_dict(data_class=cls, data=data)