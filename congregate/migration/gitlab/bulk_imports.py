from time import sleep
from dacite import from_dict
from gitlab_ps_utils.misc_utils import safe_json_response
from congregate.migration.gitlab.base_gitlab_client import BaseGitLabClient
from congregate.migration.gitlab.api.bulk_imports import BulkImportApi
from congregate.migration.meta.api_models.bulk_import import BulkImportPayload
from congregate.migration.meta.api_models.bulk_import_entity_status import BulkImportEntityStatus

class BulkImportsClient(BaseGitLabClient):
    def __init__(self, src_host=None, src_token=None, dest_host=None, dest_token=None):
        super().__init__(src_host=src_host, src_token=src_token,
                         dest_host=dest_host, dest_token=dest_token)
        self.bulk_import = BulkImportApi()


    def trigger_bulk_import(self, payload: BulkImportPayload):
        if import_request := safe_json_response(
            self.bulk_import.start_new_bulk_import(self.dest_host, self.dest_token, payload.to_dict())):
            self.log.info("Successfully triggered bulk import request")
            return list(self.bulk_import.get_bulk_import_entities(self.dest_host, self.dest_token, import_request.get('id')))

    def poll_import_status(self, id):
        while True:
            if resp := safe_json_response(self.bulk_import.get_bulk_imports_id(self.dest_host, self.dest_token, id)):
                if resp.get('status') == 'finished':
                    self.log.info('Bulk import finished')
                    return True
                else:
                    self.log.info('Bulk import still in progress')
                    sleep(self.config.export_import_timeout)

    def poll_single_entity_status(self, iid, eid):
        while True:
            if resp := safe_json_response(self.bulk_import.get_bulk_import_entity_details(self.dest_host, self.dest_token, iid, eid)):
                entity = from_dict(data_class=BulkImportEntityStatus, data=resp)
                if entity.status == 'finished':
                    self.log.info(f"Entity import for '{entity.destination_full_path}' is complete. Moving on to post-migration tasks")
                    return entity.to_dict()
                else:
                    self.log.info(f"Entity import for '{entity.destination_full_path}' in progress")
                    sleep(self.config.export_import_timeout)

    