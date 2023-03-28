from dataclasses import dataclass
from typing import List, Optional

from congregate.migration.meta.api_models.project_environment import NewProjectEnvironmentPayload
from congregate.migration.meta.api_models.shared_with_group import SharedWithGroupPayload
from congregate.migration.meta.api_models.variables import VariablePayload

@dataclass
class SingleProjectFeatures():
    id: int
    project_environments: Optional[List[NewProjectEnvironmentPayload]] = []
    shared_with_groups: Optional[List[SharedWithGroupPayload]] = []
    variables: Optional[List[VariablePayload]] = []
