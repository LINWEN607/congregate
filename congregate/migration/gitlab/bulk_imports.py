from dataclasses import dataclass
from congregate.migration.gitlab.base_gitlab_client import BaseGitLabClient
from congregate.migration.gitlab.api.bulk_imports import BulkImportApi


class BulkImportsClient(BaseGitLabClient):
    def __init__(self, src_host=None, src_token=None, dest_host=None, dest_token=None):
        super().__init__(src_host=src_host, src_token=src_token,
                         dest_host=dest_host, dest_token=dest_token)
        self.bulk_import = BulkImportApi()


    def trigger_bulk_import(self):
        pass

    def check_import_status(self, id):
        pass

    def check_single_entity_status(self, id):
        pass

    # Trigger bulk import (group or project)
    # Check status of the import and its entities (celery tasks)
    # as entities finish up, run post migration tasks

    