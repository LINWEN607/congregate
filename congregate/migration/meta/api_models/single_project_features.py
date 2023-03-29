from dataclasses import dataclass, asdict, field
from typing import Optional, List

from congregate.migration.meta.api_models.project_environment import NewProjectEnvironmentPayload
from congregate.migration.meta.api_models.shared_with_group import SharedWithGroupPayload
from congregate.migration.meta.api_models.variables import VariablePayload
from congregate.migration.meta.api_models.pipeline_schedule_variables import PipelineScheduleVariablesPayload
from congregate.migration.meta.api_models.mr_approvers import MergeRequestApproverPayload

@dataclass
class SingleProjectFeatures():
    id: int
    project_environments: Optional[List[NewProjectEnvironmentPayload]] = field(default_factory=list)
    ci_variables: Optional[List[VariablePayload]] = field(default_factory=list)
    pipeline_schedule_variables: Optional[List[PipelineScheduleVariablesPayload]] = field(default_factory=list)
    mr_approvers: Optional[List[MergeRequestApproverPayload]] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)
