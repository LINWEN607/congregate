"""
    Congregate - GitLab instance migration utility

    Copyright (c) 2023 - GitLab
"""

from congregate.helpers.base_class import BaseClass
from congregate.migration.gitlab.api.projects import ProjectsApi
from congregate.migration.gitlab.api.project_repository import ProjectRepositoryApi
from congregate.migration.gitlab.variables import VariablesClient

class BaseExternalCiClient(BaseClass):
    ci_source = None

    def __init__(self):
        super().__init__()
        self.projects_api = ProjectsApi()
        self.project_repository_api = ProjectRepositoryApi()
        self.variables = VariablesClient()

    def migrate_variables(self, project, new_id, ci_src_hostname):
        raise NotImplementedError
    
    def migrate_build_configuration(self, project, project_id):
        raise NotImplementedError

    def retrieve_jobs_with_scm_info(self, i, processes=None):
        raise NotImplementedError

    def transform_ci_variables(self, parameter, ci_src_hostname):
        raise NotImplementedError
    