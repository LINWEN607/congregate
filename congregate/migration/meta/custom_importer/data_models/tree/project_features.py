from typing import Optional
from dataclasses import dataclass, asdict

@dataclass
class ProjectFeatures:
    '''
        Dataclass covering any GitLab-specific project features

        This is fairly GitLab-specific, but if the source instance has similar settings,
        use this dataclass to translate them into the GitLab project
    '''

    analytics_access_level: Optional[int] = None
    builds_access_level: Optional[int] = None
    container_registry_access_level: Optional[int] = None
    created_at: Optional[str] = None
    environments_access_level: Optional[int] = None
    feature_flags_access_level: Optional[int] = None
    forking_access_level: Optional[int] = None
    infrastructure_access_level: Optional[int] = None
    issues_access_level: Optional[int] = None
    merge_requests_access_level: Optional[int] = None
    metrics_dashboard_access_level: Optional[int] = None
    model_experiments_access_level: Optional[int] = None
    model_registry_access_level: Optional[int] = None
    monitor_access_level: Optional[int] = None
    operations_access_level: Optional[int] = None
    package_registry_access_level: Optional[int] = None
    pages_access_level: Optional[int] = None
    project_id: Optional[int] = None
    releases_access_level: Optional[int] = None
    repository_access_level: Optional[int] = None
    requirements_access_level: Optional[int] = None
    security_and_compliance_access_level: Optional[int] = None
    snippets_access_level: Optional[int] = None
    updated_at: Optional[str] = None
    wiki_access_level: Optional[int] = None

    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v is not None}
