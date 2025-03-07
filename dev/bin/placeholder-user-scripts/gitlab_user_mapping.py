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
    python3 gitlab_user_mapping.py email_list.txt [OPTIONS]

Arguments:
    email_list.txt             Path to a file containing one email address per line

Options:
    --output FILE              Output CSV file path (default: gitlab_user_mapping_YYYYMMDD_HHMMSS.csv)
    --update-placeholders FILE Path to a placeholder users CSV file to update
    --validate-mappings        Validate mappings by cross-checking destination users
    --only-successful          Include only successfully mapped users in the output placeholder file
    --record-missing-emails    Record emails not found in GitLab instances to CSV files
    --log-level LEVEL          Set logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)
    --help                     Show this help message and exit

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
       
    3. (Optional) CSV files recording emails not found in source and destination GitLab instances.
    
    4. A log file with detailed information about the script's execution.

Features:
---------
    - Maps users between GitLab instances by email address
    - Updates placeholder user IDs for migration processes
    - Validates mappings by cross-checking emails and usernames
    - Filters output to include only successfully mapped users
    - Records emails not found in GitLab instances
    - Identifies mapping entries that can't be matched to placeholder users
    - Provides detailed logging and progress reporting

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
    - Validation results and inconsistencies

Notes:
------
    - The script uses GitLab's GraphQL API for efficient querying
    - It handles cases where users exist in only one of the GitLab instances
    - Matching is done by email address (case-insensitive)
    - The script requires admin-level API tokens to access user information
    - For placeholder updating, source_username is used as the matching key
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
    
    def __init__(self, gitlab_url: str, access_token: str, instance_name: str, missing_emails_file: str = None):
        self.gitlab_url = gitlab_url.rstrip('/')
        self.api_url = f"{self.gitlab_url}/api/graphql"
        self.access_token = access_token
        self.instance_name = instance_name
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        self.missing_emails_file = missing_emails_file
    
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
            
            # Record missing email to file if specified
            if self.missing_emails_file:
                with open(self.missing_emails_file, 'a') as f:
                    f.write(f"{self.instance_name},{email}\n")
            
            return None
                
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed for {self.instance_name} when querying email {email}: {str(e)}")
            return None

def validate_placeholder_mappings(placeholder_users: List[Dict], user_mapping: List[Dict], destination_client: GitLabGraphQLClient) -> None:
    """
    Validate the placeholder mappings by:
    1. Getting the destination user via the GitLab assigneeUserId
    2. Checking if any of their emails match the email in our source/destination mapping
    3. Using that email to find the source user
    4. Comparing the source username to the one in the placeholder CSV
    """
    logging.info("Starting validation of placeholder mappings...")
    
    # Create mapping lookups for validation
    dest_gid_to_mapping = {}
    for entry in user_mapping:
        if entry["destination_gid"]:
            dest_gid_to_mapping[entry["destination_gid"]] = entry
    
    # Create lookup of source emails to source usernames from our mapping
    source_email_to_username = {}
    for entry in user_mapping:
        if entry["source_email"] and entry["source_username"]:
            source_email_to_username[entry["source_email"]] = entry["source_username"]
    
    validation_count = 0
    mismatched_count = 0
    validation_errors = []
    
    # Process placeholder users with assigned destination IDs
    users_to_validate = [user for user in placeholder_users if user.get("GitLab assigneeUserId")]
    
    if not users_to_validate:
        logging.warning("No placeholder users with GitLab assigneeUserId found for validation")
        return
    
    logging.info(f"Validating {len(users_to_validate)} placeholder users with assigned destination IDs")
    
    for i, user in enumerate(users_to_validate, 1):
        # Log progress
        if i % 20 == 0 or i == 1 or i == len(users_to_validate):
            logging.info(f"Validating placeholder user {i}/{len(users_to_validate)}")
        
        source_username = user.get("Source username")
        dest_gid = user.get("GitLab assigneeUserId")
        
        if not source_username or not dest_gid:
            continue
        
        # Find the mapping entry for this destination ID
        mapping_entry = dest_gid_to_mapping.get(dest_gid)
        if not mapping_entry:
            logging.warning(f"Validation: No mapping entry found for destination ID {dest_gid}")
            continue
        
        # Get the user details from the destination GitLab
        try:
            # Query the destination user by ID to get their emails
            dest_user = query_gitlab_user_by_id(destination_client, dest_gid)
            
            if not dest_user:
                logging.warning(f"Validation: Could not find destination user with ID {dest_gid}")
                continue
            
            # Get the destination user's emails
            dest_emails = dest_user.get("emails", [])
            
            # Find a matching email in our source mapping
            matching_source_username = None
            matching_email = None
            
            for email in dest_emails:
                if email in source_email_to_username:
                    matching_source_username = source_email_to_username[email]
                    matching_email = email
                    break
            
            # Validate the username match
            if matching_source_username:
                validation_count += 1
                
                if matching_source_username != source_username:
                    mismatched_count += 1
                    error = {
                        "placeholder_username": source_username,
                        "derived_username": matching_source_username,
                        "destination_id": dest_gid,
                        "matching_email": matching_email
                    }
                    validation_errors.append(error)
                    logging.warning(f"Validation: Username mismatch for dest ID {dest_gid}! "
                                f"Placeholder: '{source_username}', Derived: '{matching_source_username}'")
            else:
                logging.debug(f"Validation: No matching source email found for destination user with ID {dest_gid}")
        
        except Exception as e:
            logging.error(f"Validation error for user {source_username} with dest ID {dest_gid}: {str(e)}")
    
    # Report validation summary
    logging.info(f"Validation summary:")
    logging.info(f"  - Validated {validation_count} mappings")
    
    if mismatched_count > 0:
        logging.warning(f"  - Found {mismatched_count} username mismatches!")
        logging.warning("  - Details of first 10 mismatches:")
        for i, error in enumerate(validation_errors[:10]):
            logging.warning(f"    {i+1}. Placeholder username: '{error['placeholder_username']}', "
                        f"Derived username: '{error['derived_username']}', "
                        f"Matching email: {error['matching_email']}")
    else:
        logging.info("  - All validated mappings are consistent!")

