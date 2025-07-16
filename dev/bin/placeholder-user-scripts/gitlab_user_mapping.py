"""
GitLab User Mapping Script
==========================

This script maps users between two GitLab instances by matching their email addresses.
It takes two inputs:
1. A file containing email addresses (one per line)
2. A CSV file placeholder_users downloaded from the destination toplevel group

The script outputs an updated CSV mapping file containing the following fields:
- Source host
- Import type
- Source user identifier
- Source user name
- Source username
- GitLab username
- GitLab public email

The script always validates mappings, records missing emails, and includes all users in the output.

Usage:
------
    python3 gitlab_user_mapping.py email_list.txt placeholder_users.csv [OPTIONS]

Arguments:
    email_list.txt          Path to a file containing one email address per line
    placeholder_users.csv   Path to a CSV file containing placeholder mappings

Options:
    --log-level LEVEL       Set logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)
    --help                  Show this help message and exit

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

    2. A placeholder users CSV file with the following fields:
       Source host, Import type, Source user identifier, Source user name, Source username,
       GitLab username, GitLab public email

Output:
-------
    1. A CSV file (updated_map_YYYYMMDD_HHMMSS.csv) with the following fields:
       - Source host
       - Import type
       - Source user identifier
       - Source user name
       - Source username
       - GitLab username
       - GitLab public email

    2. CSV files recording emails not found in source and destination GitLab instances.

    3. A log file with detailed information about the script's execution.

Features:
---------
    - Maps users between GitLab instances by email address
    - Updates placeholder user IDs for migration processes
    - Validates mappings by cross-checking emails and usernames
    - Records emails not found in GitLab instances
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
import time
import random
import argparse
from datetime import datetime
from typing import List, Dict, Optional

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
        """Query a user by email using GraphQL with retry logic for 503 errors."""
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

        # Retry configuration
        max_retries = 5
        initial_wait = 1  # seconds
        max_wait = 60  # seconds
        backoff_factor = 2

        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    json={"query": query, "variables": variables},
                    timeout=30  # Add timeout to prevent hanging
                )

                # Handle 503 Service Unavailable with retry
                if response.status_code == 503:
                    if attempt < max_retries - 1:
                        wait_time = min(initial_wait * (backoff_factor ** attempt), max_wait)
                        # Add jitter to prevent thundering herd
                        jitter = wait_time * 0.1 * (0.5 - random.random())
                        actual_wait = wait_time + jitter

                        logging.warning(
                            f"Received 503 from {self.instance_name} for email {email}. "
                            f"Attempt {attempt + 1}/{max_retries}. Waiting {actual_wait:.2f}s before retry."
                        )
                        time.sleep(actual_wait)
                        continue
                    logging.error(
                        f"Max retries ({max_retries}) exceeded for {self.instance_name} "
                        f"when querying email {email}. Server returned 503."
                    )
                    return None

                # Handle rate limiting (429)
                if response.status_code == 429:
                    retry_after = response.headers.get('Retry-After', '60')
                    wait_time = int(retry_after) if retry_after.isdigit() else 60

                    if attempt < max_retries - 1:
                        logging.warning(
                            f"Rate limited by {self.instance_name}. Waiting {wait_time}s before retry."
                        )
                        time.sleep(wait_time)
                        continue
                    logging.error(f"Rate limit exceeded for {self.instance_name} after {max_retries} attempts.")
                    return None

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
                    try:
                        with open(self.missing_emails_file, 'a') as f:
                            f.write(f"{self.instance_name},{email}\n")
                    except IOError as e:
                        logging.error(f"Failed to write to missing emails file: {e}")

                return None

            except requests.exceptions.Timeout:
                logging.error(
                    f"Request timeout for {self.instance_name} when querying email {email} "
                    f"(attempt {attempt + 1}/{max_retries})"
                )
                if attempt < max_retries - 1:
                    time.sleep(initial_wait * (backoff_factor ** attempt))
                    continue
                return None

            except requests.exceptions.ConnectionError as e:
                logging.error(
                    f"Connection error for {self.instance_name} when querying email {email} "
                    f"(attempt {attempt + 1}/{max_retries}): {str(e)}"
                )
                if attempt < max_retries - 1:
                    time.sleep(initial_wait * (backoff_factor ** attempt))
                    continue
                return None

            except requests.exceptions.RequestException as e:
                logging.error(f"Request failed for {self.instance_name} when querying email {email}: {str(e)}")
                return None

            except ValueError as e:
                logging.error(f"Failed to parse JSON response from {self.instance_name}: {str(e)}")
                return None

def check_for_duplicate_emails(emails:List[str]) -> List[str]:
    """
    Check for duplicate emails in the input list and remove them.
    """
    lowered = [email.lower() for email in emails]
    email_set = set(lowered)
    duplicate_emails = [email for email in email_set if lowered.count(email) > 1]
    logging.info(f"Duplicate emails found in input\n: {duplicate_emails}")
    logging.info(f"Correcting emails")
    return list(email_set)

def validate_emails_used(emails: List[str], placeholder_users: List[Dict]) -> None:
    """
    Validate that all emails from the input list have a corresponding placeholder user.
    """
    email_set = set(emails)
    placeholder_email_set = set(user.get("GitLab public email") for user in placeholder_users if user.get("GitLab public email"))
    missing_emails = email_set - placeholder_email_set
    logging.info(f"Validating emails against placeholder users.")
    logging.warning(f"Unmatched emails: {missing_emails}")

def validate_placeholder_mappings(placeholder_users: List[Dict], user_mapping: List[Dict]) -> None:
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
    users_to_validate = [user for user in placeholder_users if user.get("GitLab username") or user.get("GitLab public email")]
    users_not_to_validate = [user for user in placeholder_users if not (user.get("GitLab username") or user.get("GitLab public email"))]

    if not users_to_validate:
        logging.warning("No placeholder users with GitLab username ir GitLab public email found for validation")
        return

    logging.info(f"Validating {len(users_to_validate)} placeholder users with GitLab username or GitLab public email")
    logging.info(f"Not validating {len(users_not_to_validate)} placeholder users without GitLab username and GitLab public email. Run in DEBUG logging to see the list.")
    logging.debug(f"Placeholder users not to validate are {users_not_to_validate}")

    for i, user in enumerate(users_to_validate, 1):
        # Log progress
        if i % 20 == 0 or i == 1 or i == len(users_to_validate):
            logging.info(f"Validating placeholder source user {user.get('Source username')} : {i}/{len(users_to_validate)}")

        source_username = user.get("Source username")
        gitlab_username = user.get("GitLab username")
        gitlab_public_email = user.get("GitLab public email")

        if not source_username or not (gitlab_username or gitlab_public_email):
            continue

        # Find the mapping entry for this destination username
        matching_entry = None
        for entry in user_mapping:
            if entry["destination_username"] == gitlab_username:
                matching_entry = entry
                break
            if entry["destination_email"] == gitlab_public_email:
                matching_entry = entry
                break

        if not matching_entry:
            logging.warning(f"Validation: No mapping entry found for GitLab username {gitlab_username}")
            continue

        # Validate the username match
        validation_count += 1

        if matching_entry["source_username"] != source_username:
            mismatched_count += 1
            error = {
                "placeholder_username": source_username,
                "derived_username": matching_entry["source_username"],
                "gitlab_username": gitlab_username,
                "matching_email": matching_entry["email"]
            }
            validation_errors.append(error)
            logging.warning(f"Validation: Username mismatch for GitLab username {gitlab_username}! "
                        f"Placeholder: '{source_username}', Derived: '{matching_entry['source_username']}'")

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

def log_mapping_results(results: List[Dict]) -> None:
    """Log summary of the mapping results."""
    total_emails = len(results)
    source_matches = sum(1 for r in results if r["source_username"])
    dest_matches = sum(1 for r in results if r["destination_username"])
    complete_matches = sum(1 for r in results if r["source_username"] and r["destination_username"])

    logging.info(f"Mapping results summary:")
    logging.info(f"  - Total emails processed: {total_emails}")
    logging.info(f"  - Emails matched in source GitLab: {source_matches} ({source_matches/total_emails*100:.1f}%)")
    logging.info(f"  - Emails matched in destination GitLab: {dest_matches} ({dest_matches/total_emails*100:.1f}%)")
    logging.info(f"  - Complete matches (both sides): {complete_matches} ({complete_matches/total_emails*100:.1f}%)")

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

def write_updated_map_file(placeholder_users: List[Dict], user_mapping: List[Dict], output_file: str) -> List[Dict]:
    """
    Write updated mapping to a CSV file with the required fields.

    Fields included:
    - Source host
    - Import type
    - Source user identifier
    - Source user name
    - Source username
    - GitLab username
    - GitLab public email
    """
    fieldnames = [
        "Source host",
        "Import type",
        "Source user identifier",
        "Source user name",
        "Source username",
        "GitLab username",
        "GitLab public email"
    ]

    # Create a lookup dictionary for faster matching
    mapping_by_source_username = {
        item["source_username"]: {
            "source_username": item["source_username"],
            "destination_username": item["destination_username"],
            "destination_email": item["destination_email"]
        }
        for item in user_mapping
        if item["source_username"]
    }

    # Update placeholder users with GitLab information
    updated_users = []
    for user in placeholder_users:
        source_username = user.get("Source username")
        destination_username = mapping_by_source_username.get(source_username, {}).get("destination_username")
        destination_email = mapping_by_source_username.get(source_username, {}).get("destination_email")

        logging.debug(f"Found user in placeholder source : {source_username} : destination : {destination_username} : {destination_email}")

        if source_username and source_username in mapping_by_source_username:
            mapping_data = mapping_by_source_username[source_username]

            # Update GitLab email if there's a destination match
            if mapping_data.get("destination_email"):
                user["GitLab public email"] = mapping_data.get("destination_email") # This assumes you are admin to make this work so you can match on any confirmed
            else:
                logging.warning(f"No destination email found for placeholder user {source_username}")
        else:
            logging.warning(f"Skipping placeholder user {source_username} : {destination_email} no matching source user in mapping results")

        # Keep only the required fields
        updated_user = {field: user.get(field, "") for field in fieldnames}
        updated_users.append(updated_user)

    try:
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(updated_users)

        logging.info(f"Successfully wrote {len(updated_users)} rows to {output_file}")
        return updated_users
    except IOError as e:
        logging.error(f"Error writing to CSV file {output_file}: {str(e)}")
        sys.exit(1)

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
    parser.add_argument("placeholder_file", help="Path to placeholder mappings CSV file")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                       help="Set the logging level (default: INFO)")
    args = parser.parse_args()

    # Setup logging with the specified level
    global logger
    logger = setup_logging(args.log_level)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Define the output updated map file
    updated_map_file = f"updated_map_{timestamp}.csv"

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

    verified_and_lowered_emails = check_for_duplicate_emails(emails)

    # Read placeholder users
    placeholder_users = read_placeholder_users(args.placeholder_file)

    # Process each email
    results = []
    for i, email in enumerate(verified_and_lowered_emails, 1):
        logging.info(f"Processing email {i}/{len(verified_and_lowered_emails)}: {email}")

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

        logging.debug(f"Processed email {i}/{len(verified_and_lowered_emails)}: {email} -> {row}")

    # Log summary of mapping results
    log_mapping_results(results)

    # Update the placeholder mappings and write to the output file
    updated_users = write_updated_map_file(placeholder_users, results, updated_map_file)

    # Validate mappings
    validate_placeholder_mappings(updated_users, results)

    # Validate used emails
    validate_emails_used(verified_and_lowered_emails, updated_users)

    logging.info("GitLab user mapping process completed successfully")

if __name__ == "__main__":
    main()