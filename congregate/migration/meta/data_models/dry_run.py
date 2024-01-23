from dataclasses import dataclass, asdict, field
from typing import List
from gitlab_ps_utils.dict_utils import strip_none
from congregate.migration.meta.api_models.bulk_import_configuration import BulkImportconfiguration
from congregate.migration.meta.api_models.bulk_import_entity import BulkImportEntity

@dataclass
class DryRunData:
    top_level_group: str = ""
    entity: BulkImportEntity = None
    projects: List[str] = field(default_factory=list)
    subgroups: List[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)
