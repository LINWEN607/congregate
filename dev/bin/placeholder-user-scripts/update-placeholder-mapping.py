# Source host,Import type,Source user identifier,Source user name,Source username,GitLab username,GitLab public email,GitLab importSourceUserId,GitLab assigneeUserId,GitLab clientMutationId
# gitlab.com,email,123456,John Doe,johndoe,johndoe,johndoe@example.com,gid://gitlab/ImportSourceUser/123456,123457,123456789
# ...
# Replace the placeholders with your actual data.
# The "GitLab importSourceUserId", "GitLab assigneeUserId", and "GitLab clientMutationId" fields are used for the reassign_placeholder_user function.

# The "Source host", "Import type", "Source user identifier", "Source user name", and "Source username" fields are used for informational purposes.
# The "GitLab username" and "GitLab public email" fields are not used in the script but can be helpful for manual verification.


import csv
import requests
import logging
import os
from typing import Dict, List

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# GitLab API configuration
DESTINATION_GITLAB_ROOT = os.environ.get("DESTINATION_GITLAB_ROOT", "https://gitlab.gmgldemo.net/api")
DESTINATION_GITLAB_GRAPHQL_URL = f"{DESTINATION_GITLAB_ROOT}/api/graphql"
DESTINATION_GITLAB_API_URL = f"{DESTINATION_GITLAB_ROOT}/api/v4"
DESTINATION_ADMIN_OR_OWNER_ACCESS_TOKEN = os.environ.get("DESTINATION_ADMIN_ACCESS_TOKEN", "")
DRY_RUN = os.environ.get("DRY_RUN", "True").lower() == "true"

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
                    'importSourceUserId': row['GitLab importSourceUserId'],
                    'assigneeUserId': row['GitLab assigneeUserId'],
                    'clientMutationId': row['GitLab clientMutationId']
                })
        logger.info(f"Successfully read {len(data)} rows from {file_path}")
        return data
    except Exception as e:
        logger.error(f"Error reading CSV file: {str(e)}")
        raise

def reassign_placeholder_user(input_data: Dict[str, str]):
    """
    Make a GraphQL mutation call to reassign a placeholder user.
    """

    if DRY_RUN:
        logger.info(f"DRY RUN: Would reassign placeholder user with sourceUserId {input_data['importSourceUserId']} to assigneeUserId {input_data['assigneeUserId']}")
        return True

    headers = {
        "Authorization": f"Bearer {DESTINATION_ADMIN_OR_OWNER_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    variables = {
        "assigneeUserId": input_data['assigneeUserId'],
        "clientMutationId": input_data['clientMutationId'],
        "importSourceUserId": input_data['importSourceUserId']
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
            return False
        
        result = data["data"]["importSourceUserReassign"]
        if result["errors"]:
            logger.error(f"Reassignment failed for sourceUserId {input_data['importSourceUserId']}: {result['errors']}")
            return False
        
        status = result["importSourceUser"]["status"]
        reassigned_by = result["importSourceUser"]["reassignedByUser"]["name"]
        logger.info(f"Successfully reassigned placeholder user with sourceUserId {input_data['importSourceUserId']}. Status: {status}, Reassigned by: {reassigned_by}")
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

        for row in data:
            if reassign_placeholder_user(row):
                success_count += 1
            else:
                failure_count += 1

        logger.info(f"Reassignment process completed. Successes: {success_count}, Failures: {failure_count}")

    except Exception as e:
        logger.error(f"An error occurred during execution: {str(e)}")

if __name__ == "__main__":
    csv_file_path = "demo_placeholder_users.csv"  # Replace with your CSV file path
    main(csv_file_path)
