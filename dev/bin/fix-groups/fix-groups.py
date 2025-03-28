#!/usr/bin/env python3
"""
GitLab Direct Transfer API Migration Tool
========================================

Description:
------------
This script facilitates the migration of GitLab groups from one GitLab instance to another
using GitLab's Direct Transfer API. It reads migration details from a CSV file, identifies
the optimal migration units to minimize transfers, and executes the migration process with
comprehensive logging and status monitoring.

The script intelligently handles group hierarchies by:
1. Ordering groups from highest to lowest in the hierarchy
2. Checking which groups already exist in the destination
3. Migrating at the highest possible level to include all subgroups
4. Skipping subgroups that would be included in higher-level migrations

Prerequisites:
-------------
1. Admin access tokens for both source and destination GitLab instances
2. API access to both GitLab instances
3. Python 3.6+ with requests library installed
4. CSV file with migration details in the specified format

CSV Format:
----------
The CSV file must include the following columns:
- Wave Name: Identifier for grouping migrations (e.g., "Wave1")
- Wave Date: Date of the migration (typically today's date)
- Source Url: Complete URL to the source group (e.g., "https://gitlab.source.com/group/subgroup")
- Source Parent Path: Path to the parent group in source GitLab (without the base URL)
- Destination Parent Path: Path to the parent group in destination GitLab (without the base URL)

Environment Variables:
--------------------
The following environment variables must be set:
- SOURCE_GITLAB_ROOT: Base URL for the source GitLab instance (e.g., "https://gitlab.source.com")
- SOURCE_ADMIN_ACCESS_TOKEN: Admin access token for the source GitLab instance
- DESTINATION_GITLAB_ROOT: Base URL for the destination GitLab instance (e.g., "https://gitlab.dest.com")
- DESTINATION_ADMIN_ACCESS_TOKEN: Admin access token for the destination GitLab instance

Usage:
------
1. Set up environment variables:
   export SOURCE_GITLAB_ROOT="https://gitlab.source.com"
   export SOURCE_ADMIN_ACCESS_TOKEN="your-source-token"
   export DESTINATION_GITLAB_ROOT="https://gitlab.dest.com"
   export DESTINATION_ADMIN_ACCESS_TOKEN="your-destination-token"

2. Run in check-only mode (only check group existence, no migration):
   python fix-groups.py path/to/migration.csv --check-only

3. Run in dry-run mode (no actual migrations performed):
   python fix-groups.py path/to/migration.csv

4. Run with the --commit flag to perform actual migrations:
   python fix-groups.py path/to/migration.csv --commit

5. Enable verbose API logging with --debug flag:
   python fix-groups.py path/to/migration.csv --debug

Features:
--------
- Intelligent Group Hierarchy Handling: Migrates at optimal levels to minimize transfers
- Check-Only Mode: Only performs read operations to verify group existence, with enhanced parent-child reporting
- Dry Run Mode: Test migration plans without making actual API calls but still logs what would be done
- Comprehensive Logging: All actions are logged to both console and timestamped log files
- API Call Logging: All API requests and responses are logged (at DEBUG level, or INFO with --debug)
- Consolidated Payload: Outputs a single API payload that could be used to migrate all groups at once
- Detailed Skip Reporting: Lists all child groups that will be skipped for each parent migration
- Error Handling: Robust error detection and reporting
- Status Monitoring: Polls transfer status to confirm successful completion
- Migration Summary: Provides statistical overview of migration results

Output:
-------
1. Console output with real-time progress information
2. Main log file (gitlab_migration_YYYYMMDD_HHMMSS.log)
3. Missing source groups log file (missing_source_groups_YYYYMMDD_HHMMSS.log)
4. Existing destination groups log file (existing_destination_groups_YYYYMMDD_HHMMSS.log)
5. Consolidated payload file (consolidated_payload_YYYYMMDD_HHMMSS.json)
6. Summary of migration results by wave
7. Detailed API request/response logs (when --debug is used)

Notes:
------
- The script respects GitLab API rate limits and adds short delays between operations
- For large groups with many subgroups and projects, transfers may take considerable time
- Failed transfers can be retried by running the script again with the same CSV

Author:
-------
Created: 2023-11-01

Version:
-------
1.0.0

License:
-------
MIT License
"""

import argparse
import copy
import csv
import datetime
import json
import logging
import os
import requests
import sys
import time
import urllib.parse
from typing import Dict, List, Optional, Any, Tuple, Set

# Configuration from environment variables
SOURCE_GITLAB_ROOT = os.environ.get('SOURCE_GITLAB_ROOT')
SOURCE_ADMIN_ACCESS_TOKEN = os.environ.get('SOURCE_ADMIN_ACCESS_TOKEN')
DESTINATION_GITLAB_ROOT = os.environ.get('DESTINATION_GITLAB_ROOT')
DESTINATION_ADMIN_ACCESS_TOKEN = os.environ.get('DESTINATION_ADMIN_ACCESS_TOKEN')

# Timestamp for log files
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

# Setup logging
main_log_file = f"gitlab_migration_{timestamp}.log"
missing_sources_log_file = f"missing_source_groups_{timestamp}.log"
existing_dest_log_file = f"existing_destination_groups_{timestamp}.log"

# Create a custom logger
logger = logging.getLogger("gitlab_migrator")
logger.setLevel(logging.INFO)

# Create console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(console_handler)

# Create main log file handler
file_handler = logging.FileHandler(main_log_file)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Create missing sources log file handler
missing_sources_handler = logging.FileHandler(missing_sources_log_file)
missing_sources_handler.setLevel(logging.INFO)
missing_sources_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))

# Create existing destinations log file handler
existing_dest_handler = logging.FileHandler(existing_dest_log_file)
existing_dest_handler.setLevel(logging.INFO)
existing_dest_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))

# Create specific loggers for the special files
missing_sources_logger = logging.getLogger("missing_sources")
missing_sources_logger.setLevel(logging.INFO)
missing_sources_logger.addHandler(missing_sources_handler)
missing_sources_logger.propagate = False  # Don't propagate to parent logger

existing_dest_logger = logging.getLogger("existing_dest")
existing_dest_logger.setLevel(logging.INFO)
existing_dest_logger.addHandler(existing_dest_handler)
existing_dest_logger.propagate = False  # Don't propagate to parent logger


