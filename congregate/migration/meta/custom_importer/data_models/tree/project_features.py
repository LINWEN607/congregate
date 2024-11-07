from dataclasses import dataclass, asdict

@dataclass
class ProjectFeatures:
    analytics_access_level: int
    builds_access_level: int
    container_registry_access_level: int
    created_at: str
    environments_access_level: int
    feature_flags_access_level: int
    forking_access_level: int
    infrastructure_access_level: int
    issues_access_level: int
    merge_requests_access_level: int
    metrics_dashboard_access_level: int
    model_experiments_access_level: int
    model_registry_access_level: int
    monitor_access_level: int
    operations_access_level: int
    package_registry_access_level: int
    pages_access_level: int
    project_id: int
    releases_access_level: int
    repository_access_level: int
    requirements_access_level: int
    security_and_compliance_access_level: int
    snippets_access_level: int
    updated_at: str
    wiki_access_level: int

    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v is not None}
