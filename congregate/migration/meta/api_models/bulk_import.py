from dataclasses import dataclass, asdict
from typing import List
from congregate.migration.meta.api_models.bulk_import_configuration import BulkImportconfiguration
from congregate.migration.meta.api_models.bulk_import_entity import BulkImportEntity

@dataclass
class BulkImportPayload:
    configuration: BulkImportconfiguration
    entities: List[BulkImportEntity]

    def to_dict(self):
        return strip_none(asdict(self))
    
def strip_none(source, dest=None):
    if not dest:
        dest = {}
    if isinstance(source, dict):
        for k, v in source.items():
            if v:
                if isinstance(v, dict):
                    dest[k] = strip_none(v)
                elif isinstance(v, list):
                    dest[k] = []
                    for e in v:
                        dest[k].append(strip_none(e))
                else:
                    dest[k] = v
        return dest
    return source