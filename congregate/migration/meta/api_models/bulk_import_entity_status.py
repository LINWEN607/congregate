from dataclasses import dataclass, asdict
from typing import Optional, List

@dataclass
class BulkImportEntityStatus:
    id: int
    bulk_import_id: int
    status: str
    entity_type: str
    source_full_path: str
    destination_full_path: str
    destination_name: str
    destination_slug: str
    destination_namespace: str
    parent_id: Optional[int]
    namespace_id: Optional[int]
    project_id: Optional[int]
    created_at: str
    updated_at: str
    failures: List[dict]

    def to_dict(self):
        return asdict(self)
