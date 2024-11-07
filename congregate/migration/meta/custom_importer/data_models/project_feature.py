
from dataclasses import dataclass, asdict
from gitlab_ps_utils.dict_utils import strip_none
                    
'''
{
    "analytics_access_level": "<class 'int'>",
    "builds_access_level": "<class 'int'>",
    "container_registry_access_level": "<class 'int'>",
    "created_at": "<class 'str'>",
    "environments_access_level": "<class 'int'>",
    "feature_flags_access_level": "<class 'int'>",
    "forking_access_level": "<class 'int'>",
    "infrastructure_access_level": "<class 'int'>",
    "issues_access_level": "<class 'int'>",
    "merge_requests_access_level": "<class 'int'>",
    "metrics_dashboard_access_level": "<class 'int'>",
    "model_experiments_access_level": "<class 'int'>",
    "model_registry_access_level": "<class 'int'>",
    "monitor_access_level": "<class 'int'>",
    "operations_access_level": "<class 'int'>",
    "package_registry_access_level": "<class 'int'>",
    "pages_access_level": "<class 'int'>",
    "project_id": "<class 'int'>",
    "releases_access_level": "<class 'int'>",
    "repository_access_level": "<class 'int'>",
    "requirements_access_level": "<class 'int'>",
    "security_and_compliance_access_level": "<class 'int'>",
    "snippets_access_level": "<class 'int'>",
    "updated_at": "<class 'str'>",
    "wiki_access_level": "<class 'int'>"
}             
'''

@dataclass
class ProjectFeature:
    pass
                    