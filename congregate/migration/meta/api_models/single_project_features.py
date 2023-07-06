from dataclasses import dataclass, asdict, field
from typing import Optional, List

from congregate.migration.meta.api_models.project_environment import NewProjectEnvironmentPayload
from congregate.migration.meta.api_models.variables import VariablePayload
from congregate.migration.meta.api_models.pipeline_schedule import PipelineSchedulePayload
from congregate.migration.meta.api_models.pipeline_schedule_variables import PipelineScheduleVariablePayload
from congregate.migration.meta.api_models.mr_level_approvers import MergeRequestLevelApproverPayload
from congregate.migration.meta.api_models.project_level_approvers import ProjectLevelApproverPayload
from congregate.migration.meta.api_models.project_details import ProjectDetails

@dataclass
class SingleProjectFeatures():
    id: int
    project_details: ProjectDetails
    project_environments: Optional[List[NewProjectEnvironmentPayload]] = field(default_factory=list)
    ci_variables: Optional[List[VariablePayload]] = field(default_factory=list)
    pipeline_schedules: Optional[List[PipelineSchedulePayload]] = field(default_factory=list)
    pipeline_schedule_variables: Optional[List[PipelineScheduleVariablePayload]] = field(default_factory=list)
    mr_approvers: Optional[List[MergeRequestLevelApproverPayload]] = field(default_factory=list)
    project_approvers: Optional[List[ProjectLevelApproverPayload]] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)
