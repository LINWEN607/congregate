from dataclasses import dataclass, asdict
from typing import List
from gitlab_ps_utils.dict_utils import strip_none
from congregate.migration.meta.api_models.bulk_import_configuration import BulkImportconfiguration
from congregate.migration.meta.api_models.bulk_import_entity import BulkImportEntity

@dataclass
class BulkImportPayload:
    configuration: BulkImportconfiguration
    entities: List[BulkImportEntity]

    def to_dict(self):
        return strip_none(asdict(self))