class GitLabMigrator:
    """Class to handle GitLab group migrations using Direct Transfer API"""

    def __init__(self, dry_run: bool = True, check_only: bool = False, debug: bool = False):
        """
        Initialize the migrator
        
        Args:
            dry_run: If True, no actual migration will be performed
            check_only: If True, only check group existence, don't attempt migration
            debug: If True, enable verbose API logging
        """
        self.dry_run = dry_run
        self.check_only = check_only
        self.debug = debug
        
        # If debug is enabled, set logging level to DEBUG
        if debug:
            logger.setLevel(logging.DEBUG)
            console_handler.setLevel(logging.DEBUG)
            file_handler.setLevel(logging.DEBUG)
            logger.info("Debug mode is enabled, API calls will be logged at INFO level for visibility")
        
        # Track groups that exist on destination
        self.existing_destination_groups = set()
        # Track groups that exist on source
        self.existing_source_groups = set()
        # Track groups that have been migrated or will be migrated as part of a parent group
        self.migrated_groups = set()
        # Track groups that don't exist on source
        self.missing_source_groups = set()
        
        # Validate environment variables
        if not all([SOURCE_GITLAB_ROOT, SOURCE_ADMIN_ACCESS_TOKEN, 
                   DESTINATION_GITLAB_ROOT, DESTINATION_ADMIN_ACCESS_TOKEN]):
            logger.error("Missing required environment variables. Please set the following:")
            logger.error("  SOURCE_GITLAB_ROOT")
            logger.error("  SOURCE_ADMIN_ACCESS_TOKEN")
            logger.error("  DESTINATION_GITLAB_ROOT")
            logger.error("  DESTINATION_ADMIN_ACCESS_TOKEN")
            sys.exit(1)
            
        logger.info(f"Initialized GitLab migrator with source: {SOURCE_GITLAB_ROOT}, destination: {DESTINATION_GITLAB_ROOT}")
        if check_only:
            logger.info("Running in CHECK ONLY mode - only checking group existence, no migrations will be performed")
        elif dry_run:
            logger.info("Running in DRY RUN mode - no actual migrations will be performed")
        else:
            logger.info("Running in COMMIT mode - migrations will be executed")
        
        if debug:
            logger.info("DEBUG mode enabled - verbose API logging is active")

    def url_encode_path(self, path: str) -> str:
        """URL encode a GitLab path"""
        return urllib.parse.quote(path, safe='')

    def log_api_request(self, method: str, url: str, headers: Dict[str, str], 
                       data: Optional[Dict[str, Any]] = None, dry_run: bool = False) -> None:
        """
        Log API request details
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            headers: Request headers
            data: Request payload (for POST/PUT)
            dry_run: Whether this is a simulated request in dry-run mode
        """
        # Create a safe copy of headers to avoid logging tokens
        safe_headers = copy.deepcopy(headers)
        if 'PRIVATE-TOKEN' in safe_headers:
            safe_headers['PRIVATE-TOKEN'] = '***REDACTED***'
            
        # Create a safe copy of data to avoid logging sensitive information
        safe_data = None
        if data:
            safe_data = copy.deepcopy(data)
            if isinstance(safe_data, dict):
                # Check if using the new direct transfer API format
                if 'configuration' in safe_data and 'access_token' in safe_data.get('configuration', {}):
                    safe_data['configuration']['access_token'] = '***REDACTED***'
                # Check for legacy format
                elif 'destination_admin_token' in safe_data:
                    safe_data['destination_admin_token'] = '***REDACTED***'
        
        log_data = {
            'request': {
                'method': method,
                'url': url,
                'headers': safe_headers
            }
        }
        
        if safe_data:
            log_data['request']['data'] = safe_data
        
        # Using a more direct logging approach to ensure debug logs are captured
        log_message = f"{'DRY RUN - Simulated ' if dry_run else ''}API Request: {json.dumps(log_data, indent=2)}"
        
        if self.debug:
            # When debug is enabled, force log at INFO level to ensure it's visible
            logger.info(log_message)
        else:
            # Otherwise log at DEBUG level
            logger.debug(log_message)

    def log_api_response(self, response: Optional[requests.Response], error: Optional[str] = None, 
                        dry_run: bool = False, dry_run_response: Optional[Dict[str, Any]] = None) -> None:
        """
        Log API response details
        
        Args:
            response: Response object from requests
            error: Error message if an exception occurred
            dry_run: Whether this is a simulated response in dry-run mode
            dry_run_response: Simulated response for dry-run mode
        """
        if dry_run:
            log_data = {
                'response': dry_run_response or {'status_code': 200, 'body': {'message': 'Simulated successful response'}}
            }
            log_message = f"DRY RUN - Simulated API Response: {json.dumps(log_data, indent=2)}"
        else:
            if error:
                log_data = {
                    'response': {
                        'error': error
                    }
                }
            else:
                try:
                    response_json = response.json() if response and response.content else {}
                except json.JSONDecodeError:
                    response_json = {'non_json_response': response.text[:500] if response else "No response"}
                    
                log_data = {
                    'response': {
                        'status_code': response.status_code if response else "unknown",
                        'body': response_json
                    }
                }
            log_message = f"API Response: {json.dumps(log_data, indent=2)}"
        
        # Using a more direct logging approach
        if self.debug:
            # When debug is enabled, force log at INFO level to ensure it's visible
            logger.info(log_message)
        else:
            # Otherwise log at DEBUG level
            logger.debug(log_message)

    def make_api_request(self, method: str, url: str, headers: Dict[str, str], 
                        data: Optional[Dict[str, Any]] = None) -> Tuple[Optional[requests.Response], Optional[str]]:
        """
        Make API request with logging
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            headers: Request headers
            data: Request payload (for POST/PUT)
            
        Returns:
            Tuple of (Response object, Error message)
        """
        # In dry-run mode, don't make actual API calls except for GET in check-only mode
        if self.dry_run and not (method.upper() == 'GET' and self.check_only):
            self.log_api_request(method, url, headers, data, dry_run=True)
            
            # Create appropriate simulated responses based on the request type
            if 'bulk_imports' in url and method.upper() == 'POST':
                simulated_response = {
                    'status_code': 202,
                    'body': {
                        'id': 12345,
                        'status': 'created',
                        'message': 'Bulk import scheduled'
                    }
                }
            elif '/bulk_imports/' in url and method.upper() == 'GET':
                # Simulating a status check
                simulated_response = {
                    'status_code': 200,
                    'body': {
                        'id': 12345,
                        'status': 'finished',
                        'entities': [
                            {
                                'id': 1,
                                'source_full_path': 'group/subgroup',
                                'destination_slug': 'subgroup',
                                'destination_namespace': 'target-group',
                                'status': 'finished'
                            }
                        ]
                    }
                }
            elif '/groups/' in url and method.upper() == 'GET':
                # Simulating a group ID lookup - check if we're testing for existence
                group_path = urllib.parse.unquote(url.split('/')[-1])
                
                # In dry run, check which instance we're querying (source or destination)
                is_source = DESTINATION_GITLAB_ROOT not in url
                
                if is_source:
                    # For source, assume most groups exist except ones we've marked as missing
                    group_exists = group_path not in self.missing_source_groups
                else:
                    # For destination, check our tracked set of existing groups
                    group_exists = self.group_exists_on_destination(group_path)
                    
                if group_exists:
                    simulated_response = {
                        'status_code': 200,
                        'body': {
                            'id': 999 if is_source else 888,
                            'name': group_path.split('/')[-1],
                            'path': group_path.split('/')[-1],
                            'full_path': group_path
                        }
                    }
                else:
                    # Simulate 404 for non-existent groups
                    simulated_response = {
                        'status_code': 404,
                        'body': {
                            'message': 'Group Not Found'
                        }
                    }
            else:
                simulated_response = {
                    'status_code': 200,
                    'body': {
                        'message': f'Simulated successful {method} response for {url}'
                    }
                }
                
            self.log_api_response(None, None, True, simulated_response)
            
            # Return None for both response and error to indicate this was a dry run
            return None, None
            
        # Make actual API call (for check-only mode or commit mode)
        try:
            self.log_api_request(method, url, headers, data)
            
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers)
            elif method.upper() == 'POST':
                # Only make POST requests in commit mode
                if self.check_only:
                    logger.info(f"CHECK ONLY mode: Skipping actual POST request to {url}")
                    simulated_response = {
                        'status_code': 202,
                        'body': {
                            'message': 'Simulated successful POST response (check-only mode)'
                        }
                    }
                    self.log_api_response(None, None, True, simulated_response)
                    return None, None
                else:
                    response = requests.post(url, headers=headers, json=data)
            elif method.upper() == 'PUT':
                # Only make PUT requests in commit mode
                if self.check_only:
                    logger.info(f"CHECK ONLY mode: Skipping actual PUT request to {url}")
                    simulated_response = {
                        'status_code': 200,
                        'body': {
                            'message': 'Simulated successful PUT response (check-only mode)'
                        }
                    }
                    self.log_api_response(None, None, True, simulated_response)
                    return None, None
                else:
                    response = requests.put(url, headers=headers, json=data)
            elif method.upper() == 'DELETE':
                # Only make DELETE requests in commit mode
                if self.check_only:
                    logger.info(f"CHECK ONLY mode: Skipping actual DELETE request to {url}")
                    simulated_response = {
                        'status_code': 204,
                        'body': {
                            'message': 'Simulated successful DELETE response (check-only mode)'
                        }
                    }
                    self.log_api_response(None, None, True, simulated_response)
                    return None, None
                else:
                    response = requests.delete(url, headers=headers)
            else:
                return None, f"Unsupported HTTP method: {method}"
                
            self.log_api_response(response)
            return response, None
            
        except Exception as e:
            error_msg = str(e)
            self.log_api_response(None, error_msg)
            return None, error_msg

    def check_group_exists(self, gitlab_url: str, token: str, group_path: str) -> bool:
        """
        Check if a group exists in the GitLab instance
        
        Args:
            gitlab_url: Base GitLab URL
            token: GitLab API token
            group_path: Full path to the group
            
        Returns:
            True if the group exists
        """
        if not group_path.strip():
            return False
        
        encoded_path = self.url_encode_path(group_path)
        headers = {'PRIVATE-TOKEN': token}
        url = f"{gitlab_url}/api/v4/groups/{encoded_path}"
        
        # For source groups in dry run mode but not check-only, simulate existence
        if self.dry_run and not self.check_only and gitlab_url == SOURCE_GITLAB_ROOT:
            # In dry run, assume source groups exist unless marked as missing
            exists = group_path not in self.missing_source_groups
            if exists:
                logger.info(f"DRY RUN: Simulating that source group '{group_path}' exists")
            else:
                logger.info(f"DRY RUN: Simulating that source group '{group_path}' does not exist")
                missing_sources_logger.info(f"Source group does not exist: {group_path}")
            return exists
            
        # For destination groups in dry run mode but not check-only, simulate existence check
        if self.dry_run and not self.check_only and gitlab_url == DESTINATION_GITLAB_ROOT:
            # In dry run, check our tracked set for destination groups
            exists = self.group_exists_on_destination(group_path)
            if exists:
                logger.info(f"DRY RUN: Simulating that destination group '{group_path}' exists")
                existing_dest_logger.info(f"Destination group exists: {group_path}")
            else:
                logger.info(f"DRY RUN: Simulating that destination group '{group_path}' does not exist")
            return exists
        
        # In check-only mode or commit mode, make the actual API call
        response, error = self.make_api_request('GET', url, headers)
        
        if error:
            logger.error(f"Error checking if group {group_path} exists: {error}")
            return False
            
        exists = response and response.status_code == 200
        
        # Track group existence
        if exists:
            if gitlab_url == SOURCE_GITLAB_ROOT:
                self.existing_source_groups.add(group_path)
                logger.info(f"Source group '{group_path}' exists")
            elif gitlab_url == DESTINATION_GITLAB_ROOT:
                self.existing_destination_groups.add(group_path)
                logger.info(f"Destination group '{group_path}' exists")
                existing_dest_logger.info(f"Destination group exists: {group_path}")
        else:
            if gitlab_url == SOURCE_GITLAB_ROOT:
                self.missing_source_groups.add(group_path)
                logger.info(f"Source group '{group_path}' does not exist")
                missing_sources_logger.info(f"Source group does not exist: {group_path}")
            elif gitlab_url == DESTINATION_GITLAB_ROOT:
                logger.info(f"Destination group '{group_path}' does not exist")
                
        return exists

    def group_exists_on_destination(self, group_path: str) -> bool:
        """
        Check if a group exists on the destination in dry run mode
        
        Args:
            group_path: Full path to the group
            
        Returns:
            True if the group is simulated to exist
        """
        # For simulation in dry run, we'll say that groups already in our tracking set exist
        return group_path in self.existing_destination_groups

    def get_group_id(self, gitlab_url: str, token: str, group_path: str) -> Optional[int]:
        """
        Get GitLab group ID by path
        
        Args:
            gitlab_url: Base GitLab URL
            token: GitLab API token
            group_path: Full path to the group
            
        Returns:
            Group ID or None if not found
        """
        if not group_path.strip():
            logger.warning(f"Empty group path provided")
            return None
        
        encoded_path = self.url_encode_path(group_path)
        headers = {'PRIVATE-TOKEN': token}
        url = f"{gitlab_url}/api/v4/groups/{encoded_path}"
        
        if self.dry_run and not self.check_only:
            logger.info(f"DRY RUN: Simulating group ID lookup for {group_path}")
            # If we're checking destination and the group is marked as existing, return a simulated ID
            if gitlab_url == DESTINATION_GITLAB_ROOT and self.group_exists_on_destination(group_path):
                return 999
            # If we're checking source, assume it exists unless marked as missing
            elif gitlab_url == SOURCE_GITLAB_ROOT and group_path not in self.missing_source_groups:
                return 888
            # Otherwise it doesn't exist
            return None
        
        response, error = self.make_api_request('GET', url, headers)
        
        if error:
            logger.error(f"Error getting group ID for {group_path}: {error}")
            return None
            
        if response and response.status_code == 200:
            group_id = response.json()['id']
            logger.info(f"Found group ID {group_id} for {group_path}")
            return group_id
        else:
            status_code = response.status_code if response else "unknown"
            response_text = response.text if response else "no response"
            logger.error(f"Failed to get group ID for {group_path}: {status_code} - {response_text}")
            return None

    def extract_group_name_and_path(self, full_url: str) -> Tuple[str, str]:
        """
        Extract group name and full path from a URL
        
        Args:
            full_url: Full URL to the group
            
        Returns:
            Tuple of (group name, group full path)
        """
        # Remove the base URL
        path = full_url.replace(SOURCE_GITLAB_ROOT, "")
        if path.startswith('/'):
            path = path[1:]
            
        # Extract the group name (last part of path)
        parts = path.split('/')
        group_name = parts[-1] if parts else ""
        
        return group_name, path

    def get_parent_paths(self, group_path: str) -> List[str]:
        """
        Get all parent paths of a group, from highest to lowest
        
        For example, for 'a/b/c/d', returns ['a', 'a/b', 'a/b/c']
        
        Args:
            group_path: Full path to the group
            
        Returns:
            List of parent paths, from highest to lowest
        """
        parts = group_path.split('/')
        parent_paths = []
        
        for i in range(1, len(parts)):
            parent_paths.append('/'.join(parts[:i]))
            
        return parent_paths

    def check_destination_groups(self, groups: List[dict]) -> None:
        """
        Check which groups already exist on the destination GitLab.
        Only checks the exact destination paths that would be created, not parent paths.
        
        Args:
            groups: List of groups from the CSV file
        """
        logger.info("Checking which groups already exist on the destination...")
        existing_dest_logger.info("=== Starting destination group existence check ===")
        
        # First, extract all unique destination paths that would be created
        destination_paths = set()
        for group in groups:
            # Extract source path and get group name (last part)
            _, source_path = self.extract_group_name_and_path(group['Source Url'])
            group_name = source_path.split('/')[-1]
            
            # Construct the full destination path
            dest_parent = group['Destination Parent Path']
            if dest_parent:
                full_dest_path = f"{dest_parent}/{group_name}"
            else:
                full_dest_path = group_name
                
            destination_paths.add(full_dest_path)
        
        # Check each destination path
        for path in sorted(destination_paths):
            # In dry run mode without check-only, simulate existence
            if self.dry_run and not self.check_only:
                # Simulate that short paths already exist (for testing)
                if path.count('/') <= 1:
                    logger.info(f"DRY RUN: Simulating that group '{path}' exists on destination")
                    self.existing_destination_groups.add(path)
                    existing_dest_logger.info(f"Destination group exists: {path}")
                else:
                    logger.info(f"DRY RUN: Simulating that group '{path}' does not exist on destination")
            else:
                # In check-only or commit mode, actually check
                exists = self.check_group_exists(DESTINATION_GITLAB_ROOT, DESTINATION_ADMIN_ACCESS_TOKEN, path)
                if exists:
                    logger.info(f"Group '{path}' already exists on destination")
                    self.existing_destination_groups.add(path)
                    existing_dest_logger.info(f"Destination group exists: {path}")
                else:
                    logger.info(f"Group '{path}' does not exist on destination")
        
        existing_dest_logger.info("=== Completed destination group existence check ===")
        existing_dest_logger.info(f"Total existing destination groups: {len(self.existing_destination_groups)}")

    def check_source_groups(self, groups: List[dict]) -> None:
        """
        Check which groups exist on the source GitLab
        
        Args:
            groups: List of groups from the CSV file
        """
        logger.info("Checking which groups exist on the source...")
        missing_sources_logger.info("=== Starting source group existence check ===")
        
        # First, extract all unique group paths
        all_paths = set()
        for group in groups:
            # The group is a dictionary with the CSV row data
            _, path = self.extract_group_name_and_path(group['Source Url'])
            all_paths.add(path)
        
        # Check each path on the source
        for path in sorted(all_paths):
            # In dry run mode without check-only, assume all source groups exist
            if self.dry_run and not self.check_only:
                logger.info(f"DRY RUN: Assuming source group '{path}' exists")
                self.existing_source_groups.add(path)
            else:
                # In check-only or commit mode, actually check
                exists = self.check_group_exists(SOURCE_GITLAB_ROOT, SOURCE_ADMIN_ACCESS_TOKEN, path)
                if exists:
                    logger.info(f"Source group '{path}' exists")
                    self.existing_source_groups.add(path)
                else:
                    logger.info(f"Source group '{path}' does not exist")
                    self.missing_source_groups.add(path)
                    missing_sources_logger.info(f"Source group does not exist: {path}")
        
        missing_sources_logger.info("=== Completed source group existence check ===")
        missing_sources_logger.info(f"Total missing source groups: {len(self.missing_source_groups)}")

    def analyze_group_hierarchy(self, groups: List[dict]) -> List[dict]:
        """
        Analyze the group hierarchy to determine optimal migration strategy.
        Simplified to only consider the final destination path existence.
        Works in both check-only and migration modes.
        
        Args:
            groups: List of groups from the CSV file
            
        Returns:
            List of groups to migrate, with optimal paths
        """
        logger.info("Analyzing group hierarchy to determine optimal migration strategy...")
        
        # Step 1: Sort groups by path length (shortest/highest first)
        sorted_groups = sorted(groups, key=lambda g: len(self.extract_group_name_and_path(g['Source Url'])[1].split('/')))
        
        # Step 2: Determine which groups need to be migrated
        groups_to_migrate = []
        for group in sorted_groups:
            # Extract source path and get group name
            _, source_path = self.extract_group_name_and_path(group['Source Url'])
            group_name = source_path.split('/')[-1]
            
            # Get destination path
            dest_parent = group['Destination Parent Path']
            if dest_parent:
                full_dest_path = f"{dest_parent}/{group_name}"
            else:
                full_dest_path = group_name
        
            # Skip if this group doesn't exist on source
            if source_path in self.missing_source_groups:
                if self.check_only:
                    logger.info(f"Group '{source_path}' would be skipped as it does not exist on source")
                else:
                    logger.info(f"Skipping group '{source_path}' as it does not exist on source")
                continue
                
            # Skip if this group is already migrated or will be migrated as part of a parent
            if source_path in self.migrated_groups:
                if self.check_only:
                    logger.info(f"Group '{source_path}' would be skipped as it would be migrated as part of a parent group")
                else:
                    logger.info(f"Skipping group '{source_path}' as it will be migrated as part of a parent group")
                continue
                
            # If the destination group already exists, skip it
            if full_dest_path in self.existing_destination_groups:
                if self.check_only:
                    logger.info(f"Destination path '{full_dest_path}' already exists - would be skipped")
                else:
                    logger.info(f"Destination path '{full_dest_path}' already exists - skipping")
                # Mark this group as handled
                self.migrated_groups.add(source_path)
                continue
            
            # This group needs to be migrated
            if self.check_only:
                logger.info(f"Group '{source_path}' would need to be migrated (would be placed at '{full_dest_path}')")
            else:
                logger.info(f"Group '{source_path}' needs to be migrated (will be placed at '{full_dest_path}')")
            groups_to_migrate.append(group)
            
            # Mark this group and all its potential children as handled
            self.migrated_groups.add(source_path)
            for other_group in sorted_groups:
                _, other_path = self.extract_group_name_and_path(other_group['Source Url'])
                if other_path.startswith(f"{source_path}/"):
                    if self.check_only:
                        logger.info(f"Marking '{other_path}' as handled (would be migrated with '{source_path}')")
                    else:
                        logger.info(f"Marking '{other_path}' as handled (will be migrated with '{source_path}')")
                    self.migrated_groups.add(other_path)
        
        return groups_to_migrate

    def generate_consolidated_payload(self, groups_to_migrate: List[dict]) -> None:
        """
        Generate and log a consolidated payload that could be used to migrate all groups at once
        
        Args:
            groups_to_migrate: List of groups to migrate
        """
        # Create entities list
        entities = []
        
        for group in groups_to_migrate:
            # Extract source path
            _, source_path = self.extract_group_name_and_path(group['Source Url'])
            
            # Get just the group name (last part of the source path)
            group_name = source_path.split('/')[-1]
            
            # Get destination parent path
            dest_parent = group['Destination Parent Path']
            
            # Add to entities
            entities.append({
                "source_full_path": source_path,
                "source_type": "group_entity",
                "destination_slug": group_name,
                "destination_namespace": dest_parent,
                "migrate_projects": False
            })
        
        # Create full payload
        payload = {
            "configuration": {
                "url": SOURCE_GITLAB_ROOT,
                "access_token": SOURCE_ADMIN_ACCESS_TOKEN
            },
            "entities": entities
        }
        
        # Make a safe copy for logging
        safe_payload = copy.deepcopy(payload)
        safe_payload["configuration"]["access_token"] = "***REDACTED***"
        
        # Log as a consolidated payload that could be used in a single API call
        logger.info("=============== CONSOLIDATED API PAYLOAD ===============")
        logger.info("The following is a consolidated payload that could be used to migrate all groups in a single API call:")
        logger.info(json.dumps(safe_payload, indent=2))
        logger.info("=======================================================")
        
        # Output to a file for easier access
        consolidated_payload_file = f"consolidated_payload_{timestamp}.json"
        with open(consolidated_payload_file, "w") as f:
            json.dump(safe_payload, f, indent=2)
        logger.info(f"Consolidated payload also saved to: {consolidated_payload_file}")

    def initiate_transfer(self, source_group_url: str, source_parent_path: str, 
                          destination_parent_path: str, wave_name: str, wave_date: str) -> bool:
        """
        Initiate group transfer from source to destination
        
        Args:
            source_group_url: Full URL to the source group
            source_parent_path: Path to the parent group in source GitLab
            destination_parent_path: Path to the parent group in destination GitLab
            wave_name: Migration wave name
            wave_date: Migration wave date
            
        Returns:
            True if migration was successful or simulated in dry-run mode
        """
        # Extract source path
        _, source_path = self.extract_group_name_and_path(source_group_url)
        
        # Get just the group name (last part of the source path)
        group_name = source_path.split('/')[-1]
        
        # Construct the full destination path
        if destination_parent_path:
            full_dest_path = f"{destination_parent_path}/{group_name}"
        else:
            full_dest_path = group_name
            
        logger.info(f"Processing migration for group: {source_path}")
        logger.info(f"Wave: {wave_name}, Date: {wave_date}")
        logger.info(f"Source parent path: {source_parent_path}")
        logger.info(f"Destination parent path: {destination_parent_path}")
        logger.info(f"Group name: {group_name}")
        logger.info(f"Full destination path will be: {full_dest_path}")
        
        # In check-only mode, just check source and destination existence
        if self.check_only:
            # Check if source group exists
            if source_path not in self.existing_source_groups and source_path not in self.missing_source_groups:
                source_exists = self.check_group_exists(SOURCE_GITLAB_ROOT, SOURCE_ADMIN_ACCESS_TOKEN, source_path)
                if not source_exists:
                    logger.error(f"CHECK ONLY: Source group '{source_path}' does not exist")
                    return False
                    
            # Check if destination group already exists
            if full_dest_path not in self.existing_destination_groups:
                dest_exists = self.check_group_exists(DESTINATION_GITLAB_ROOT, DESTINATION_ADMIN_ACCESS_TOKEN, full_dest_path)
                if dest_exists:
                    logger.info(f"CHECK ONLY: Destination group '{full_dest_path}' already exists")
                    self.existing_destination_groups.add(full_dest_path)
                else:
                    logger.info(f"CHECK ONLY: Destination group '{full_dest_path}' does not exist and would need to be migrated")
                
            # In check-only mode, return True if source exists and destination does not
            return source_path in self.existing_source_groups and full_dest_path not in self.existing_destination_groups
        
        # Check if this group already exists on destination
        if full_dest_path in self.existing_destination_groups:
            logger.info(f"Group '{full_dest_path}' already exists on destination - skipping")
            return True
            
        # Check if this group will be migrated as part of a parent group
        parent_paths = self.get_parent_paths(source_path)
        for parent in parent_paths:
            if parent in self.migrated_groups:
                logger.info(f"Group '{source_path}' will be migrated as part of parent '{parent}' - skipping")
                return True
        
        if self.dry_run:
            logger.info(f"DRY RUN: Would migrate group '{source_path}' from {SOURCE_GITLAB_ROOT} to {DESTINATION_GITLAB_ROOT}")
            logger.info(f"DRY RUN: Destination will be '{full_dest_path}'")
            
            # For dry run, create the Direct Transfer API payload with the correct format
            transfer_payload = {
                "configuration": {
                    "url": SOURCE_GITLAB_ROOT,
                    "access_token": SOURCE_ADMIN_ACCESS_TOKEN
                },
                "entities": [
                    {
                        "source_full_path": source_path,
                        "source_type": "group_entity",
                        "destination_slug": group_name,
                        "destination_namespace": destination_parent_path,
                        "migrate_projects": False
                    }
                ]
            }
            
            # Set up the API endpoint for the bulk import
            url = f"{DESTINATION_GITLAB_ROOT}/api/v4/bulk_imports"
            headers = {'PRIVATE-TOKEN': DESTINATION_ADMIN_ACCESS_TOKEN}
            
            # Log the simulated API call
            self.make_api_request('POST', url, headers, transfer_payload)
            
            # Simulate polling for status
            poll_url = f"{DESTINATION_GITLAB_ROOT}/api/v4/bulk_imports/12345"
            entities_url = f"{DESTINATION_GITLAB_ROOT}/api/v4/bulk_imports/12345/entities"
            
            # Simulate checking import status
            simulated_statuses = ['created', 'started', 'finished']
            for status in simulated_statuses:
                # Simulate bulk import status
                simulated_response = {
                    'status_code': 200,
                    'body': {
                        'id': 12345,
                        'status': status,
                        'created_at': '2023-11-01T12:00:00Z',
                        'updated_at': '2023-11-01T12:30:00Z'
                    }
                }
                self.log_api_request('GET', poll_url, headers, dry_run=True)
                self.log_api_response(None, None, True, simulated_response)
                
                # Simulate entity status
                entity_status = 'finished' if status == 'finished' else 'created' if status == 'created' else 'started'
                entity_response = {
                    'status_code': 200,
                    'body': [
                        {
                            'id': 1,
                            'bulk_import_id': 12345,
                            'status': entity_status,
                            'source_full_path': source_path,
                            'destination_namespace': destination_parent_path,
                            'destination_slug': group_name,
                            "migrate_projects": False
                        }
                    ]
                }
                self.log_api_request('GET', entities_url, headers, dry_run=True)
                self.log_api_response(None, None, True, entity_response)
                
                logger.info(f"DRY RUN: Simulated bulk import status: {status}, entity status: {entity_status}")
                
                if status != 'finished':
                    logger.info(f"DRY RUN: Would wait 30 seconds before checking again")
            
            logger.info("DRY RUN: Simulated bulk import completed successfully")
            
            # Mark this group and all potential subgroups as migrated
            self.migrated_groups.add(source_path)
            # Also add the destination path to existing groups
            self.existing_destination_groups.add(full_dest_path)
            return True
            
        # In commit mode, create the correct bulk import API payload
        transfer_payload = {
            "configuration": {
                "url": SOURCE_GITLAB_ROOT,
                "access_token": SOURCE_ADMIN_ACCESS_TOKEN
            },
            "entities": [
                {
                    "source_full_path": source_path,
                    "source_type": "group_entity",
                    "destination_slug": group_name,
                    "destination_namespace": destination_parent_path,
                    "migrate_projects": False
                }
            ]
        }
        
        # Set up the API endpoint for the bulk import
        url = f"{DESTINATION_GITLAB_ROOT}/api/v4/bulk_imports"
        headers = {'PRIVATE-TOKEN': DESTINATION_ADMIN_ACCESS_TOKEN}
        
        # Make the API call to initiate bulk import
        response, error = self.make_api_request('POST', url, headers, transfer_payload)
        
        if error:
            logger.error(f"Error during bulk import initiation: {error}")
            return False
            
        if response and response.status_code in [200, 201, 202]:
            logger.info(f"Successfully initiated bulk import for group {source_path}")
            
            # Get the bulk import ID from the response
            import_id = response.json().get('id')
            if not import_id:
                logger.error("No import ID returned from bulk import initiation")
                return False
                
            # Poll for bulk import status
            if self.poll_bulk_import_status(import_id, source_path):
                logger.info(f"Bulk import completed successfully for group {source_path}")
                # Mark this group as migrated
                self.migrated_groups.add(source_path)
                # Also add the destination path to existing groups
                self.existing_destination_groups.add(full_dest_path)
                return True
            else:
                logger.error(f"Bulk import failed or timed out for group {source_path}")
                return False
        else:
            status_code = response.status_code if response else "unknown"
            response_text = response.text if response else "no response"
            logger.error(f"Failed to initiate bulk import: {status_code} - {response_text}")
            return False

    def poll_bulk_import_status(self, import_id: int, source_path: str,
                               timeout_minutes: int = 60, check_interval: int = 30) -> bool:
        """
        Poll for bulk import status until completion or timeout
        
        Args:
            import_id: Bulk import operation ID
            source_path: Source path of the group being imported
            timeout_minutes: Maximum time to wait for import in minutes
            check_interval: Time between status checks in seconds
            
        Returns:
            True if import completed successfully
        """
        bulk_import_url = f"{DESTINATION_GITLAB_ROOT}/api/v4/bulk_imports/{import_id}"
        entities_url = f"{DESTINATION_GITLAB_ROOT}/api/v4/bulk_imports/{import_id}/entities"
        headers = {'PRIVATE-TOKEN': DESTINATION_ADMIN_ACCESS_TOKEN}
        
        start_time = time.time()
        timeout_seconds = timeout_minutes * 60
        
        logger.info(f"Polling for bulk import status (timeout: {timeout_minutes} minutes)")
        
        while (time.time() - start_time) < timeout_seconds:
            # Check the overall bulk import status
            response, error = self.make_api_request('GET', bulk_import_url, headers)
            
            if error:
                logger.error(f"Error checking bulk import status: {error}")
                time.sleep(check_interval)
                continue
                
            if not response or response.status_code != 200:
                status_code = response.status_code if response else "unknown"
                response_text = response.text if response else "no response"
                logger.warning(f"Failed to get bulk import status: {status_code} - {response_text}")
                time.sleep(check_interval)
                continue
                
            import_status = response.json().get('status', '')
            logger.info(f"Bulk import status: {import_status}")
            
            # If the bulk import has failed, no need to check entities
            if import_status in ['failed', 'error']:
                logger.error(f"Bulk import failed with status: {import_status}")
                return False
                
            # Check the status of the specific entity we're importing
            entities_response, entities_error = self.make_api_request('GET', entities_url, headers)
            
            if entities_error:
                logger.error(f"Error checking bulk import entities: {entities_error}")
                time.sleep(check_interval)
                continue
                
            if not entities_response or entities_response.status_code != 200:
                status_code = entities_response.status_code if entities_response else "unknown"
                response_text = entities_response.text if entities_response else "no response"
                logger.warning(f"Failed to get bulk import entities: {status_code} - {response_text}")
                time.sleep(check_interval)
                continue
                
            # Find our entity in the list
            entities = entities_response.json()
            for entity in entities:
                if entity.get('source_full_path') == source_path:
                    entity_status = entity.get('status', '')
                    logger.info(f"Entity status for {source_path}: {entity_status}")
                    
                    if entity_status == 'finished':
                        return True
                    elif entity_status in ['failed', 'error']:
                        logger.error(f"Entity import failed with status: {entity_status}")
                        if 'error' in entity:
                            logger.error(f"Error details: {entity.get('error', 'No error details provided')}")
                        return False
                    
                    # Entity is still in progress, continue polling
                    break
            else:
                logger.warning(f"Could not find entity for {source_path} in bulk import entities")
                
            # If the overall import is finished but we haven't returned yet, check one more time
            if import_status == 'finished':
                logger.info("Bulk import is finished, checking final entity status...")
                entities_response, entities_error = self.make_api_request('GET', entities_url, headers)
                
                if not entities_error and entities_response and entities_response.status_code == 200:
                    entities = entities_response.json()
                    for entity in entities:
                        if entity.get('source_full_path') == source_path:
                            entity_status = entity.get('status', '')
                            logger.info(f"Final entity status for {source_path}: {entity_status}")
                            
                            if entity_status == 'finished':
                                return True
                            else:
                                logger.error(f"Entity import failed with final status: {entity_status}")
                                return False
                
                # If we can't determine the final status, assume failure
                logger.error("Could not determine final entity status after bulk import finished")
                return False
                
            # Wait before checking again
            logger.info(f"Waiting {check_interval} seconds before checking bulk import status again")
            time.sleep(check_interval)
            
        logger.error(f"Bulk import polling timed out after {timeout_minutes} minutes")
        return False

    def process_csv(self, csv_file: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Process CSV file containing migration data
        
        Args:
            csv_file: Path to CSV file
            
        Returns:
            Dictionary with results by wave
        """
        results = {}
        
        try:
            with open(csv_file, 'r') as f:
                reader = csv.DictReader(f)
                
                # Validate CSV headers
                required_fields = ['Wave Name', 'Wave Date', 'Source Url', 
                                 'Source Parent Path', 'Destination Parent Path']
                if reader.fieldnames:
                    missing_fields = [field for field in required_fields if field not in reader.fieldnames]
                    
                    if missing_fields:
                        logger.error(f"CSV is missing required fields: {', '.join(missing_fields)}")
                        return results
                else:
                    logger.error("CSV file appears to be empty or improperly formatted")
                    return results
                
                # First pass: collect all groups
                all_groups = []
                for row in reader:
                    # Skip empty rows
                    if not row['Source Url'].strip():
                        continue
                    all_groups.append(row)
                
                # First, check source groups to validate they exist
                self.check_source_groups(all_groups)
                
                # Then check which groups already exist on destination
                self.check_destination_groups(all_groups)
                
                # Analyze group hierarchy for both check-only and migration modes
                # This helps identify which groups would be skipped due to parent migrations
                groups_to_migrate = self.analyze_group_hierarchy(all_groups)

                # Generate consolidated API payload
                if groups_to_migrate:
                    self.generate_consolidated_payload(groups_to_migrate)

                if not self.check_only:
                    logger.info(f"Found {len(all_groups)} total groups, {len(groups_to_migrate)} need migration")
                else:
                    logger.info(f"CHECK ONLY: Checking {len(all_groups)} total groups, {len(groups_to_migrate)} would need migration")
                
                # Create a mapping of parent groups to their child groups for better reporting
                parent_to_children = {}
                for group in all_groups:
                    if group not in groups_to_migrate:
                        _, source_path = self.extract_group_name_and_path(group['Source Url'])
                        
                        # Check if this is being skipped because it's part of a parent migration
                        skip_parent = None
                        for parent in self.get_parent_paths(source_path):
                            if parent in self.migrated_groups:
                                skip_parent = parent
                                # Add this group to the parent's children list
                                if parent not in parent_to_children:
                                    parent_to_children[parent] = []
                                parent_to_children[parent].append(source_path)
                                break
                
                # Log the parent-child relationships for skipped groups
                if parent_to_children:
                    if self.check_only:
                        logger.info("\n===== Groups That Would Be Skipped Due to Parent Migration =====")
                    else:
                        logger.info("\n===== Groups Being Skipped Due to Parent Migration =====")
                        
                    for parent, children in parent_to_children.items():
                        if self.check_only:
                            logger.info(f"Parent group that would be migrated: {parent}")
                            logger.info(f"  Child groups that would be skipped ({len(children)}):")
                        else:
                            logger.info(f"Parent group that will be migrated: {parent}")
                            logger.info(f"  Child groups that will be skipped ({len(children)}):")
                            
                        # Group children by directory level for better organization
                        by_level = {}
                        for child in children:
                            level = child.count('/')
                            if level not in by_level:
                                by_level[level] = []
                            by_level[level].append(child)
                        
                        # Print children sorted by level (depth)
                        for level in sorted(by_level.keys()):
                            for child in sorted(by_level[level]):
                                logger.info(f"    - {child}")
                                
                    logger.info("========================================================\n")
                
                # Process groups that need migration
                for group in groups_to_migrate:
                    wave_name = group['Wave Name']
                    wave_date = group['Wave Date']
                    source_url = group['Source Url']
                    source_parent = group['Source Parent Path']
                    dest_parent = group['Destination Parent Path']
                    
                    # Initialize wave in results if not exists
                    if wave_name not in results:
                        results[wave_name] = []
                        
                    # Initiate transfer or just check in check-only mode
                    success = self.initiate_transfer(
                        source_url, source_parent, dest_parent, wave_name, wave_date)
                        
                    # Record result
                    results[wave_name].append({
                        'source_url': source_url,
                        'source_parent': source_parent,
                        'dest_parent': dest_parent,
                        'success': success,
                        'action': 'checked' if self.check_only else 'migrated'
                    })
                    
                    # Add a small delay to avoid overloading the API
                    time.sleep(1)
                    
                # Add skipped groups to results (for both check-only and migration modes)
                for group in all_groups:
                    if group not in groups_to_migrate:
                        wave_name = group['Wave Name']
                        
                        # Initialize wave in results if not exists
                        if wave_name not in results:
                            results[wave_name] = []
                            
                        # Extract paths to determine skip reason
                        _, source_path = self.extract_group_name_and_path(group['Source Url'])
                        group_name = source_path.split('/')[-1]
                        dest_parent = group['Destination Parent Path']
                        if dest_parent:
                            full_dest_path = f"{dest_parent}/{group_name}"
                        else:
                            full_dest_path = group_name
                        
                        # Determine skip reason
                        skip_reason = ""
                        skip_parent = None
                        if source_path in self.missing_source_groups:
                            skip_reason = "does not exist on source"
                        elif full_dest_path in self.existing_destination_groups:
                            skip_reason = "already exists on destination"
                        else:
                            # Check if it's part of a parent migration
                            for parent in self.get_parent_paths(source_path):
                                if parent in self.migrated_groups:
                                    skip_parent = parent
                                    if self.check_only:
                                        skip_reason = f"would be migrated with parent '{parent}'"
                                    else:
                                        skip_reason = f"will be migrated with parent '{parent}'"
                                    break
                            if not skip_reason:
                                skip_reason = "unknown reason"
                        
                        # Record as skipped with reason
                        action_type = 'would_be_skipped' if self.check_only else 'skipped'
                        results[wave_name].append({
                            'source_url': group['Source Url'],
                            'source_parent': group['Source Parent Path'],
                            'dest_parent': group['Destination Parent Path'],
                            'success': True,
                            'action': action_type,
                            'skip_reason': skip_reason,
                            'skip_parent': skip_parent
                        })
                    
        except FileNotFoundError:
            logger.error(f"CSV file not found: {csv_file}")
        except Exception as e:
            logger.error(f"Error processing CSV file: {str(e)}")
            
        return results

    def print_summary(self, results: Dict[str, List[Dict[str, Any]]]) -> None:
        """Print summary of migration results"""
        logger.info("\n========== MIGRATION SUMMARY ==========")
        
        total_groups = 0
        total_migrated = 0
        total_skipped = 0
        total_failed = 0
        total_checked = 0
        total_would_be_skipped = 0
        
        # Keep track of destinations we've verified exist
        verified_destinations = set(self.existing_destination_groups)
        
        for wave_name, items in results.items():
            wave_total = len(items)
            
            if self.check_only:
                wave_checked = sum(1 for item in items if item.get('success') and item.get('action') == 'checked')
                wave_would_be_skipped = sum(1 for item in items if item.get('action') == 'would_be_skipped')
                wave_failed = sum(1 for item in items if not item.get('success'))
                
                logger.info(f"Wave: {wave_name}")
                logger.info(f"  Total Groups: {wave_total}")
                logger.info(f"  Checked Successfully: {wave_checked}")
                logger.info(f"  Would Be Skipped: {wave_would_be_skipped}")
                
                # Count skip reasons for check-only mode
                if wave_would_be_skipped > 0:
                    skip_reasons = {}
                    for item in items:
                        if item.get('action') == 'would_be_skipped':
                            reason = item.get('skip_reason', 'unknown reason')
                            # Only count as "already exists" if we've actually verified it exists
                            if "already exists on destination" in reason:
                                _, source_path = self.extract_group_name_and_path(item['source_url'])
                                group_name = source_path.split('/')[-1]
                                dest_parent = item.get('dest_parent', '')
                                if dest_parent:
                                    full_dest_path = f"{dest_parent}/{group_name}"
                                else:
                                    full_dest_path = group_name
                                    
                                if full_dest_path not in verified_destinations:
                                    # If we haven't verified this exists, use a more generic reason
                                    reason = "skipped for other reasons"
                                    
                            skip_reasons[reason] = skip_reasons.get(reason, 0) + 1
                    
                    # Print skip reasons
                    for reason, count in skip_reasons.items():
                        logger.info(f"    - {count} groups would be skipped: {reason}")
                
                logger.info(f"  Validation Failed: {wave_failed}")
                
                total_groups += wave_total
                total_checked += wave_checked
                total_would_be_skipped += wave_would_be_skipped
                total_failed += wave_failed
            else:
                wave_migrated = sum(1 for item in items if item.get('success') and item.get('action') == 'migrated')
                wave_skipped = sum(1 for item in items if item.get('action') == 'skipped')
                wave_failed = sum(1 for item in items if not item.get('success'))
                
                logger.info(f"Wave: {wave_name}")
                logger.info(f"  Total Groups: {wave_total}")
                logger.info(f"  Migrated: {wave_migrated}")
                logger.info(f"  Skipped: {wave_skipped}")
                if wave_skipped > 0:
                    # Count skip reasons
                    skip_reasons = {}
                    for item in items:
                        if item.get('action') == 'skipped':
                            reason = item.get('skip_reason', 'unknown reason')
                            # Only count as "already exists" if we've actually verified it exists
                            if "already exists on destination" in reason:
                                _, source_path = self.extract_group_name_and_path(item['source_url'])
                                group_name = source_path.split('/')[-1]
                                dest_parent = item.get('dest_parent', '')
                                if dest_parent:
                                    full_dest_path = f"{dest_parent}/{group_name}"
                                else:
                                    full_dest_path = group_name
                                    
                                if full_dest_path not in verified_destinations:
                                    # If we haven't verified this exists, use a more generic reason
                                    reason = "skipped for other reasons"
                            
                            skip_reasons[reason] = skip_reasons.get(reason, 0) + 1
                    
                    # Print skip reasons
                    for reason, count in skip_reasons.items():
                        logger.info(f"    - {count} groups skipped: {reason}")
                
                logger.info(f"  Failed: {wave_failed}")
                
                total_groups += wave_total
                total_migrated += wave_migrated
                total_skipped += wave_skipped
                total_failed += wave_failed
        
        # Overall results - moved this outside the wave loop
        logger.info("\nOverall Results:")
        logger.info(f"  Total Groups: {total_groups}")
        
        if self.check_only:
            logger.info(f"  Checked Successfully: {total_checked}")
            logger.info(f"  Would Be Skipped: {total_would_be_skipped}")
            logger.info(f"  Validation Failed: {total_failed}")
            
            if total_groups > 0:
                success_rate = ((total_checked + total_would_be_skipped) / total_groups) * 100
                logger.info(f"  Success Rate: {success_rate:.2f}%")
            else:
                logger.info(f"  Success Rate: N/A")
                
            # Organize skipped groups by parent for clearer reporting
            parent_groups = {}
            for wave_name, items in results.items():
                for item in items:
                    if item.get('action') == 'would_be_skipped' and 'skip_parent' in item and item['skip_parent']:
                        parent = item['skip_parent']
                        if parent not in parent_groups:
                            parent_groups[parent] = []
                        _, source_path = self.extract_group_name_and_path(item['source_url'])
                        parent_groups[parent].append(source_path)
            
            # Add extra information about skipped groups if available
            if parent_groups:
                logger.info("\nGroups That Would Be Skipped By Parent:")
                for parent, children in parent_groups.items():
                    logger.info(f"  Parent '{parent}' would include these child groups:")
                    # Group children by directory level for better organization
                    by_level = {}
                    for child in children:
                        level = child.count('/')
                        if level not in by_level:
                            by_level[level] = []
                        by_level[level].append(child)
                    
                    # Print children sorted by level (depth)
                    for level in sorted(by_level.keys()):
                        for child in sorted(by_level[level]):
                            logger.info(f"    - {child}")
        else:
            logger.info(f"  Migrated: {total_migrated}")
            logger.info(f"  Skipped: {total_skipped}")
            logger.info(f"  Failed: {total_failed}")
            
            if total_groups > 0:
                success_rate = ((total_migrated + total_skipped) / total_groups) * 100
                logger.info(f"  Success Rate: {success_rate:.2f}%")
            else:
                logger.info(f"  Success Rate: N/A")
                
            # Organize skipped groups by parent for clearer reporting
            parent_groups = {}
            for wave_name, items in results.items():
                for item in items:
                    if item.get('action') == 'skipped' and 'skip_parent' in item and item['skip_parent']:
                        parent = item['skip_parent']
                        if parent not in parent_groups:
                            parent_groups[parent] = []
                        _, source_path = self.extract_group_name_and_path(item['source_url'])
                        parent_groups[parent].append(source_path)
            
            # Add extra information about skipped groups if available
            if parent_groups:
                logger.info("\nSkipped Groups By Parent:")
                for parent, children in parent_groups.items():
                    logger.info(f"  Parent '{parent}' will include these child groups:")
                    # Group children by directory level for better organization
                    by_level = {}
                    for child in children:
                        level = child.count('/')
                        if level not in by_level:
                            by_level[level] = []
                        by_level[level].append(child)
                    
                    # Print children sorted by level (depth)
                    for level in sorted(by_level.keys()):
                        for child in sorted(by_level[level]):
                            logger.info(f"    - {child}")
        
        mode = "CHECK ONLY" if self.check_only else "DRY RUN" if self.dry_run else "COMMIT"
        logger.info(f"\nExecution Mode: {mode}")
        logger.info("========================================\n")
        
        # Print log file locations
        logger.info("Log Files:")
        logger.info(f"  Main Log: {main_log_file}")
        logger.info(f"  Missing Source Groups: {missing_sources_log_file}")
        logger.info(f"  Existing Destination Groups: {existing_dest_log_file}")
        
        consolidated_payload_file = f"consolidated_payload_{timestamp}.json"
        entities_only_file = f"entities_only_{timestamp}.json"
        logger.info(f"  Consolidated API Payload: {consolidated_payload_file}")
        logger.info(f"  Entities-Only Array: {entities_only_file}")

    def generate_consolidated_payload(self, groups_to_migrate: List[dict]) -> None:
        """
        Generate and log a consolidated payload that could be used to migrate all groups at once
        
        Args:
            groups_to_migrate: List of groups to migrate
        """
        # Create entities list
        entities = []
        
        for group in groups_to_migrate:
            # Extract source path
            _, source_path = self.extract_group_name_and_path(group['Source Url'])
            
            # Get just the group name (last part of the source path)
            group_name = source_path.split('/')[-1]
            
            # Get destination parent path
            dest_parent = group['Destination Parent Path']
            
            # Add to entities
            entities.append({
                "source_full_path": source_path,
                "source_type": "group_entity",
                "destination_slug": group_name,
                "destination_namespace": dest_parent,
                "migrate_projects": False
            })
        
        # Create full payload
        payload = {
            "configuration": {
                "url": SOURCE_GITLAB_ROOT,
                "access_token": SOURCE_ADMIN_ACCESS_TOKEN
            },
            "entities": entities
        }
        
        # Make a safe copy for logging
        safe_payload = copy.deepcopy(payload)
        safe_payload["configuration"]["access_token"] = "***REDACTED***"
        
        # Log as a consolidated payload that could be used in a single API call
        logger.info("=============== CONSOLIDATED API PAYLOAD ===============")
        logger.info("The following is a consolidated payload that could be used to migrate all groups in a single API call:")
        logger.info(json.dumps(safe_payload, indent=2))
        logger.info("=======================================================")
        
        # Output to a file for easier access
        consolidated_payload_file = f"consolidated_payload_{timestamp}.json"
        with open(consolidated_payload_file, "w") as f:
            json.dump(safe_payload, f, indent=2)
        logger.info(f"Consolidated payload also saved to: {consolidated_payload_file}")
        
        # Also output just the entities part for easy copying
        logger.info("\n=============== CONSOLIDATED ENTITIES ONLY ===============")
        logger.info("The following entities array can be used in the API call for bulk migration:")
        logger.info(json.dumps(entities, indent=2))
        logger.info("==========================================================")
        
        # Output just the entities to a separate file
        entities_only_file = f"entities_only_{timestamp}.json"
        with open(entities_only_file, "w") as f:
            json.dump(entities, f, indent=2)
        logger.info(f"Entities-only array also saved to: {entities_only_file}")

def main():
    """Main entry point for the script"""
    parser = argparse.ArgumentParser(description='GitLab Group Migration Tool')
    parser.add_argument('csv_file', help='CSV file containing groups to migrate')
    parser.add_argument('--commit', action='store_true', 
                      help='Execute actual migration (without this flag, runs in dry-run mode)')
    parser.add_argument('--check-only', action='store_true',
                      help='Only check if groups exist on source and destination, no migrations')
    parser.add_argument('--debug', action='store_true',
                      help='Enable detailed API logging (can be verbose)')
    args = parser.parse_args()
    
    # Check if environment variables are set
    missing_vars = []
    for var in ['SOURCE_GITLAB_ROOT', 'SOURCE_ADMIN_ACCESS_TOKEN', 
               'DESTINATION_GITLAB_ROOT', 'DESTINATION_ADMIN_ACCESS_TOKEN']:
        if not os.environ.get(var):
            missing_vars.append(var)
            
    if missing_vars:
        logger.error("Missing required environment variables:")
        for var in missing_vars:
            logger.error(f"  {var}")
        sys.exit(1)
        
    # Determine the execution mode
    check_only = args.check_only
    dry_run = not args.commit
    debug = args.debug
    
    # Initialize migrator
    migrator = GitLabMigrator(dry_run=dry_run, check_only=check_only, debug=debug)
    
    # Process CSV file
    logger.info(f"Processing CSV file: {args.csv_file}")
    results = migrator.process_csv(args.csv_file)
    
    # Print summary
    migrator.print_summary(results)
    
    logger.info(f"Migration completed. See log files for details")


if __name__ == "__main__":
    main()