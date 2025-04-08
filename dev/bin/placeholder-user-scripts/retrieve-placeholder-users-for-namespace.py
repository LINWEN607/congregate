"""
GitLab Placeholder Users Export Script

This script retrieves placeholder users from a GitLab group and exports them to a CSV file.
The exported CSV can be used as input for the user reassignment process during GitLab migrations.

Features:
- Retrieves all placeholder users from a specified GitLab group using REST API
- Exports user data to a CSV file in the required format for user reassignment
- Includes error handling and detailed logging

Prerequisites:
- Set DESTINATION_GITLAB_ROOT environment variable (e.g., "https://gitlab.example.com")
- Set DESTINATION_ADMIN_ACCESS_TOKEN environment variable with an admin access token
- Set DESTINATION_CUSTOMER_NAME environment variable with the customer name
- Set DESTINATION_TOP_LEVEL_GROUP environment variable with the target group path

Usage:
1. Set the required environment variables
2. Run the script to generate the CSV file

Example usage:
```
export DESTINATION_GITLAB_ROOT="https://gitlab.example.com"
export DESTINATION_ADMIN_ACCESS_TOKEN="glpat-xxxxxxxxxxxxxxxxxxxx"
export DESTINATION_CUSTOMER_NAME="demo"
export DESTINATION_TOP_LEVEL_GROUP="import-target"
python retrieve-placeholder-users-for-namespace.py
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
The data is written to a CSV named with the pattern:

output_file = f"{customer_name}_{group_full_path}_{timestamp}_placeholder_users.csv"  # Name of the output CSV file

"""

import requests
import os
import logging
import csv
import sys
from datetime import datetime
import io

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Check for required environment variables
DESTINATION_GITLAB_ROOT = os.environ.get("DESTINATION_GITLAB_ROOT")
DESTINATION_ADMIN_ACCESS_TOKEN = os.environ.get("DESTINATION_ADMIN_ACCESS_TOKEN")
DESTINATION_CUSTOMER_NAME = os.environ.get("DESTINATION_CUSTOMER_NAME")
DESTINATION_TOP_LEVEL_GROUP = os.environ.get("DESTINATION_TOP_LEVEL_GROUP")

# Validate required environment variables
if not DESTINATION_GITLAB_ROOT:
    logger.error("Required environment variable DESTINATION_GITLAB_ROOT is not set")
    sys.exit("ERROR: DESTINATION_GITLAB_ROOT environment variable must be set")

if not DESTINATION_ADMIN_ACCESS_TOKEN:
    logger.error("Required environment variable DESTINATION_ADMIN_ACCESS_TOKEN is not set")
    sys.exit("ERROR: DESTINATION_ADMIN_ACCESS_TOKEN environment variable must be set")

if not DESTINATION_CUSTOMER_NAME:
    logger.error("Required environment variable DESTINATION_CUSTOMER_NAME is not set")
    sys.exit("ERROR: DESTINATION_CUSTOMER_NAME environment variable must be set")

if not DESTINATION_TOP_LEVEL_GROUP:
    logger.error("Required environment variable DESTINATION_TOP_LEVEL_GROUP is not set")
    sys.exit("ERROR: DESTINATION_TOP_LEVEL_GROUP environment variable must be set")

# GitLab API configuration
DESTINATION_GITLAB_API_URL = f"{DESTINATION_GITLAB_ROOT}/api/v4"

def get_placeholder_users(group_full_path):
    """
    Retrieve placeholder users for a given GitLab group using the REST API.

    Args:
        group_full_path (str): The full path of the GitLab group.

    Returns:
        tuple: (csv_header, csv_data) where csv_header is the list of column names and
               csv_data is a list of data rows.

    Raises:
        requests.RequestException: If there's an error with the API request.
    """
    headers = {
        "Private-Token": DESTINATION_ADMIN_ACCESS_TOKEN
    }

    logger.info(f"Attempting to retrieve placeholder users for group: {group_full_path}")
    
    url = f"{DESTINATION_GITLAB_API_URL}/groups/{requests.utils.quote(group_full_path, safe='')}/placeholder_reassignments"
    logger.info(f"Calling API URL: {url}")
    
    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=30
        )
        response.raise_for_status()

        # The response is CSV data
        csv_data = response.text
        
        # Parse the CSV to count rows and get header
        csv_reader = csv.reader(io.StringIO(csv_data))
        csv_rows = list(csv_reader)
        
        if len(csv_rows) > 0:
            header = csv_rows[0]
            data_rows = csv_rows[1:]
            row_count = len(data_rows)
            
            logger.info(f"Successfully retrieved {row_count} placeholder users")
            return header, data_rows
        else:
            logger.info("No placeholder users found (empty CSV)")
            return [], []
            
    except requests.RequestException as e:
        logger.error(f"Error making request to GitLab API: {str(e)}")
        raise

def write_to_csv(csv_data, output_file):
    """
    Write CSV data to a file.

    Args:
        csv_data (tuple): A tuple containing (header, data_rows)
            where header is a list of column names and data_rows is a list of data rows.
        output_file (str): Name of the output CSV file.
    """
    header, data_rows = csv_data
    
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write the header
            writer.writerow(header)
            
            # Write all data rows
            writer.writerows(data_rows)

        logger.info(f"Successfully wrote {len(data_rows)} records to {output_file}")
    except IOError as e:
        logger.error(f"Error writing to CSV file: {str(e)}")
        raise

# Example usage
if __name__ == "__main__":
    try:
        customer_name = DESTINATION_CUSTOMER_NAME
        group_full_path = DESTINATION_TOP_LEVEL_GROUP
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"{customer_name}_{group_full_path}_{timestamp}_placeholder_users.csv"  # Name of the output CSV file

        logger.info(f"Starting retrieval of placeholder users for group: {group_full_path}")
        
        csv_data = get_placeholder_users(group_full_path)
        
        logger.info(f"Writing placeholder users data to CSV: {output_file}")
        write_to_csv(csv_data, output_file)
        
        logger.info(f"Total placeholder users processed: {len(csv_data[1])}")
    
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        sys.exit(f"ERROR: {str(e)}")