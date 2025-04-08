"""
GitLab Placeholder User Reassignment Tool
----------------------------------------

This script automates the reassignment of placeholder users in GitLab
following a migration or import. It takes a mapping file and submits it
to the GitLab API to reassign placeholder users to actual GitLab users.

Features:
- Uploads a CSV file containing user mapping information to GitLab API
- Supports dry-run mode to preview changes without applying them
- Logs all operations and outputs detailed results

Usage:
  python3 update-placeholder-mapping.py [--commit] [input_csv_file]

  --commit          Execute the actual reassignments (default is dry-run mode)
  input_csv_file    Path to the CSV file containing the updated user mappings

Environment Variables:
  DESTINATION_GITLAB_ROOT: Base URL for the GitLab instance
  DESTINATION_ADMIN_ACCESS_TOKEN: Admin access token for GitLab API authentication
"""

from pydoc import text
import requests
import logging
import os
import datetime
import argparse
import sys
from typing import Dict, List

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Parse command line arguments
parser = argparse.ArgumentParser(description='GitLab Placeholder User Reassignment Tool')
parser.add_argument('--commit', action='store_true', help='Execute the actual reassignments (default is dry-run mode)')
parser.add_argument('input_csv_file', nargs='?', default="placeholder_users.csv", 
                    help='Path to the CSV file containing user mappings')
parser.add_argument('--group-id', required=True, help='ID of the GitLab group to perform reassignments')
args = parser.parse_args()

# GitLab API configuration
DESTINATION_GITLAB_ROOT = os.environ.get("DESTINATION_GITLAB_ROOT", "")
if not DESTINATION_GITLAB_ROOT:
    logger.error("DESTINATION_GITLAB_ROOT environment variable is not set")
    sys.exit(1)

DESTINATION_GITLAB_API_URL = f"{DESTINATION_GITLAB_ROOT}/api/v4"
DESTINATION_ADMIN_ACCESS_TOKEN = os.environ.get("DESTINATION_ADMIN_ACCESS_TOKEN", "")
if not DESTINATION_ADMIN_ACCESS_TOKEN:
    logger.error("DESTINATION_ADMIN_ACCESS_TOKEN environment variable is not set")
    sys.exit(1)

DRY_RUN = not args.commit
GROUP_ID = args.group_id

def upload_placeholder_reassignments(file_path: str, group_id: str) -> bool:
    """
    Upload the placeholder reassignment CSV file to GitLab API.
    """
    if DRY_RUN:
        logger.info(f"DRY RUN: Would upload {file_path} to group ID {group_id}")
        return True

    logger.info(f"Uploading placeholder reassignment file {file_path} to group ID {group_id}")

    try:
        headers = {
            "PRIVATE-TOKEN": DESTINATION_ADMIN_ACCESS_TOKEN
        }
        
        url = f"{DESTINATION_GITLAB_API_URL}/groups/{group_id}/placeholder_reassignments"
        
        with open(file_path, 'rb') as file:
            files = {
                'file': file
            }
            
            response = requests.post(
                url,
                headers=headers,
                files=files,
                timeout=60
            )
        
        response.raise_for_status()
        
        logger.info(f"Successfully uploaded placeholder reassignment file. Response status: {response.status_code}")
        logger.info(f"Response content: {response.text}")
        return True
        
    except requests.RequestException as e:
        logger.error(f"Error uploading placeholder reassignment file: {str(e)}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Response status code: {e.response.status_code}")
            logger.error(f"Response content: {e.response.text}")
        return False

def main(csv_file_path: str, group_id: str):
    """
    Main function to upload CSV file for placeholder user reassignments.
    """
    try:
        if not os.path.exists(csv_file_path):
            logger.error(f"File not found: {csv_file_path}")
            sys.exit(1)
            
        logger.info(f"Running in {'DRY RUN' if DRY_RUN else 'LIVE'} mode")
        
        result = upload_placeholder_reassignments(csv_file_path, group_id)
        
        if result:
            logger.info("Placeholder reassignment process submitted successfully")
        else:
            logger.error("Failed to submit placeholder reassignment process")
            sys.exit(1)

    except Exception as e:
        logger.error(f"An error occurred during execution: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    print(f"Running in {'DRY RUN' if DRY_RUN else 'COMMIT'} mode")
    main(args.input_csv_file, GROUP_ID)