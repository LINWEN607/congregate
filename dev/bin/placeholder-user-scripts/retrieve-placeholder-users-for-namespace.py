# --------------------------------------------------------------------------------
# Example CSV file content:
# Source host,Import type,Source user identifier,Source user name,Source username,GitLab username,GitLab public email,GitLab importSourceUserId,GitLab assigneeUserId,GitLab clientMutationId
# gitlab.com,email,123456,John Doe,johndoe,johndoe,johndoe@example.com,gid://gitlab/ImportSourceUser/123456,123457,123456789
# ...
# Replace the placeholders in the MAIN function with your actual data.
#        group_full_path = "import-target"  # Replace with your group's full path
#        output_file = "placeholder_users.csv"  # Name of the output CSV file
# Note: The "GitLab username" and "GitLab public email" fields are not used in the script.
# The "GitLab importSourceUserId", "GitLab assigneeUserId", and "GitLab clientMutationId" fields are used for the reassign_placeholder_user function.

import requests
import os
import logging
import csv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# GitLab API configuration
DESTINATION_GITLAB_ROOT  = os.environ.get("DESTINATION_GITLAB_ROOT", "")
DESTINATION_GITLAB_GRAPHQL_URL = f"{DESTINATION_GITLAB_ROOT}/api/graphql"
DESTINATION_GITLAB_API_URL = f"{DESTINATION_GITLAB_ROOT}/api/v4"
DESTINATION_ADMIN_ACCESS_TOKEN = os.environ.get("DESTINATION_ADMIN_ACCESS_TOKEN", "")

FIND_PLACEHOLDERS_FOR_NAMESPACE_QUERY = """
query($fullPath: ID!){
  namespace(fullPath: $fullPath) {
    importSourceUsers {
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
    Retrieve placeholder users for a given GitLab group using GraphQL API.

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

    variables = {
        "fullPath": group_full_path
    }

    logger.info(f"Attempting to retrieve placeholder users for group: {group_full_path}")

    try:
        logger.debug("Sending GraphQL query to GitLab API")
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
        
        placeholder_users = data["data"]["namespace"]["importSourceUsers"]["nodes"]
        logger.info(f"Successfully retrieved {len(placeholder_users)} placeholder users")
        return placeholder_users

    except requests.RequestException as e:
        logger.error(f"Error making request to GitLab API: {str(e)}")
        raise
    except KeyError as e:
        logger.error(f"Unexpected response structure: {str(e)}")
        raise
    except ValueError as e:
        logger.error(str(e))
        raise

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
        group_full_path = "import-target"  # Replace with your group's full path
        output_file = "placeholder_users.csv"  # Name of the output CSV file

        logger.info(f"Starting retrieval of placeholder users for group: {group_full_path}")
        
        placeholder_users = get_placeholder_users(group_full_path)
        
        logger.info(f"Writing placeholder users data to CSV: {output_file}")
        write_to_csv(placeholder_users, output_file)
        
        logger.info(f"Total placeholder users processed: {len(placeholder_users)}")
    
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")