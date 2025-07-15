from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
from gitlab_ps_utils.dict_utils import strip_none

from congregate.migration.meta.custom_importer.data_models.tree.namespace_settings import NameSpaceSettings
from congregate.migration.meta.custom_importer.data_models.tree.epics import Epics

@dataclass
class GroupExport:
    '''
        Main dataclass for building out the content in the group tree folder

        This will pull all the data together and eventually turn into several ndjson files
    '''
    namespace_settings: Optional[NameSpaceSettings]
    epics: Optional[List[Epics]] = None
