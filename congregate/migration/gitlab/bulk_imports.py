import json
from time import sleep
from typing import Tuple
from dacite import from_dict
from celery import shared_task, chain
from datetime import datetime, timedelta
from gitlab_ps_utils.misc_utils import safe_json_response, is_error_message_present
from congregate.helpers.migrate_utils import get_stage_wave_paths, get_staged_projects, get_full_path_with_parent_namespace
from congregate.migration.gitlab.api.groups import GroupsApi
from congregate.migration.gitlab.base_gitlab_client import BaseGitLabClient
from congregate.migration.gitlab.api.bulk_imports import BulkImportApi
from congregate.migration.gitlab.migrate import post_migration_task
from congregate.migration.meta.api_models.task_result import TaskResult
from congregate.migration.meta.api_models.bulk_import import BulkImportPayload
from congregate.migration.meta.api_models.bulk_import_entity import BulkImportEntity
from congregate.migration.meta.api_models.bulk_import_configuration import BulkImportConfiguration
from congregate.migration.meta.api_models.bulk_import_entity_status import BulkImportEntityStatus
from congregate.migration.meta.data_models.dry_run import DryRunData
from congregate.helpers.celery_mdbc import CeleryMongoConnector


class BulkImportsClient(BaseGitLabClient):
    def __init__(self, src_host=None, src_token=None, dest_host=None, dest_token=None):
        super().__init__(src_host=src_host, src_token=src_token,
                         dest_host=dest_host, dest_token=dest_token)
        self.bulk_import = BulkImportApi()

    def trigger_bulk_import(self, payload: BulkImportPayload, dry_run=True) -> Tuple[int, dict, str]:
        # Check if this import contains any project entities
        has_project_entities = any(entity.source_type == 'project_entity' for entity in payload.entities)
        
        if not dry_run:
            import_response = self.bulk_import.start_new_bulk_import(
                self.dest_host, self.dest_token, payload.to_dict())
            if import_response.status_code in [200, 201, 202]:
                import_response_json = import_response.json()
                # Store metadata about entity types
                import_response_json['has_project_entities'] = has_project_entities
                
                self.log.info(
                    f"Successfully triggered bulk import request with response: {import_response_json}")
                return (import_response_json.get('id'), None, import_response.text)
            return (None, None, import_response.text)
        return (None, payload.to_dict(), None)

    def poll_import_status(self, dt_id, extract_results=True, has_project_entities=False):
        while True:
            if resp := safe_json_response(self.bulk_import.get_bulk_import_status(self.dest_host, self.dest_token, dt_id)):
                if resp.get('status') == 'finished':
                    self.log.info(f'Bulk import {dt_id} finished')
                    
                    # Extract migration results if requested AND there are project entities
                    if extract_results and has_project_entities:
                        try:
                            # Set the default output filename
                            output_filename = f"{self.app_path}/data/results/project_migration_results.json"
                            self.log.info(f"Project entities found in import. Extracting migration results to {output_filename}")
                            
                            # Wait a short time to ensure all post-migration tasks are completed
                            sleep(10)
                            
                            # Pass the import status response directly to avoid duplicate API requests
                            extraction_result = self.extract_migration_results(dt_id, output_filename, import_details=resp)
                            self.log.info(f"Migration results extraction complete: {extraction_result}")
                        except Exception as e:
                            self.log.error(f"Failed to extract migration results: {e}")
                            self.log.info("For advanced extraction options, use the manual script at congregate/dev/bin/mongo-to-results-json/migration_extract.py")
                    elif extract_results:
                        self.log.info("No project entities in this import. Skipping migration results extraction.")
                    
                    return True
                    
                if resp.get('status') == 'failed':
                    self.log.error(
                        f"Bulk import {dt_id} failed. Refer to Congregate and GitLab logs for more information")
                    return False
                    
                self.log.info(f'Bulk import {dt_id} still in progress')
                sleep(self.config.poll_interval)

    def extract_migration_results(self, dt_id, output_file="project_migration_results.json", import_details=None):
        """
        Extract completed migration task data from MongoDB and format it into a structured JSON file.
        This is meant to be called after poll_import_status confirms the migration is 'finished'.
        
        Args:
            dt_id: ID of the completed bulk import
            output_file: Path to write the resulting JSON file
            import_details: Import status details from poll_import_status
        
        Returns:
            Dictionary with summary of the extraction
        """
        self.log.info(f"Extracting migration results for bulk import {dt_id}...")
        
        # Get prefix from configuration
        if prefix := self.config.dstn_parent_group_path:
            self.log.info(f"Using prefix '{prefix}' from configuration")
        else:
            self.log.warning("No destination parent group path found in configuration")
        
        # Set up retry parameters
        max_retries = 5
        retry_delay = 6  # seconds
        
        # Extract timestamps outside the retry loop
        try:
            created_at = import_details.get('created_at')
            finished_at = import_details.get('finished_at') or import_details.get('updated_at')
            
            start_time = datetime.fromisoformat(created_at.replace('Z', '+00:00')) - timedelta(minutes=5)
            end_time = datetime.fromisoformat(finished_at.replace('Z', '+00:00')) + timedelta(minutes=5)
            
            self.log.info(f"Using import timeframe: {start_time} to {end_time}")
        except (ValueError, TypeError) as e:
            self.log.error(f"Could not parse bulk import timestamps: {e}")
            return {"status": "error", "message": f"Could not parse timestamps: {e}"}
            
        for attempt in range(1, max_retries + 1):
            # Create a new MongoDB connector for each attempt
            mongo = CeleryMongoConnector()
            
            try:
                # Query MongoDB for tasks within this time window - only for project tasks with src_path
                tasks = list(mongo.db.celery_taskmeta.find({
                    'task': 'post-migration-task', 
                    'status': 'SUCCESS',
                    'date_done': {'$gte': start_time, '$lte': end_time},
                    'result': {'$regex': 'src_path'}  # Only tasks with src_path in the result
                }))
                                        
                self.log.info(f"Found {len(tasks)} project migration tasks within the bulk import timeframe")
                
                if not tasks:
                    # No tasks found in this attempt
                    if attempt < max_retries:
                        self.log.warning(f"No migration tasks found for this bulk import on attempt {attempt}. Retrying in {retry_delay} seconds...")
                        # Close the connection before retrying
                        mongo.close_connection()
                        sleep(retry_delay)
                        continue
                    else:
                        self.log.warning(f"No migration tasks found for this bulk import after {max_retries} attempts")
                        mongo.close_connection()
                        return {"status": "warning", "message": f"No migration tasks found after {max_retries} attempts"}
                
                self.log.info(f"Processing {len(tasks)} migration tasks...")
                
                # Prepare the result list
                results = []
                count = 0
                skipped = 0
                
                # Process each task
                for task in tasks:
                    count += 1
                    try:
                        # Parse the result JSON string
                        task_result_dict = json.loads(task.get("result", "{}"))
                        
                        # Create a TaskResult object from the dictionary
                        try:
                            task_result = TaskResult.from_dict(task_result_dict)
                            
                            # Skip tasks without src_path
                            if not task_result.src_path:
                                self.log.warning(f"Missing src_path in task {task.get('_id')}")
                                skipped += 1
                                continue
                                
                            # Create the path with prefix
                            if prefix:
                                project_path = f"{prefix}/{task_result.src_path}"
                            else:
                                project_path = task_result.src_path
                            
                            # Check if this project path is already in the results to prevent duplicates
                            if any(project_path in result for result in results):
                                self.log.info(f"Skipping duplicate entry for project {project_path}")
                                continue
                            
                            # Create the entry using the task_result's to_dict method
                            entry = {project_path: task_result.to_dict()}
                            
                            # Add to results
                            results.append(entry)
                            
                        except (ValueError, TypeError) as e:
                            self.log.warning(f"Failed to create TaskResult from dictionary: {e}")
                            skipped += 1
                            continue
                            
                    except json.JSONDecodeError:
                        self.log.warning(f"Failed to parse result for task {task.get('_id')}")
                        skipped += 1
                        continue
                
                # Write the results to file
                if results:
                    with open(output_file, 'w') as f:
                        json.dump(results, f, indent=4)
                    
                    # Summary
                    summary = {
                        "status": "success",
                        "tasks_processed": count,
                        "tasks_skipped": skipped,
                        "results_extracted": len(results),
                        "output_file": output_file,
                        "prefix_used": prefix or "None",
                        "attempt": attempt
                    }
                    
                    self.log.info(f"Extraction Summary:")
                    self.log.info(f"- Total tasks processed: {count}")
                    self.log.info(f"- Tasks skipped (missing data): {skipped}")
                    self.log.info(f"- Valid results extracted: {len(results)}")
                    self.log.info(f"- Results written to: {output_file}")
                    self.log.info(f"- Successful on attempt {attempt} of {max_retries}")
                    
                    if prefix:
                        self.log.info(f"- Used prefix: {prefix}")
                    else:
                        self.log.info("- No prefix was used - project paths reflect source paths directly")
                    
                    # Always close the connection before returning
                    mongo.close_connection()
                    return summary
                else:
                    # If we have tasks but no valid results, try again if attempts remain
                    if attempt < max_retries:
                        self.log.warning(f"Found tasks but no valid results on attempt {attempt}. Retrying in {retry_delay} seconds...")
                        # Close the connection before retrying
                        mongo.close_connection()
                        sleep(retry_delay)
                        continue
                    else:
                        self.log.warning(f"Processed {count} tasks but no valid results were found after {max_retries} attempts")
                        mongo.close_connection()
                        return {
                            "status": "warning",
                            "message": "No valid results to write",
                            "tasks_processed": count,
                            "tasks_skipped": skipped,
                            "attempts": max_retries
                        }
            
            except Exception as e:
                # Handle any unexpected errors during the extraction process
                self.log.error(f"Error during extraction attempt {attempt}: {e}")
                # Close the connection before retrying
                mongo.close_connection()
                
                if attempt < max_retries:
                    self.log.info(f"Retrying in {retry_delay} seconds...")
                    sleep(retry_delay)
                    continue
                else:
                    self.log.error(f"Error during extraction after {max_retries} attempts: {e}")
                    return {"status": "error", "message": str(e)}

    def poll_single_entity_status(self, entity) -> BulkImportEntityStatus:
        entity_id = entity.get('id')
        dt_id = entity.get('bulk_import_id')
        while True:
            if resp := safe_json_response(self.bulk_import.get_bulk_import_entity_details(self.dest_host, self.dest_token, dt_id, entity_id)):
                entity = from_dict(
                    data_class=BulkImportEntityStatus, data=resp)
                if entity.status == 'finished':
                    self.log.info(
                        f"Entity import for '{entity.destination_slug}' is complete. Moving on to post-migration tasks")
                    return entity.to_dict()
                if entity.status == 'failed':
                    self.log.error(
                        f"Entity import for '{entity.destination_slug}' failed. Refer to Congregate and GitLab logs for more information")
                    return None
                self.log.info(
                    f"Entity import for '{entity.destination_slug}' in progress")
                sleep(self.config.poll_interval)

    def calculate_entity_count(self, full_path):
        """
            Get total count of entities included in the direct transfer request

            This is used downstream to poll the DT API to make sure all the entities have been
            created before we move on to other tasks
        """
        groups_api = GroupsApi()
        host = self.config.source_host
        token = self.config.source_token
        group = safe_json_response(
            groups_api.get_group_by_full_path(full_path, host, token))
        gid = group.get('id')
        total_project_count = groups_api.get_all_group_projects_count(
            gid, host, token)
        if not total_project_count:
            total_project_count = len(
                list(groups_api.get_all_group_projects(gid, host, token)))
        total_subgroup_count = groups_api.get_all_group_subgroups_count(
            gid, host, token)
        if not total_subgroup_count:
            total_subgroup_count = len(
                list(groups_api.get_all_group_subgroups(gid, host, token)))
        return total_project_count + total_subgroup_count + 1

    def get_all_group_paths(self, entity: BulkImportEntity):
        """
            Get list of all group and project paths in a dry-run
        """
        groups_api = GroupsApi()
        host = self.config.source_host
        token = self.config.source_token
        group = safe_json_response(groups_api.get_group_by_full_path(
            entity.source_full_path, host, token))
        paths = DryRunData(top_level_group=group.get(
            'full_path'), entity=entity)
        gid = group.get('id')
        for project in groups_api.get_all_group_projects(gid, host, token):
            paths.projects.append(project.get('path_with_namespace'))
        for subgroup in groups_api.get_all_group_subgroups(gid, host, token):
            paths.subgroups.append(subgroup.get('full_path'))
        return paths

    def build_payload(self, staged_data, entity_type, skip_projects=False):
        """
            Build out the direct transfer API payload based on the staged data
        """
        config = BulkImportConfiguration(
            url=self.config.source_host, access_token=self.config.source_token)
        entities = []
        entity_paths = set()
        if entity_type == 'group':
            # Order the staged groups from topmost level down
            sorted_staged_data = sorted(
                staged_data, key=lambda d: d['full_path'].count('/'))
        elif entity_type == 'project':
            # Similar sort for projects
            sorted_staged_data = sorted(
                staged_data, key=lambda d: d['path_with_namespace'].count('/'))
        else:
            self.log.error(
                f"Unknown entity type {entity_type} provided for staged data")
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
                if subset_namespaces.get(data['full_path']) and not skip_projects:
                    entities.append(self.build_group_entity(
                        data, skip_projects=True))
                    for project in subset_namespaces[data['full_path']]:
                        entities.append(self.build_project_entity(project))
                else:
                    entities.append(self.build_group_entity(
                        data, skip_projects=skip_projects))
            elif entity_type == 'project':
                entities.append(self.build_project_entity(data))
        return BulkImportPayload(configuration=config, entities=entities)

    def parent_group_exists(self, full_path, entity_paths):
        """
            Check if the subgroup's parent group is already staged.

            If so, skip the subgroup. If not, keep the subgroup
        """
        return any(full_path.startswith(parent + '/') for parent in entity_paths)

    def build_group_entity(self, group_data, skip_projects=False):
        """
            Build a single direct transfer group entity

            Note: this currently doesn't work with stage wave
        """
        namespace = get_full_path_with_parent_namespace(
            group_data['full_path'])
        return BulkImportEntity(
            source_type="group_entity",
            source_full_path=group_data['full_path'],
            destination_slug=group_data['path'],
            destination_namespace=namespace.rsplit(
                "/", 1)[0] if "/" in namespace else "",
            migrate_projects=(not skip_projects),
        )

    def build_project_entity(self, project_data):
        """
            Build a single direct transfer project entity
        """
        _, target_namespace=get_stage_wave_paths(project_data)
        return BulkImportEntity(
            source_type="project_entity",
            source_full_path=project_data['path_with_namespace'],
            destination_slug=project_data['path'],
            destination_namespace=target_namespace,
        )

    def subset_projects_staged(self):
        """
            Checks to see if any subsets of group projects are staged
            instead of the entire group and its projects
        """
        namespaces = {}
        subsets = {}
        groups_api = GroupsApi()
        host = self.config.source_host
        token = self.config.source_token
        for project in get_staged_projects():
            if namespaces.get(project['namespace']):
                namespaces[project['namespace']].append(project)
            else:
                namespaces[project['namespace']] = [project]
        for namespace, projects in namespaces.items():
            if found_group := safe_json_response(
                groups_api.get_group_by_full_path(namespace, host, token)):
                error, _ = is_error_message_present(found_group)
                if not error:
                    total_project_count = groups_api.get_all_group_projects_count(
                        found_group['id'], host, token)
                    staged_count = len(projects)
                    if total_project_count > staged_count:
                        subsets[namespace] = projects
                else:
                    self.log.error(f"Unable to find group {namespace}")
            else:
                self.log.warning(
                    f"Could not find group for namespace '{namespace}'. Run new list and/or validate the data in mongo DB")
        return subsets

