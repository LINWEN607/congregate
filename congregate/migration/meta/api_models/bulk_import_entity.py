from dataclasses import dataclass
from typing import Optional

@dataclass
class BulkImportEntity:
    source_type: str
    source_full_path: str
    destination_slug: str
    destination_namespace: str
    destination_name: Optional[str] = None
    migrate_projects: Optional[bool] = True
    