"""
GitLab Group Members Export Script

This script fetches all members of a specified GitLab group and exports their usernames and email addresses to a CSV file.

Usage:
1. Set the GITLAB_URL, GITLAB_TOKEN, and GROUP_ID variables.
2. Run the script to generate a CSV file named 'gitlab_group_members.csv'.

Requirements:
- requests library
- csv module
- GitLab API access token with appropriate permissions

Note: This script uses pagination to fetch all members, even for large groups.
Note: If the namespace consists of [Enterprise Users](https://docs.gitlab.com/ee/user/enterprise_user/), then an Owner token in the namespace is sufficient
"""

import requests
import csv
import os
import logging
from requests.exceptions import RequestException

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# GitLab API configuration
DESTINATION_GITLAB_ROOT= os.environ.get("DESTINATION_GITLAB_ROOT", "https://gitlab.com")
DESTINATION_GITLAB_API_URL = f"{DESTINATION_GITLAB_ROOT}/api/v4"
# As noted above, for Enterprise Users, an Owner token is sufficient
DESTINATION_ADMIN_ACCESS_TOKEN = os.environ.get("DESTINATION_ADMIN_ACCESS_TOKEN", "")
GROUP_ID = os.environ.get("GROUP_ID", None) 

# API endpoint
api_url = f"{DESTINATION_GITLAB_API_URL}/groups/{GROUP_ID}/members/all"

# Headers for authentication
headers = {
    "PRIVATE-TOKEN": DESTINATION_ADMIN_ACCESS_TOKEN
}

def fetch_all_members():
    """
    Fetch all members of the specified GitLab group using pagination.
    
    Returns:
        list: A list of dictionaries containing member information.
    
    Raises:
        RequestException: If there's an error fetching members from the API.
    """
    members = []
    page = 1
    per_page = 100

    while True:
        try:
            response = requests.get(
                api_url,
                headers=headers,
                params={"page": page, "per_page": per_page},
                timeout=30
            )
            response.raise_for_status()
            
            page_members = response.json()
            if not page_members:
                break
            
            members.extend(page_members)
            page += 1
            logger.info(f"Fetched page {page-1} of members")
        except RequestException as e:
            logger.error(f"Error fetching page {page} of members: {str(e)}")
            raise

    return members

def write_to_csv(csv_data, csv_filename):
    """
    Write member data to a CSV file.
    
    Args:
        csv_data (list): List of dictionaries containing member data.
        csv_filename (str): Name of the CSV file to write.
    
    Raises:
        IOError: If there's an error writing to the CSV file.
    """
    csv_headers = ["destination_username", "destination_primary_email"]
    try:
        with open(csv_filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_headers)
            writer.writeheader()
            writer.writerows(csv_data)
        logger.info(f"CSV file '{csv_filename}' has been created successfully.")
        logger.info(f"Total members exported: {len(csv_data)}")
    except IOError as e:
        logger.error(f"Error writing to CSV file: {str(e)}")
        raise

def main():
    """
    Main function to orchestrate the fetching of group members and writing to CSV.
    """
    try:
        # Fetch all group members
        logger.info("Starting to fetch group members")
        group_members = fetch_all_members()
        logger.info(f"Successfully fetched {len(group_members)} group members")

        # Prepare data for CSV
        csv_data = []
        for member in group_members:
            csv_data.append({
                "destination_username": member.get("username"),
                "destination_primary_email": member.get("email")
            })

        # Write data to CSV file
        csv_filename = "gitlab_group_members.csv"
        write_to_csv(csv_data, csv_filename)

    except RequestException as e:
        logger.error(f"Error fetching group members: {str(e)}")
        exit(1)
    except IOError as e:
        logger.error(f"Error writing to CSV file: {str(e)}")
        exit(1)
    except Exception as e:
        logger.error(f"Unexpected error occurred: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()