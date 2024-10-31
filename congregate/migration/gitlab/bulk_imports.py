from time import sleep
from dacite import from_dict
from celery import shared_task, chain
from gitlab_ps_utils.misc_utils import safe_json_response
from congregate.helpers.migrate_utils import get_project_dest_namespace, get_staged_projects
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.base_gitlab_client import BaseGitLabClient
from congregate.migration.gitlab.api.bulk_imports import BulkImportApi
from congregate.migration.gitlab.migrate import post_migration_task
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
                if entity.source_type == 'group_entity':
                    total_entity_count += self.calculate_entity_count(entity.source_full_path)
                else:
                    total_entity_count += 1
            if import_response.status_code in [200, 201, 202]:
                import_response = import_response.json()
                self.log.info(f"Successfully triggered bulk import request with response: {import_response}")
                self.log.info(f"total entity count: {total_entity_count}")
                while len(list(self.bulk_import.get_bulk_import_entities(self.dest_host, self.dest_token, import_response.get('id')))) >= total_entity_count:
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
                    drd = DryRunData(entity=entity)
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
        entity_paths = set()
        if entity_type== 'group':
            # Order the staged groups from topmost level down
            sorted_staged_data = sorted(staged_data, key=lambda d: d['full_path'])
        elif entity_type== 'project':
            # Similar sort for projects
            sorted_staged_data = sorted(staged_data, key=lambda d: d['path_with_namespace'])
        else:
            self.log.error(f"Unknown entity type {entity_type} provided for staged data")
            return None
        # Get a list of namespaces where we have a subset of projects staged
        subset_namespaces = self.subset_projects_staged()
        for data in sorted_staged_data:
            if entity_type == 'group':
                # If a parent group is staged, skip adding this subgroup to the payload
                if self.parent_group_exists(data['full_path'], entity_paths):
                    continue
                entity_paths.add(data['full_path'])
                # If not all projects in this group are staged, add each individual project to the payload
                # and skip migrating projects in the group entity
                if subset_namespaces.get(data['full_path']) and skip_projects != True:
                    entities.append(self.build_group_entity(data, skip_projects=True))
                    for project in subset_namespaces[data['full_path']]:
                        entities.append(self.build_project_entity(project))
                else:
                    entities.append(self.build_group_entity(data, skip_projects=skip_projects))
            elif entity_type == 'project':
                entities.append(self.build_project_entity(data))
        return BulkImportPayload(configuration=config, entities=entities)

    def parent_group_exists(self, full_path, entity_paths):
        """
            Check if the subgroup's parent group is already staged.

            If so, skip the subgroup. If not, keep the subgroup
        """
        levels = full_path.split("/")
        rebuilt_path = []
        for level in levels:
            rebuilt_path.append(level)
            if "/".join(rebuilt_path) in entity_paths:
                self.log.warning(f"Skipping entity {full_path} due to parent group already present in staged data")
                return True
        return False

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
            destination_namespace=get_project_dest_namespace(project_data, group_path=self.config.dstn_parent_group_path),
            # destination_name=project_data['name'],
            migrate_projects=None
        )
    
    def subset_projects_staged(self):
        """
            Checks to see if any subsets of group projects are staged
            instead of the entire group and its projects
        """
        namespaces = {}
        subsets = {}
        groups_api = GroupsApi()
        for project in get_staged_projects():
            if namespaces.get(project['namespace']):
                namespaces[project['namespace']].append(project)
            else:
                namespaces[project['namespace']] = [project]
        for namespace, projects in namespaces.items():
            found_group = safe_json_response(groups_api.get_group_by_full_path(namespace, self.config.source_host, self.config.source_token))
            total_project_count = groups_api.get_all_group_projects_count(found_group['id'], self.config.source_host, self.config.source_token)
            staged_count = len(projects)
            if total_project_count > staged_count:
                subsets[namespace] = projects
        return subsets

# 'self' is in the function parameters due to the use of the 'bind' parameter in the decorator
# See https://docs.celeryq.dev/en/latest/userguide/tasks.html#bound-tasks for more information
@shared_task(bind=True, name='trigger-bulk-import-task')
def kick_off_bulk_import(self, payload, dry_run=True):
    payload = from_dict(data_class=BulkImportPayload, data=payload)
    dt_client = BulkImportsClient(payload.configuration.url, payload.configuration.access_token)
    dt_id, dt_entities, errors = dt_client.trigger_bulk_import(payload, dry_run=dry_run)
    if dt_id and dt_entities:
        # Kick off overall watch job
        watch_status = watch_import_status.delay(dt_client.config.destination_host, dt_client.config.destination_token, dt_id)
        entity_ids = []
        for entity in dt_entities:
            # Chain together watching the status of a specific entity
            # and then once that job completes, trigger post migration tasks
            res = chain(
                watch_import_entity_status.s(dt_client.config.destination_host, dt_client.config.destination_token, entity), 
                post_migration_task.s(dt_client.config.destination_host, dt_client.config.destination_token, dry_run=dry_run)
            ).apply_async(queue='celery')
            entity_ids.append(res.id)
        return {
            'status': 'triggered direct transfer jobs',
            'overall_status_id': watch_status.id,
            'entity_ids': entity_ids 
        }
    if dt_entities and (not dt_id):
        return {
            'status': 'dry run successful',
            'dry_run_data': dt_entities
        }
    return {
        'status': 'failed to trigger migration',
        'errors': errors
    }

@shared_task(name='watch-import-status')
def watch_import_status(dest_host: str, dest_token: str, id: int):
    client = BulkImportsClient(src_host=None, src_token=None, dest_host=dest_host, dest_token=dest_token)
    return client.poll_import_status(id)

@shared_task(name='watch-import-entity-status')
def watch_import_entity_status(dest_host: str, dest_token: str, entity: dict):
    client = BulkImportsClient(src_host=None, src_token=None, dest_host=dest_host, dest_token=dest_token)
    return client.poll_single_entity_status(entity)
