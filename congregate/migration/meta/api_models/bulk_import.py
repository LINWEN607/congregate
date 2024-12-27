from dataclasses import dataclass, asdict
from typing import List
from gitlab_ps_utils.dict_utils import strip_none
from congregate.migration.meta.api_models.bulk_import_configuration import BulkImportConfiguration
from congregate.migration.meta.api_models.bulk_import_entity import BulkImportEntity


@dataclass
class BulkImportPayload:
    configuration: BulkImportConfiguration
    entities: List[BulkImportEntity]

    def to_dict(self):
        """
            Returns the dataclass as dictionary with all the values set to None
            stripped out to make sure we send a clean API request and avoid any
            possible validation errors when making the direct transfer request
        """
        return strip_none(asdict(self))
