"""
GitLab User Mapping Script
==========================

This script maps users between two GitLab instances by matching their email addresses.
It takes a file containing email addresses, searches for users with these emails in both 
the source and destination GitLab instances, and outputs a CSV mapping showing details 
for each user across both systems.

The script can also update a placeholder users CSV file by replacing placeholder user IDs
with actual destination GitLab user IDs based on the mapping.

Usage:
------
    python3 gitlab_user_mapping.py email_list.txt [--output output_file.csv]
                                  [--update-placeholders placeholder_file.csv]
                                  [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]

Arguments:
    email_list.txt             Path to a file containing one email address per line
    --output                   Optional path for the output CSV file
                               Default: gitlab_user_mapping_YYYYMMDD_HHMMSS.csv
    --update-placeholders      Optional path to a placeholder users CSV file to update
    --log-level                Optional logging level (default: INFO)

Environment Variables (Required):
---------------------------------
    SOURCE_GITLAB_ROOT          Base URL for the source GitLab instance (e.g., https://gitlab.source.com)
    SOURCE_ADMIN_ACCESS_TOKEN   Admin access token for the source GitLab instance
    DESTINATION_GITLAB_ROOT     Base URL for the destination GitLab instance (e.g., https://gitlab.dest.com)
    DESTINATION_ADMIN_ACCESS_TOKEN  Admin access token for the destination GitLab instance

Input:
------
    1. A text file containing one email address per line. Example:
    
       user1@example.com
       user2@example.com
       user3@example.com
       
    2. (Optional) A placeholder users CSV file with the following fields:
       Source host,Import type,Source user identifier,Source user name,Source username,
       GitLab username,GitLab public email,GitLab importSourceUserId,GitLab assigneeUserId,
       GitLab clientMutationId

Output:
-------
    1. A CSV file with the following columns:
       - email: The original email address from the input file
       - source_username: Username in the source GitLab instance
       - source_email: Email in the source GitLab instance
       - source_gid: User ID in the source GitLab instance
       - destination_username: Username in the destination GitLab instance
       - destination_email: Email in the destination GitLab instance
       - destination_gid: User ID in the destination GitLab instance
       
    2. (Optional) An updated placeholder users CSV file (placeholder_users-generated.csv)
       with GitLab assigneeUserId updated to match destination_gid from the mapping.

Logging:
--------
    The script logs information, warnings, and errors to both:
    1. Console (stdout)
    2. A timestamped log file: gitlab_user_mapping_YYYYMMDD_HHMMSS.log
    
    Log entries include:
    - Starting and completion of the script
    - Email processing progress
    - User lookup successes and failures
    - API request errors
    - File I/O operations
    - Detailed information about placeholder user mapping

Notes:
------
    - The script uses GitLab's GraphQL API for efficient querying
    - It handles cases where users exist in only one of the GitLab instances
    - Matching is done by email address (case-insensitive)
    - The script requires admin-level API tokens to access user information
"""

import os
import sys
import csv
import logging
import requests
import argparse
from datetime import datetime
from typing import List, Dict, Optional, Tuple

# Configure logging - moved to main function to allow for command-line level selection

