# This script updates the public email of a GitLab user on a destination system based on their primary email from the source system
# This assumes you have an admin-level token for the destination system and that the source primary email is unique to each user
# To use this script, create a CSV file named "source-usernames-and-emails.csv" with the following columns: \
# Source user name,source_primary_email
# This code has a DRY_RUN flag. If true, the public email for the user will not be updated
# You can set the DRY_RUN flag as an environment variable (DRY_RUN=True or DRY_RUN=False)
# or hard code it into the script.  If you don't set the environment variable, the default value is True.

import csv
import requests
import json
import logging
import os
from requests.exceptions import RequestException

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set DRY_RUN flag based on environment variable, defaulting to True if not set
DRY_RUN = os.environ.get('DRY_RUN', 'True').lower() == 'true'

# GitLab API endpoint and personal access token
DESTINATION_GITLAB_ROOT = "https://gitlab.gmgldemo.net/api"
DESTINATION_GITLAB_GRAPHQL_URL = f"{DESTINATION_GITLAB_ROOT}/graphql"
DESTINATION_GITLAB_API_URL = f"{DESTINATION_GITLAB_ROOT}/v4"
DESTINATION_ADMIN_ACCESS_TOKEN = ""

# GraphQL query to find user by email
FIND_USER_QUERY = """
query($email: String!) {
    users(search: $email) {
        nodes {
                id
                username
                publicEmail
                emails {
                    nodes {
                            email
                    }
                }
        }
    }
}
"""

# GraphQL mutation to update user's public email
# Currently not used
UPDATE_PUBLIC_EMAIL_MUTATION = """
mutation($id: UserID!, $publicEmail: String!) {
  userUpdate(id: $id, publicEmail: $publicEmail) {
    user {
      id
      username
      publicEmail
    }
    errors
  }
}
"""

def run_graphql_query(query, variables):
    """
    Execute a GraphQL query against the GitLab API.

    Args:
        query (str): The GraphQL query string.
        variables (dict): Variables to be used in the query.

    Returns:
        dict: The JSON response from the API.

    Raises:
        RequestException: If the API request fails.
    """
    headers = {
        "Authorization": f"Bearer {DESTINATION_ADMIN_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    try:
        response = requests.post(
            DESTINATION_GITLAB_GRAPHQL_URL,
            headers=headers,
            json={"query": query, "variables": variables},
            timeout=30  # Add a timeout
        )
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()
    except RequestException as e:
        logger.error(f"API request failed: {str(e)}")
        raise

def find_user_by_email(email):
    """
    Find a user in GitLab by their email address.

    Args:
        email (str): The email address to search for.

    Returns:
        dict: User data if found, None otherwise.
    """
    variables = {"email": email}
    try:
        result = run_graphql_query(FIND_USER_QUERY, variables)
        users = result.get("data", {}).get("users", {}).get("nodes", [])
        if not users:
            logger.warning(f"No user found for email: {email}")
        elif len(users) > 1:
            logger.warning(f"Multiple users found for email: {email}")
        return users[0] if users else None
    except Exception as e:
        logger.error(f"Error finding user by email {email}: {str(e)}")
        return None

def update_public_email(user_id, public_email):
    """
    Update the public email address for a GitLab user using the GitLab Users API.

    Args:
        user_id (str): The ID of the user to update.
        public_email (str): The new public email address.

    Returns:
        dict: The result of the update operation.
    """
    user_id = user_id.split('/')[-1]
    api_url = f"{DESTINATION_GITLAB_API_URL}/users/{user_id}"
    headers = {
        "private-token": f"{DESTINATION_ADMIN_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    data = {"public_email": public_email}

    
    try:
        if DRY_RUN:
            logger.info(f"DRY RUN: Would update public email for user {user_id} to {public_email}")
            return {"dryRun": True}
        else:
            response = requests.put(api_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()  # Raise an exception for HTTP errors
            update_result = response.json()
            
            if response.status_code == 200:
                logger.info(f"Successfully updated public email for user {user_id}")
            else:
                logger.error(f"Failed to update public email for user {user_id}: {update_result}")
            
            return update_result
    except requests.RequestException as e:
        logger.error(f"API request failed for user {user_id}: {str(e)}")
        return {"errors": [str(e)]}
    except Exception as e:
        logger.error(f"Error updating public email for user {user_id}: {str(e)}")
        return {"errors": [str(e)]}

def process_csv_file(file_path):
    """
    Process a CSV file containing user email addresses and update their public email in GitLab.

    Args:
        file_path (str): The path to the CSV file.

    This function reads the CSV file, finds each user by their email,
    and updates their public email in GitLab.
    """
    try:
        with open(file_path, "r") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                email = row.get("source_primary_email")
                if not email:
                    logger.warning("Email not found in CSV row")
                    continue

                user = find_user_by_email(email)
                if user:
                    user_id = user["id"]
                    update_result = update_public_email(user_id, email)
                    if DRY_RUN:
                        logger.info(f"DRY RUN: Would have updated public email for {email}")
                    elif "errors" in update_result and update_result["errors"]:
                        logger.error(f"Failed to update public email for {email}: {update_result['errors']}")
                    else:
                        logger.info(f"Updated public email for {email}")
                else:
                    logger.warning(f"User not found for email: {email}")
    except FileNotFoundError:
        logger.error(f"CSV file not found: {file_path}")
    except csv.Error as e:
        logger.error(f"Error reading CSV file: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error processing CSV file: {str(e)}")

if __name__ == "__main__":
    csv_file_path = "source-usernames-and-emails.csv"
    try:
        logger.info(f"Starting script execution. DRY_RUN mode: {DRY_RUN}")
        process_csv_file(csv_file_path)
    except Exception as e:
        logger.critical(f"Script execution failed: {str(e)}")