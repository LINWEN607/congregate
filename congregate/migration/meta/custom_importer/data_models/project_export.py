from dataclasses import dataclass
from typing import List, Optional

from congregate.migration.meta.custom_importer.data_models.tree.approval_rules import ApprovalRules
from congregate.migration.meta.custom_importer.data_models.tree.auto_devops import AutoDevops

from congregate.migration.meta.custom_importer.data_models.tree.ci_cd_settings import CiCdSettings
from congregate.migration.meta.custom_importer.data_models.tree.ci_pipelines import CiPipelines
from congregate.migration.meta.custom_importer.data_models.tree.commit_notes import CommitNotes
from congregate.migration.meta.custom_importer.data_models.tree.container_expiration_policy import ContainerExpirationPolicy
from congregate.migration.meta.custom_importer.data_models.tree.issues import Issues
from congregate.migration.meta.custom_importer.data_models.tree.labels import Labels
from congregate.migration.meta.custom_importer.data_models.tree.merge_requests import MergeRequests
from congregate.migration.meta.custom_importer.data_models.tree.project_features import ProjectFeatures
from congregate.migration.meta.custom_importer.data_models.tree.project_members import ProjectMembers
from congregate.migration.meta.custom_importer.data_models.tree.protected_branches import ProtectedBranches
from congregate.migration.meta.custom_importer.data_models.tree.protected_tags import ProtectedTags
from congregate.migration.meta.custom_importer.data_models.tree.push_rule import PushRule
from congregate.migration.meta.custom_importer.data_models.tree.releases import Releases
from congregate.migration.meta.custom_importer.data_models.tree.security_setting import SecuritySetting
from congregate.migration.meta.custom_importer.data_models.tree.user_contributions import UserContributions

@dataclass
class ProjectExport:
    project_features: ProjectFeatures
    approval_rules: Optional[ApprovalRules] = None
    auto_devops: Optional[AutoDevops] = None
    ci_cd_settings: Optional[CiCdSettings] = None
    ci_pipelines: Optional[List[CiPipelines]] = []
    commit_notes: Optional[List[CommitNotes]] = []
    container_expiration_policy: Optional[ContainerExpirationPolicy] = None
    issues: Optional[List[Issues]] = []
    labels: Optional[List[Labels]] = []
    merge_requests: Optional[List[MergeRequests]] = []
    project_members: Optional[List[ProjectMembers]] = []
    protected_branches: Optional[List[ProtectedBranches]] = []
    protected_tags: Optional[List[ProtectedTags]] = []
    push_rule: Optional[PushRule] = None
    releases: Optional[List[Releases]] = None
    security_setting: Optional[SecuritySetting] = None
    user_contributions: Optional[UserContributions] = None