"""
GitLab Placeholder User Reassignment Tool
----------------------------------------

This script automates the reassignment of placeholder users in GitLab
following a migration or import. It reads user mapping data from a CSV file
and uses the GitLab GraphQL API to reassign placeholder users to actual GitLab users.

Features:
- Processes CSV files containing user mapping information
- Makes GraphQL API calls to GitLab to reassign users
- Supports dry-run mode to preview changes without applying them
- Logs all operations and outputs detailed results
- Records failed reassignments to a separate CSV file for retry

Usage:
  python3 reassign_placeholder_users.py [--commit] [input_csv_file]

  --commit    Execute the actual reassignments (default is dry-run mode)
  input_csv_file    Path to the CSV file containing user mappings (default: placeholder_users.csv)

CSV Format:
  The CSV file should include the following headers:
  - Source host
  - Import type
  - Source user identifier
  - Source user name
  - Source username
  - GitLab username
  - GitLab public email
  - GitLab importSourceUserId
  - GitLab assigneeUserId
  - GitLab clientMutationId

Environment Variables:
  DESTINATION_GITLAB_ROOT: Base URL for the GitLab instance
  DESTINATION_ADMIN_ACCESS_TOKEN: Admin access token for GitLab API authentication
"""


import csv
import requests
import logging
import os
import datetime
import argparse
from typing import Dict, List

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Parse command line arguments
parser = argparse.ArgumentParser(description='GitLab Placeholder User Reassignment Tool')
parser.add_argument('--commit', action='store_true', help='Execute the actual reassignments (default is dry-run mode)')
parser.add_argument('input_csv_file', nargs='?', default="placeholder_users.csv", 
                    help='Path to the CSV file containing user mappings')
args = parser.parse_args()

# GitLab API configuration
DESTINATION_GITLAB_ROOT = os.environ.get("DESTINATION_GITLAB_ROOT", "")
DESTINATION_GITLAB_GRAPHQL_URL = f"{DESTINATION_GITLAB_ROOT}/api/graphql"
DESTINATION_GITLAB_API_URL = f"{DESTINATION_GITLAB_ROOT}/api/v4"
DESTINATION_ADMIN_OR_OWNER_ACCESS_TOKEN = os.environ.get("DESTINATION_ADMIN_ACCESS_TOKEN", "")
DRY_RUN = not args.commit
FAILURE_FILE_PATH = ""

# GraphQL mutation
REASSIGN_PLACEHOLDER_USER_MUTATION = """
mutation($assigneeUserId: UserID!, $clientMutationId: String, $importSourceUserId: ImportSourceUserID!) {
    importSourceUserReassign ( 
        input: {
                assigneeUserId: $assigneeUserId ,
                clientMutationId: $clientMutationId ,
                id: $importSourceUserId
        }
    ) 
    {
        clientMutationId
        importSourceUser {
            status
            reassignedByUser {
                name
            }
        }
        errors
    }
}
"""

def read_csv_file(file_path: str) -> List[Dict[str, str]]:
    """
    Read the CSV file and return a list of dictionaries with the required fields.
    """
    data = []
    try:
        with open(file_path, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                data.append({
                    'Source host': row['Source host'],
                    'Import type': row['Import type'],
                    'Source user identifier': row['Source user identifier'],
                    'Source user name': row['Source user name'],
                    'Source username': row['Source username'],
                    'GitLab username': row['GitLab username'],
                    'GitLab public email': row['GitLab public email'],
                    'GitLab importSourceUserId': row['GitLab importSourceUserId'],
                    'GitLab assigneeUserId': row['GitLab assigneeUserId'],
                    'GitLab clientMutationId': row['GitLab clientMutationId']
                })
        logger.info(f"Successfully read {len(data)} rows from {file_path}")
        return data
    except Exception as e:
        logger.error(f"Error reading CSV file: {str(e)}")
        raise

def reassign_placeholder_user(input_data: Dict[str, str], FAILURE_FILE_PATH: str)-> bool:
    """
    Make a GraphQL mutation call to reassign a placeholder user.
    """

    if DRY_RUN:
        logger.info(f"DRY RUN: Would reassign placeholder user {input_data['Source username']} with sourceUserId {input_data['GitLab importSourceUserId']} to assigneeUserId {input_data['GitLab assigneeUserId']}")
        return True

    headers = {
        "Authorization": f"Bearer {DESTINATION_ADMIN_OR_OWNER_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    variables = {
        "assigneeUserId": input_data['GitLab assigneeUserId'],
        "clientMutationId": input_data['GitLab clientMutationId'],
        "importSourceUserId": input_data['GitLab importSourceUserId']
    }

    logger.info(f"Attempting to reassign placeholder user with variables: {variables}")

    try:
        response = requests.post(
            f"{DESTINATION_GITLAB_GRAPHQL_URL}",
            json={"query": REASSIGN_PLACEHOLDER_USER_MUTATION, "variables": variables},
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()

        if "errors" in data:
            logger.error(f"GraphQL mutation returned errors: {data['errors']}")
            with open(FAILURE_FILE_PATH, 'w') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=list(input_data.keys()))
                writer.writerow(input_data)
            return False
        
        result = data["data"]["importSourceUserReassign"]
        if result["errors"]:
            logger.error(f"Reassignment failed for sourceUserId {input_data['GitLab importSourceUserId']}: {result['errors']}")
            with open(FAILURE_FILE_PATH, 'w') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=list(input_data.keys()))
                writer.writerow(input_data)
            return False
        
        status = result["importSourceUser"]["status"]
        reassigned_by = result["importSourceUser"]["reassignedByUser"]["name"]
        logger.info(f"Successfully reassigned placeholder user with sourceUserId {input_data['GitLab importSourceUserId']}. Status: {status}, Reassigned by: {reassigned_by}")
        return True

    except requests.RequestException as e:
        logger.error(f"Error making request to GitLab API: {str(e)}")
        return False

def main(csv_file_path: str):
    """
    Main function to read CSV and reassign placeholder users.
    """
    try:
        data = read_csv_file(csv_file_path)
        success_count = 0
        failure_count = 0

        logger.info(f"Running in {'DRY RUN' if DRY_RUN else 'LIVE'} mode")
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        FAILURE_FILE_PATH = f"{timestamp}-{csv_file_path}-failures.csv"
        
        # Create a failure file
        with open(FAILURE_FILE_PATH, 'w') as csvfile:
            fieldnames = ["Source host", "Import type", "Source user identifier", "Source user name", "Source username", "GitLab username", "GitLab public email", "GitLab importSourceUserId", "GitLab assigneeUserId", "GitLab clientMutationId"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

        # TODO: This should probably pass the entire dataset to collect failures and successes (counts and data) for output rather than output-per-row calls to the function
        for row in data:
            if reassign_placeholder_user(row, FAILURE_FILE_PATH):
                success_count += 1
            else:
                failure_count += 1

        logger.info(f"Reassignment process completed. Successes: {success_count}, Failures: {failure_count}")

    except Exception as e:
        logger.error(f"An error occurred during execution: {str(e)}")

if __name__ == "__main__":
    print(f"Running in {'DRY RUN' if DRY_RUN else 'COMMIT'} mode")
    main(args.input_csv_file)