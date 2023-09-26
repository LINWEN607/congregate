from dataclasses import dataclass
from typing import Optional

@dataclass
class BulkImportEntity:
    source_type: str
    source_full_path: str
    destination_slug: str
    destination_name: str
    destination_namespace: str
    migrate_projects: Optional[bool] = True