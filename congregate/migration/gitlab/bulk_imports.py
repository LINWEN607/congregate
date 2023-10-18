from time import sleep
from dacite import from_dict
from celery import shared_task
from gitlab_ps_utils.misc_utils import safe_json_response
from congregate.migration.gitlab.api.groups import GroupsApi
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
        import_response = self.bulk_import.start_new_bulk_import(self.dest_host, self.dest_token, payload.to_dict())
        total_entity_count = 0
        for entity in payload.entities:
            total_entity_count += self.calculate_entity_count(entity.source_full_path)
        if import_response.status_code in [200, 201, 202]:
            import_response = import_response.json()
            self.log.info(f"Successfully triggered bulk import request with response: {import_response}")
            self.log.info(f"total entity count: {total_entity_count}")
            while len(list(self.bulk_import.get_bulk_import_entities(self.dest_host, self.dest_token, import_response.get('id')))) != total_entity_count:
                self.log.debug(f"Waiting to see all {total_entity_count} entities populated.")
                sleep(2)          
            return (import_response.get('id'), list(self.bulk_import.get_bulk_import_entities(self.dest_host, self.dest_token, import_response.get('id'))), None)
        else:
            return (None, None, import_response.text)

    def poll_import_status(self, id):
        while True:
            if resp := safe_json_response(self.bulk_import.get_bulk_imports_id(self.dest_host, self.dest_token, id)):
                if resp.get('status') == 'finished':
                    self.log.info(f'Bulk import {id} finished')
                    return True
                else:
                    self.log.info(f'Bulk import {id} still in progress')
                    # sleep(self.config.export_import_timeout)
                    sleep(10)

    def poll_single_entity_status(self, entity) -> BulkImportEntityStatus:
        entity_id = entity.get('id')
        dt_id = entity.get('bulk_import_id')
        while True:
            if resp := safe_json_response(self.bulk_import.get_bulk_import_entity_details(self.dest_host, self.dest_token, dt_id, entity_id)):
                entity = from_dict(data_class=BulkImportEntityStatus, data=resp)
                if entity.status == 'finished':
                    self.log.info(f"Entity import for '{entity.destination_slug}' is complete. Moving on to post-migration tasks")
                    return entity.to_dict()
                else:
                    self.log.info(f"Entity import for '{entity.destination_slug}' in progress")
                    # sleep(self.config.export_import_timeout)
                    sleep(10)
    
    def calculate_entity_count(self, full_path):
        groups_api = GroupsApi()
        group = safe_json_response(groups_api.get_group_by_full_path(full_path, self.config.source_host, self.config.source_token))
        gid = group.get('id')
        total_project_count = groups_api.get_all_group_projects_count(gid, self.config.source_host, self.config.source_token, include_subgroups=True)
        if not total_project_count:
            total_project_count = len(list(groups_api.get_all_group_projects(gid, self.config.source_host, self.config.source_token)))
        total_subgroup_count = groups_api.get_all_group_subgroups_count(gid, self.config.source_host, self.config.source_token)
        if not total_subgroup_count:
            total_subgroup_count = len(list(groups_api.get_all_group_subgroups(gid, self.config.source_host, self.config.source_token)))
        return total_project_count + total_subgroup_count + 1

    

@shared_task
def watch_import_status(dest_host: str, dest_token: str, id: int):
    client = BulkImportsClient(src_host=None, src_token=None, dest_host=dest_host, dest_token=dest_token)
    return client.poll_import_status(id)

@shared_task
def watch_import_entity_status(dest_host: str, dest_token: str, entity: dict):
    client = BulkImportsClient(src_host=None, src_token=None, dest_host=dest_host, dest_token=dest_token)
    return client.poll_single_entity_status(entity)
