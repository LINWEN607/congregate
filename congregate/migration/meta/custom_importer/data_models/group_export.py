from dataclasses import dataclass
from typing import Optional

from congregate.migration.meta.custom_importer.data_models.tree.namespace_settings import NameSpaceSettings

@dataclass
class GroupExport:
    '''
        Main dataclass for building out the content in the group tree folder

        This will pull all the data together and eventually turn into several ndjson files
    '''
    namespace_settings: Optional[NameSpaceSettings]