# 'self' is in the function parameters due to the use of the 'bind' parameter in the decorator
# See https://docs.celeryq.dev/en/latest/userguide/tasks.html#bound-tasks for more information
@shared_task(bind=True, name='trigger-bulk-import-task')
def kick_off_bulk_import(self, payload, dry_run=True):
    payload = from_dict(data_class=BulkImportPayload, data=payload)
    
    # Check if this import contains any project entities
    has_project_entities = any(entity.source_type == 'project_entity' for entity in payload.entities)
    
    dt_client = BulkImportsClient(
        payload.configuration.url, payload.configuration.access_token)
    dt_id, dt_entities, errors = dt_client.trigger_bulk_import(
        payload, dry_run=dry_run)
    host = dt_client.config.destination_host
    token = dt_client.config.destination_token
    if dt_id:
        # Kick off overall watch job, passing the project entities flag
        watch_status = watch_import_status.delay(host, token, dt_id, extract_results=True, has_project_entities=has_project_entities)
        entity_ids = []
        processed_entities = set()
        imported_entities = list(
            dt_client.bulk_import.get_bulk_import_entities(host, token, dt_id))
        while len(processed_entities) < len(imported_entities):
            dt_client.log.info(
                f"Total processed entities: {len(processed_entities)}, Total discovered entities: {len(imported_entities)}")
            for entity in imported_entities:
                entity_id = entity.get('id')
                if entity_id not in processed_entities:
                    dt_client.log.debug(f"Need to process entity {entity}")
                    # Chain together watching the status of a specific entity
                    # and then once that job completes, trigger post migration tasks
                    res = chain(
                        watch_import_entity_status.s(host, token, entity),
                        post_migration_task.s(host, token, dry_run=dry_run)
                    ).apply_async(queue='celery')
                    dt_client.log.debug(f"Task response: {res}")
                    entity_ids.append(res.id)
                    processed_entities.add(entity_id)
                else:
                    dt_client.log.info(
                        f"Entity {entity.get('id')} is already in the queue")
            dt_client.log.info("Waiting for all entities to be populated")
            sleep(dt_client.config.poll_interval)
            imported_entities = list(
                dt_client.bulk_import.get_bulk_import_entities(host, token, dt_id))
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
def watch_import_status(dest_host: str, dest_token: str, dt_id: int, extract_results=True, has_project_entities=False):
    client = BulkImportsClient(
        src_host=None, src_token=None, dest_host=dest_host, dest_token=dest_token)
    return client.poll_import_status(dt_id, extract_results=extract_results, has_project_entities=has_project_entities)


@shared_task(name='watch-import-entity-status')
def watch_import_entity_status(dest_host: str, dest_token: str, entity: dict):
    client = BulkImportsClient(
        src_host=None, src_token=None, dest_host=dest_host, dest_token=dest_token)
    return client.poll_single_entity_status(entity)
