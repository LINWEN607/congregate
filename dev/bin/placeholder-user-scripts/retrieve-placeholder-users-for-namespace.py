"""
GitLab Placeholder Users Export Script

This script retrieves placeholder users from a GitLab group and exports them to a CSV file.
The exported CSV can be used as input for the user reassignment process during GitLab migrations.

Features:
- Retrieves all placeholder users from a specified GitLab group using GraphQL API with pagination
- Exports user data to a CSV file in the required format for user reassignment
- Includes error handling and detailed logging

Prerequisites:
- Set DESTINATION_GITLAB_ROOT environment variable (e.g., "https://gitlab.example.com")
- Set DESTINATION_ADMIN_ACCESS_TOKEN environment variable with an admin access token

Usage:
1. Set the required environment variables
2. Modify the group_full_path and customer_name variables in the main function with your target group path
3. Run the script to generate the CSV file

Example usage:
```
export DESTINATION_GITLAB_ROOT="https://gitlab.example.com"
export DESTINATION_ADMIN_ACCESS_TOKEN="glpat-xxxxxxxxxxxxxxxxxxxx"
python retrieve-placeholcer-users-for-namespace.py
```

Output CSV Format:
The generated CSV includes these columns:
- Source host: The source GitLab instance hostname
- Import type: Type of import (email, username)
- Source user identifier: User ID from the source system
- Source user name: Full name from the source system
- Source username: Username from the source system
- GitLab username: (Empty, to be filled by the user)
- GitLab public email: (Empty, to be filled by the user)
- GitLab importSourceUserId: ID of the import source user
- GitLab assigneeUserId: (Empty, to be filled by the user)
- GitLab clientMutationId: (Empty, to be filled by the user)

Example CSV output:
Source host,Import type,Source user identifier,Source user name,Source username,GitLab username,GitLab public email,GitLab importSourceUserId,GitLab assigneeUserId,GitLab clientMutationId
gitlab.com,email,123456,John Doe,johndoe,,,gid://gitlab/ImportSourceUser/123456,,
"""

import requests
import os
import logging
import csv
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# GitLab API configuration
DESTINATION_GITLAB_ROOT  = os.environ.get("DESTINATION_GITLAB_ROOT", "")
DESTINATION_GITLAB_GRAPHQL_URL = f"{DESTINATION_GITLAB_ROOT}/api/graphql"
DESTINATION_GITLAB_API_URL = f"{DESTINATION_GITLAB_ROOT}/api/v4"
DESTINATION_ADMIN_ACCESS_TOKEN = os.environ.get("DESTINATION_ADMIN_ACCESS_TOKEN", "")

FIND_PLACEHOLDERS_FOR_NAMESPACE_QUERY = """
query($fullPath: ID!, $after: String){
  namespace(fullPath: $fullPath) {
    importSourceUsers(first: 100, after: $after) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        id
        importType
        sourceName
        sourceHostname
        sourceUsername
        sourceUserIdentifier
      }
    }
  }
}
"""

def get_placeholder_users(group_full_path):
    """
    Retrieve placeholder users for a given GitLab group using GraphQL API with pagination.

    Args:
        group_full_path (str): The full path of the GitLab group.

    Returns:
        list: A list of dictionaries containing placeholder user information.

    Raises:
        requests.RequestException: If there's an error with the API request.
        KeyError: If the response doesn't contain the expected data structure.
    """
    headers = {
        "Authorization": f"Bearer {DESTINATION_ADMIN_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    all_placeholder_users = []
    has_next_page = True
    after_cursor = None
    total_retrieved = 0

    logger.info(f"Attempting to retrieve placeholder users for group: {group_full_path}")

    while has_next_page:
        variables = {
            "fullPath": group_full_path,
            "after": after_cursor
        }

        try:
            logger.debug(f"Sending GraphQL query to GitLab API (pagination cursor: {after_cursor})")
            response = requests.post(
                f"{DESTINATION_GITLAB_GRAPHQL_URL}",
                json={"query": FIND_PLACEHOLDERS_FOR_NAMESPACE_QUERY, "variables": variables},
                headers=headers,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            
            if "errors" in data:
                logger.error(f"GraphQL query returned errors: {data['errors']}")
                raise ValueError(f"GraphQL query returned errors: {data['errors']}")
            
            page_info = data["data"]["namespace"]["importSourceUsers"]["pageInfo"]
            placeholder_users = data["data"]["namespace"]["importSourceUsers"]["nodes"]
            
            all_placeholder_users.extend(placeholder_users)
            total_retrieved += len(placeholder_users)
            
            # Update pagination info
            has_next_page = page_info["hasNextPage"]
            after_cursor = page_info["endCursor"] if has_next_page else None
            
            logger.info(f"Retrieved {len(placeholder_users)} placeholder users in this page. Total so far: {total_retrieved}")
            
        except requests.RequestException as e:
            logger.error(f"Error making request to GitLab API: {str(e)}")
            raise
        except KeyError as e:
            logger.error(f"Unexpected response structure: {str(e)}")
            raise
        except ValueError as e:
            logger.error(str(e))
            raise

    logger.info(f"Successfully retrieved all {total_retrieved} placeholder users")
    return all_placeholder_users

def write_to_csv(placeholder_users, output_file):
    """
    Write placeholder users data to a CSV file.

    Args:
        placeholder_users (list): List of dictionaries containing placeholder user data.
        output_file (str): Name of the output CSV file.
    """

    fieldnames = [
        "Source host",
        "Import type",
        "Source user identifier",
        "Source user name",
        "Source username",
        "GitLab username",
        "GitLab public email",
        "GitLab importSourceUserId",
        "GitLab assigneeUserId",
        "GitLab clientMutationId"
    ]

    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for user in placeholder_users:
                writer.writerow({
                    'Source host': user['sourceHostname'],
                    'Import type': user['importType'],
                    'Source user identifier': user['sourceUserIdentifier'],
                    'Source user name': user['sourceName'],    
                    'Source username': user['sourceUsername'],
                    'GitLab username': "",
                    'GitLab public email': "",
                    "GitLab importSourceUserId": user['id'],
                    "GitLab assigneeUserId": "",
                    "GitLab clientMutationId": ""
                })

        logger.info(f"Successfully wrote {len(placeholder_users)} records to {output_file}")
    except IOError as e:
        logger.error(f"Error writing to CSV file: {str(e)}")
        raise

# Example usage
if __name__ == "__main__":
    try:
        customer_name = "demo"
        group_full_path = "import-target"  # Replace with your group's full path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"{customer_name}_{group_full_path}_{timestamp}_placeholder_users.csv"  # Name of the output CSV file

        logger.info(f"Starting retrieval of placeholder users for group: {group_full_path}")
        
        placeholder_users = get_placeholder_users(group_full_path)
        
        logger.info(f"Writing placeholder users data to CSV: {output_file}")
        write_to_csv(placeholder_users, output_file)
        
        logger.info(f"Total placeholder users processed: {len(placeholder_users)}")
    
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")