def query_gitlab_user_by_id(client: GitLabGraphQLClient, user_id: str) -> Optional[Dict]:
    """Query a GitLab user by ID and return their details including emails."""
    query = """
    query($id: UserID!) {
    user(id: $id) {
        username
        emails {
        nodes {
            email
        }
        }
    }
    }
    """
    
    variables = {"id": user_id}
    
    try:
        response = requests.post(
            client.api_url,
            headers=client.headers,
            json={"query": query, "variables": variables}
        )
        response.raise_for_status()
        
        data = response.json()
        
        if "errors" in data:
            logging.error(f"GraphQL error when querying user ID {user_id}: {data['errors']}")
            return None
        
        user_data = data.get("data", {}).get("user")
        if not user_data:
            logging.warning(f"No user found for ID: {user_id}")
            return None
        
        # Extract emails from nested structure
        email_nodes = user_data.get("emails", {}).get("nodes", [])
        emails = [node.get("email") for node in email_nodes if node.get("email")]
        
        return {
            "username": user_data.get("username"),
            "emails": emails
        }
            
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed when querying user ID {user_id}: {str(e)}")
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

def write_updated_placeholder_users(placeholder_users: List[Dict], output_file: str, only_successful: bool = False) -> None:
    """
    Write updated placeholder users to a CSV file.
    
    Args:
        placeholder_users: List of placeholder user dictionaries
        output_file: Path to the output CSV file
        only_successful: If True, only output users with a GitLab assigneeUserId
    """
    if not placeholder_users:
        logging.warning("No placeholder users to write")
        return
    
    # Filter users if only_successful is True
    if only_successful:
        successful_users = [user for user in placeholder_users if user.get("GitLab assigneeUserId")]
        if not successful_users:
            logging.warning("No successfully mapped placeholder users to write")
            return
        
        users_to_write = successful_users
        logging.info(f"Writing {len(successful_users)} successfully mapped users out of {len(placeholder_users)} total")
    else:
        users_to_write = placeholder_users
        logging.info(f"Writing all {len(placeholder_users)} placeholder users")
    
    try:
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=users_to_write[0].keys())
            writer.writeheader()
            writer.writerows(users_to_write)
        
        logging.info(f"Successfully wrote {len(users_to_write)} placeholder users to {output_file}")
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
    parser.add_argument("--validate-mappings", action="store_true", 
                       help="Validate the mappings by cross-checking destination users")
    parser.add_argument("--only-successful", action="store_true",
                       help="Include only successfully mapped users in the generated placeholder file")
    parser.add_argument("--record-missing-emails", action="store_true",
                       help="Record missing emails to files")
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

    # Initialize missing emails files
    source_missing_file = None
    dest_missing_file = None        

    if args.record_missing_emails:
        source_missing_file = f"missing_emails_source_{timestamp}.csv"
        dest_missing_file = f"missing_emails_destination_{timestamp}.csv"
        
        # Initialize the files with headers
        for file_path, instance in [(source_missing_file, "source"), (dest_missing_file, "destination")]:
            with open(file_path, 'w') as f:
                f.write("instance,email\n")
        
        logging.info(f"Recording missing emails to {source_missing_file} and {dest_missing_file}")

    # Initialize GraphQL clients
    source_client = GitLabGraphQLClient(source_url, source_token, "source", source_missing_file)
    destination_client = GitLabGraphQLClient(destination_url, destination_token, "destination", dest_missing_file)
    
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

       # Add validation step
        if args.validate_mappings:
            validate_placeholder_mappings(updated_placeholder_users, results, destination_client)

        output_placeholder_file = "placeholder_users-generated.csv"
        write_updated_placeholder_users(
            updated_placeholder_users, 
            output_placeholder_file, 
            only_successful=args.only_successful
        )
    
    logging.info("GitLab user mapping process completed successfully")

if __name__ == "__main__":
    main()