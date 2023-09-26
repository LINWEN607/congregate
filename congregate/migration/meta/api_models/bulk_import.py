from dataclasses import dataclass
from typing import List
from congregate.migration.meta.api_models.bulk_import_configuration import BulkImportconfiguration
from congregate.migration.meta.api_models.bulk_import_entity import BulkImportEntity

@dataclass
class BulkImportPayload:
    configuration: BulkImportconfiguration
    entities: List[BulkImportEntity]