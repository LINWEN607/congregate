from time import sleep
from dacite import from_dict
from celery import shared_task
from gitlab_ps_utils.misc_utils import safe_json_response
from congregate.helpers.migrate_utils import get_project_dest_namespace
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.base_gitlab_client import BaseGitLabClient
from congregate.migration.gitlab.api.bulk_imports import BulkImportApi
from congregate.migration.meta.api_models.bulk_import import BulkImportPayload
from congregate.migration.meta.api_models.bulk_import_entity import BulkImportEntity
from congregate.migration.meta.api_models.bulk_import_configuration import BulkImportconfiguration
from congregate.migration.meta.api_models.bulk_import_entity_status import BulkImportEntityStatus
from congregate.migration.meta.data_models.dry_run import DryRunData

class BulkImportsClient(BaseGitLabClient):
    def __init__(self, src_host=None, src_token=None, dest_host=None, dest_token=None):
        super().__init__(src_host=src_host, src_token=src_token,
                         dest_host=dest_host, dest_token=dest_token)
        self.bulk_import = BulkImportApi()

    def trigger_bulk_import(self, payload: BulkImportPayload, dry_run=True):
        if not dry_run:
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
                    sleep(self.config.poll_interval)          
                return (import_response.get('id'), list(self.bulk_import.get_bulk_import_entities(self.dest_host, self.dest_token, import_response.get('id'))), None)
            else:
                return (None, None, import_response.text)
        else:
            dry_run_data = []
            for entity in payload.entities:
                if entity.source_type == 'group_entity':
                    drd = self.get_all_group_paths(entity)
                    dry_run_data.append(drd.to_dict())
                elif entity.source_type == 'project_entity':
                    drd = DryRunData(projects=[entity.source_full_path])
                    dry_run_data.append(drd.to_dict())
            return (None, dry_run_data, None)

    def poll_import_status(self, id):
        while True:
            if resp := safe_json_response(self.bulk_import.get_bulk_import_status(self.dest_host, self.dest_token, id)):
                if resp.get('status') == 'finished':
                    self.log.info(f'Bulk import {id} finished')
                    return True
                elif resp.get('status') == 'failed':
                    self.log.error(f"Bulk import {id} failed. Refer to Congregate and GitLab logs for more information")
                    return False
                else:
                    self.log.info(f'Bulk import {id} still in progress')
                    sleep(self.config.poll_interval)

    def poll_single_entity_status(self, entity) -> BulkImportEntityStatus:
        entity_id = entity.get('id')
        dt_id = entity.get('bulk_import_id')
        while True:
            if resp := safe_json_response(self.bulk_import.get_bulk_import_entity_details(self.dest_host, self.dest_token, dt_id, entity_id)):
                entity = from_dict(data_class=BulkImportEntityStatus, data=resp)
                if entity.status == 'finished':
                    self.log.info(f"Entity import for '{entity.destination_slug}' is complete. Moving on to post-migration tasks")
                    return entity.to_dict()
                elif entity.status == 'failed':
                    self.log.error(f"Entity import for '{entity.destination_slug}' failed. Refer to Congregate and GitLab logs for more information")
                    return None
                else:
                    self.log.info(f"Entity import for '{entity.destination_slug}' in progress")
                    sleep(self.config.poll_interval)
    
    def calculate_entity_count(self, full_path):
        """
            Get total count of entities included in the direct transfer request

            This is used downstream to poll the DT API to make sure all the entities have been
            created before we move on to other tasks
        """
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

    def get_all_group_paths(self, entity: BulkImportEntity):
        """
            Get list of all group and project paths in a dry-run
        """
        groups_api = GroupsApi()
        group = safe_json_response(groups_api.get_group_by_full_path(entity.source_full_path, self.config.source_host, self.config.source_token))
        paths = DryRunData(top_level_group=group.get('full_path'), entity=entity)
        gid = group.get('id')
        for project in groups_api.get_all_group_projects(gid, self.config.source_host, self.config.source_token, include_subgroups=True):
            paths.projects.append(project.get('path_with_namespace'))
        for subgroup in groups_api.get_all_group_subgroups(gid, self.config.source_host, self.config.source_token):
            paths.subgroups.append(subgroup.get('full_path'))
        return paths
    
    def build_payload(self, staged_data, entity_type, skip_projects=False):
        """
            Build out the direct transfer API payload based on the staged data
        """
        config = BulkImportconfiguration(url=self.config.source_host, access_token=self.config.source_token)
        entities = []
        for data in staged_data:
            if entity_type == 'group':
                # Skip subgroups since they will be included in the top level group payload
                if len(data['full_path'].split("/")) == 1:
                    entities.append(self.build_group_entity(data, skip_projects=skip_projects))
            elif entity_type == 'project':
                entities.append(self.build_project_entity(data))
        return BulkImportPayload(configuration=config, entities=entities)
    
    def build_group_entity(self, group_data, skip_projects=False):
        """
            Build a single direct transfer group entity

            Note: this currently doesn't work with stage wave
        """
        return BulkImportEntity(
            source_type=f"group_entity",
            source_full_path=group_data['full_path'],
            destination_slug=group_data['path'],
            destination_namespace=self.config.dstn_parent_group_path,
            # destination_name=group_data['name'],
            migrate_projects=(not skip_projects)
        )
    
    def build_project_entity(self, project_data):
        """
            Build a single direct transfer project entity

            Note: this currently doesn't work with stage wave
        """
        return BulkImportEntity(
            source_type=f"project_entity",
            source_full_path=project_data['path_with_namespace'],
            destination_slug=project_data['path'],
            destination_namespace=get_project_dest_namespace(project_data),
            destination_name=project_data['name'],
        )

@shared_task(name='watch-import-status')
def watch_import_status(dest_host: str, dest_token: str, id: int):
    client = BulkImportsClient(src_host=None, src_token=None, dest_host=dest_host, dest_token=dest_token)
    return client.poll_import_status(id)

@shared_task(name='watch-import-entity-status')
def watch_import_entity_status(dest_host: str, dest_token: str, entity: dict):
    client = BulkImportsClient(src_host=None, src_token=None, dest_host=dest_host, dest_token=dest_token)
    return client.poll_single_entity_status(entity)
