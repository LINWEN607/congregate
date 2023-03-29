from dataclasses import dataclass, asdict
from typing import List, Optional

from congregate.migration.meta.api_models.project_environment import NewProjectEnvironmentPayload
from congregate.migration.meta.api_models.shared_with_group import SharedWithGroupPayload
from congregate.migration.meta.api_models.variables import VariablePayload
from congregate.migration.meta.api_models.pipeline_schedule_variables import PipelineScheduleVariablesPayload
from congregate.migration.meta.api_models.mr_approvers import MergeRequestApproverPayload

@dataclass
class SingleProjectFeatures():
    id: int
    project_environments: Optional[List[NewProjectEnvironmentPayload]] = []
    shared_with_groups: Optional[List[SharedWithGroupPayload]] = []
    ci_variables: Optional[List[VariablePayload]] = []
    pipeline_schedule_variables: Optional[List[PipelineScheduleVariablesPayload]] = []
    mr_approvers: Optional[List[MergeRequestApproverPayload]] = []

    def to_dict(self):
        return asdict(self)