def setup_logging(level_name: str) -> None:
    """Set up logging with the specified level."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"gitlab_user_mapping_{timestamp}.log"
    
    # Convert string level to logging level
    numeric_level = getattr(logging, level_name.upper(), None)
    if not isinstance(numeric_level, int):
        print(f"Invalid log level: {level_name}, defaulting to INFO")
        numeric_level = logging.INFO
    
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized at level {level_name}")
    return logger

class GitLabGraphQLClient:
    """Client to interact with GitLab GraphQL API."""
    
    def __init__(self, gitlab_url: str, access_token: str, instance_name: str):
        self.gitlab_url = gitlab_url.rstrip('/')
        self.api_url = f"{self.gitlab_url}/api/graphql"
        self.access_token = access_token
        self.instance_name = instance_name
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    def query_user_by_email(self, email: str) -> Optional[Dict]:
        """Query a user by email using GraphQL."""
        query = """
        query($email: String!) {
          users(search: $email, first: 10) {
            nodes {
              id
              username
              emails {
                nodes {
                  email
                }
              }
            }
          }
        }
        """
        
        variables = {"email": email}
        
        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json={"query": query, "variables": variables}
            )
            response.raise_for_status()
            
            data = response.json()
            
            if "errors" in data:
                logging.error(f"GraphQL error for {self.instance_name} when querying email {email}: {data['errors']}")
                return None
            
            nodes = data.get("data", {}).get("users", {}).get("nodes", [])
            
            # Find the user with the matching email
            for user in nodes:
                email_nodes = user.get("emails", {}).get("nodes", [])
                user_emails = [node.get("email") for node in email_nodes if node.get("email")]
                
                if email.lower() in [e.lower() for e in user_emails]:
                    return {
                        "username": user.get("username"),
                        "email": email,  # Use the original email we searched for
                        "gid": user.get("id")  # Using the id field instead of gitlabUserid
                    }
            
            logging.warning(f"No user found in {self.instance_name} for email: {email}")
            return None
                
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed for {self.instance_name} when querying email {email}: {str(e)}")
            return None

def read_emails_from_file(file_path: str) -> List[str]:
    """Read a list of email addresses from a file."""
    try:
        with open(file_path, 'r') as f:
            # Strip whitespace and filter out empty lines
            emails = [line.strip() for line in f.readlines() if line.strip()]
        
        logging.info(f"Successfully read {len(emails)} emails from {file_path}")
        return emails
    except IOError as e:
        logging.error(f"Error reading email file {file_path}: {str(e)}")
        sys.exit(1)

def write_results_to_csv(results: List[Dict], output_file: str) -> None:
    """Write the mapping results to a CSV file."""
    fieldnames = [
        "email", 
        "source_username", "source_email", "source_gid",
        "destination_username", "destination_email", "destination_gid"
    ]
    
    try:
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        
        logging.info(f"Successfully wrote {len(results)} rows to {output_file}")
    except IOError as e:
        logging.error(f"Error writing to CSV file {output_file}: {str(e)}")
        sys.exit(1)

def read_placeholder_users(file_path: str) -> List[Dict]:
    """Read placeholder users from a CSV file."""
    try:
        placeholder_users = []
        with open(file_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                placeholder_users.append(row)
        
        logging.info(f"Successfully read {len(placeholder_users)} placeholder users from {file_path}")
        return placeholder_users
    except IOError as e:
        logging.error(f"Error reading placeholder users file {file_path}: {str(e)}")
        sys.exit(1)

def write_updated_placeholder_users(placeholder_users: List[Dict], output_file: str) -> None:
    """Write updated placeholder users to a CSV file."""
    if not placeholder_users:
        logging.warning("No placeholder users to write")
        return
    
    try:
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=placeholder_users[0].keys())
            writer.writeheader()
            writer.writerows(placeholder_users)
        
        logging.info(f"Successfully wrote {len(placeholder_users)} updated placeholder users to {output_file}")
    except IOError as e:
        logging.error(f"Error writing updated placeholder users to {output_file}: {str(e)}")
        sys.exit(1)

def update_placeholder_users(placeholder_users: List[Dict], user_mapping: List[Dict]) -> List[Dict]:
    """
    Update placeholder users with destination GitLab IDs from the user mapping.
    
    This function matches placeholder users by their 'Source username' field to the
    'source_username' field in the user mapping, and updates their 'GitLab assigneeUserId'
    with the corresponding 'destination_gid'.
    
    It also identifies mapping entries that cannot be matched to any placeholder user,
    which indicates missing data in the placeholder file.
    """
    # Create a lookup dictionary for faster matching of source usernames to destination GIDs
    mapping_by_source_username = {
        item["source_username"]: {
            "destination_gid": item["destination_gid"],
            "email": item["email"],
            "matched": False  # Track whether this mapping entry was used
        }
        for item in user_mapping 
        if item["source_username"] and item["destination_gid"]
    }
    
    # Set of all source usernames in the placeholder file
    placeholder_usernames = {
        user.get("Source username") 
        for user in placeholder_users 
        if user.get("Source username")
    }
    
    logging.info(f"Starting update of placeholder users - {len(placeholder_users)} to process")
    logging.info(f"Found {len(mapping_by_source_username)} source usernames with destination IDs in mapping")
    logging.info(f"Found {len(placeholder_usernames)} unique source usernames in placeholder file")
    
    updated_count = 0
    not_found_count = 0
    
    # Update placeholder users
    for i, user in enumerate(placeholder_users, 1):
        source_username = user.get("Source username")
        
        # Log progress every 100 users or at the beginning and end
        if i % 100 == 0 or i == 1 or i == len(placeholder_users):
            logging.info(f"Processing placeholder user {i}/{len(placeholder_users)}")
        
        if not source_username:
            logging.debug(f"Placeholder user at row {i} has no 'Source username'")
            continue
            
        if source_username in mapping_by_source_username:
            mapping_entry = mapping_by_source_username[source_username]
            old_id = user.get("GitLab assigneeUserId", "None")
            new_id = mapping_entry["destination_gid"]
            user["GitLab assigneeUserId"] = new_id
            updated_count += 1
            
            # Mark this mapping entry as matched
            mapping_entry["matched"] = True
            
            logging.debug(f"Updated user '{source_username}' (email: {mapping_entry['email']}) - ID changed from {old_id} to {new_id}")
        else:
            not_found_count += 1
            logging.debug(f"No mapping found for placeholder user '{source_username}'")
    
    # Check for mapping entries that weren't matched to any placeholder user
    unmatched_mappings = [
        {"username": username, "email": details["email"]}
        for username, details in mapping_by_source_username.items()
        if not details["matched"]
    ]
    
    if unmatched_mappings:
        logging.warning(f"{len(unmatched_mappings)} entries in mapping could not be matched to any placeholder user")
        for i, entry in enumerate(unmatched_mappings[:20]):  # Log first 20 for brevity
            logging.warning(f"  Unmatched mapping entry {i+1}: username={entry['username']}, email={entry['email']}")
        
        if len(unmatched_mappings) > 20:
            logging.warning(f"  ... and {len(unmatched_mappings) - 20} more unmatched entries")
    
    # Summary logging
    logging.info(f"User mapping summary:")
    logging.info(f"  - Updated {updated_count} placeholder users with destination GitLab IDs")
    logging.info(f"  - Could not find mappings for {not_found_count} placeholder users")
    
    # Coverage analysis for the mapping file
    if mapping_by_source_username:
        matched_count = sum(1 for details in mapping_by_source_username.values() if details["matched"])
        mapping_coverage_pct = (matched_count / len(mapping_by_source_username)) * 100
        logging.info(f"  - {matched_count} out of {len(mapping_by_source_username)} mapping entries were matched ({mapping_coverage_pct:.2f}%)")
        
        if matched_count < len(mapping_by_source_username):
            logging.warning(f"  - {len(mapping_by_source_username) - matched_count} mapping entries could not be matched to placeholder users")
    
    return placeholder_users

def get_environment_variable(var_name: str) -> str:
    """Get environment variable with error handling."""
    value = os.environ.get(var_name)
    if not value:
        logging.error(f"Required environment variable {var_name} is not set")
        sys.exit(1)
    return value

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Map GitLab users between instances by email.")
    parser.add_argument("email_file", help="File containing list of email addresses")
    parser.add_argument("--output", default=None, 
                       help="Output CSV file path (default: gitlab_user_mapping_<timestamp>.csv)")
    parser.add_argument("--update-placeholders", help="Path to placeholder users CSV file to update")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                       help="Set the logging level (default: INFO)")
    args = parser.parse_args()
    
    # Setup logging with the specified level
    global logger
    logger = setup_logging(args.log_level)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if args.output is None:
        args.output = f"gitlab_user_mapping_{timestamp}.csv"
    
    logging.info("Starting GitLab user mapping process")
    
    # Get environment variables
    try:
        source_url = get_environment_variable("SOURCE_GITLAB_ROOT")
        source_token = get_environment_variable("SOURCE_ADMIN_ACCESS_TOKEN")
        destination_url = get_environment_variable("DESTINATION_GITLAB_ROOT")
        destination_token = get_environment_variable("DESTINATION_ADMIN_ACCESS_TOKEN")
    except SystemExit:
        return
    
    # Initialize GraphQL clients
    source_client = GitLabGraphQLClient(source_url, source_token, "source")
    destination_client = GitLabGraphQLClient(destination_url, destination_token, "destination")
    
    # Read emails from file
    emails = read_emails_from_file(args.email_file)
    
    # Process each email
    results = []
    for i, email in enumerate(emails, 1):
        logging.info(f"Processing email {i}/{len(emails)}: {email}")
        
        source_data = source_client.query_user_by_email(email)
        destination_data = destination_client.query_user_by_email(email)
        
        # Create a row for the CSV, even if one side is missing
        row = {
            "email": email,
            "source_username": source_data.get("username") if source_data else None,
            "source_email": source_data.get("email") if source_data else None,
            "source_gid": source_data.get("gid") if source_data else None,
            "destination_username": destination_data.get("username") if destination_data else None,
            "destination_email": destination_data.get("email") if destination_data else None,
            "destination_gid": destination_data.get("gid") if destination_data else None
        }
        
        results.append(row)
    
    # Write results to CSV
    write_results_to_csv(results, args.output)
    
    # Process placeholder users if requested
    if args.update_placeholders:
        logging.info(f"Updating placeholder users from {args.update_placeholders}")
        placeholder_users = read_placeholder_users(args.update_placeholders)
        updated_placeholder_users = update_placeholder_users(placeholder_users, results)
        output_placeholder_file = "placeholder_users-generated.csv"
        write_updated_placeholder_users(updated_placeholder_users, output_placeholder_file)
    
    logging.info("GitLab user mapping process completed successfully")

if __name__ == "__main__":
    main()