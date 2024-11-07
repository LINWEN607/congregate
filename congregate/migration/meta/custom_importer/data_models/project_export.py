from dataclasses import dataclass
from typing import List

from congregate.migration.meta.custom_importer.data_models.approval_rules import ApprovalRules
from congregate.migration.meta.custom_importer.data_models.auto_devops import AutoDevops

from congregate.migration.meta.custom_importer.data_models.ci_cd_settings import CiCdSettings
from congregate.migration.meta.custom_importer.data_models.ci_pipelines import CiPipelines
from congregate.migration.meta.custom_importer.data_models.commit_notes import CommitNotes
from congregate.migration.meta.custom_importer.data_models.container_expiration_policy import ContainerExpirationPolicy
from congregate.migration.meta.custom_importer.data_models.issues import Issues
from congregate.migration.meta.custom_importer.data_models.labels import Labels
from congregate.migration.meta.custom_importer.data_models.merge_requests import MergeRequests
from congregate.migration.meta.custom_importer.data_models.project_features import ProjectFeatures
from congregate.migration.meta.custom_importer.data_models.project_members import ProjectMembers
from congregate.migration.meta.custom_importer.data_models.protected_branches import ProtectedBranches
from congregate.migration.meta.custom_importer.data_models.protected_tags import ProtectedTags
from congregate.migration.meta.custom_importer.data_models.push_rule import PushRule
from congregate.migration.meta.custom_importer.data_models.releases import Releases
from congregate.migration.meta.custom_importer.data_models.security_setting import SecuritySetting
from congregate.migration.meta.custom_importer.data_models.user_contributions import UserContributions

@dataclass
class ProjectExport:
    approval_rules: ApprovalRules
    auto_devops: AutoDevops
    ci_cd_settings: CiCdSettings
    ci_pipelines: List[CiPipelines]
    commit_notes: List[CommitNotes]
    container_expiration_policy: ContainerExpirationPolicy
    issues: List[Issues]
    labels: List[Labels]
    merge_requests: List[MergeRequests]
    project_features: ProjectFeatures
    project_members: List[ProjectMembers]
    protected_branches: List[ProtectedBranches]
    protected_tags: List[ProtectedTags]
    push_rule: PushRule
    releases: List[Releases]
    security_setting: SecuritySetting
    user_contributions: UserContributions