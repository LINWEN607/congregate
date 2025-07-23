"""
GitLab User Mapping Script - Username-based Email Search Version
================================================================

This script maps users between two GitLab instances by searching for email addresses
associated with usernames in the source GitLab instance and then mapping to destination
users.

It takes a CSV file of downloaded placeholder mappings and:
1. Queries the source GitLab instance for each username to get all associated emails
2. Searches for matching users in the destination GitLab instance by email
3. Updates the placeholder mappings with the found destination usernames and emails

The script outputs an updated CSV mapping file containing the following fields:
- Source host
- Import type
- Source user identifier
- Source user name
- Source username
- GitLab username
- GitLab public email

The script also outputs additional CSV files:
- Source usernames with emails (including public/primary status)
- Error files for usernames not found in source and destination

Usage:
------
    python3 gitlab_user_mapping_by_username.py placeholder_mappings.csv [OPTIONS]

Arguments:
    placeholder_mappings.csv   Path to a CSV file containing placeholder mappings

Options:
    --enterprise-users         Use the group enterprise users API for destination search
    --log-level LEVEL          Set logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)
    --help                     Show this help message and exit

Environment Variables (Required):
---------------------------------
    SOURCE_GITLAB_ROOT          Base URL for the source GitLab instance (e.g., https://gitlab.source.com)
    SOURCE_ADMIN_ACCESS_TOKEN   Admin access token for the source GitLab instance
    DESTINATION_GITLAB_ROOT     Base URL for the destination GitLab instance (e.g., https://gitlab.dest.com)
    DESTINATION_ADMIN_ACCESS_TOKEN  Admin access token for the destination GitLab instance
    DESTINATION_GROUP_ID        When using --enterprise-users, the group ID to search in (required for enterprise users API)

Input:
------
    A placeholder mappings CSV file with the following fields:
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

    2. A CSV file (source_username_emails_YYYYMMDD_HHMMSS.csv) with the following fields:
       - source_username
       - source_email
       - is_public
       - is_primary

    3. Error CSV files:
       - source_username_not_found_YYYYMMDD_HHMMSS.csv with source_username column
       - destination_email_not_found_YYYYMMDD_HHMMSS.csv with source_username column

    4. A log file with detailed information about the script's execution.

Features:
---------
    - Maps users between GitLab instances by looking up emails for source usernames
    - Updates placeholder user IDs for migration processes
    - Records emails not found in destination GitLab instance
    - Provides detailed logging and progress reporting
    - Option to use enterprise users API for destination user search

Logging:
--------
    The script logs information, warnings, and errors to both:
    1. Console (stdout)
    2. A timestamped log file: gitlab_user_mapping_YYYYMMDD_HHMMSS.log

    Log entries include:
    - Starting and completion of the script
    - Username processing progress
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
    - For placeholder updating, source_username is used as the matching key
"""

import os
import sys
import csv
import logging
import requests
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

    def __init__(self, gitlab_url: str, access_token: str, instance_name: str, group_id: Optional[str] = None):
        self.gitlab_url = gitlab_url.rstrip('/')
        self.api_url = f"{self.gitlab_url}/api/graphql"
        self.rest_api_url = f"{self.gitlab_url}/api/v4"
        self.access_token = access_token
        self.instance_name = instance_name
        self.group_id = group_id
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

    def query_user_by_username(self, username: str) -> Optional[Dict]:
        """Query a user by username using GraphQL and return their details including all emails."""
        query = """
        query($username: String!) {
          users(username: $username, first: 1) {
            nodes {
              id
              username
              publicEmail
              emails {
                nodes {
                  email
                  confirmed
                  primary
                }
              }
            }
          }
        }
        """

        variables = {"username": username}

        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json={"query": query, "variables": variables}
            )
            response.raise_for_status()

            data = response.json()

            if "errors" in data:
                logging.error(f"GraphQL error for {self.instance_name} when querying username {username}: {data['errors']}")
                return None

            nodes = data.get("data", {}).get("users", {}).get("nodes", [])

            if not nodes:
                logging.warning(f"No user found in {self.instance_name} for username: {username}")
                return None

            user = nodes[0]
            email_nodes = user.get("emails", {}).get("nodes", [])
            public_email = user.get("publicEmail")

            # Collect all emails with their properties
            emails = []
            primary_email = None

            for node in email_nodes:
                email = node.get("email")
                if not email:
                    continue

                is_primary = node.get("primary", False)
                is_public = (email == public_email)

                email_info = {
                    "email": email,
                    "is_primary": is_primary,
                    "is_public": is_public
                }

                emails.append(email_info)

                if is_primary:
                    primary_email = email

            return {
                "username": user.get("username"),
                "emails": emails,
                "public_email": public_email,
                "primary_email": primary_email,
                "gid": user.get("id")
            }

        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed for {self.instance_name} when querying username {username}: {str(e)}")
            return None

    def query_user_by_email(self, email: str, use_enterprise_api: bool = False) -> Optional[Dict]:
        """
        Query a user by email using GraphQL or REST API depending on the use_enterprise_api flag.
        Returns the user details if found.
        """
        if use_enterprise_api:
            if not self.group_id:
                logging.error("DESTINATION_GROUP_ID environment variable is required when using enterprise users API")
                sys.exit(1)
            return self._query_user_by_email_enterprise(email)
        else:
            return self._query_user_by_email_standard(email)

    def _query_user_by_email_standard(self, email: str) -> Optional[Dict]:
        """Query a user by email using standard GraphQL API."""
        query = """
        query($email: String!) {
          users(search: $email, first: 10) {
            nodes {
              id
              username
              publicEmail
              emails {
                nodes {
                  email
                  confirmed
                  primary
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
                public_email = user.get("publicEmail")

                if email.lower() in [e.lower() for e in user_emails]:
                    # Find primary email
                    primary_email = None
                    for node in email_nodes:
                        if node.get("primary", False):
                            primary_email = node.get("email")
                            break

                    return {
                        "username": user.get("username"),
                        "email": email,  # The email we searched for
                        "public_email": public_email,
                        "primary_email": primary_email,
                        "gid": user.get("id")
                    }

            logging.warning(f"No user found in {self.instance_name} for email: {email}")
            return None

        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed for {self.instance_name} when querying email {email}: {str(e)}")
            return None

    def _query_user_by_email_enterprise(self, email: str) -> Optional[Dict]:
        """Query a user by email using the group enterprise users API."""
        try:
            # Search enterprise users by email using REST API
            endpoint = f"{self.rest_api_url}/groups/{self.group_id}/enterprise_users"
            params = {"search": email}

            response = requests.get(
                endpoint,
                headers=self.headers,
                params=params
            )
            response.raise_for_status()

            users = response.json()

            # Find a user with matching email
            for user in users:
                user_emails = [e.get("email") for e in user.get("emails", [])]
                if email.lower() in [e.lower() for e in user_emails]:
                    # Determine public and primary emails
                    public_email = user.get("public_email")
                    primary_email = None
                    for e in user.get("emails", []):
                        if e.get("primary", False):
                            primary_email = e.get("email")
                            break

                    return {
                        "username": user.get("username"),
                        "email": email,  # The email we searched for
                        "public_email": public_email,
                        "primary_email": primary_email,
                        "gid": user.get("id")
                    }

            logging.warning(f"No enterprise user found in {self.instance_name} for email: {email}")
            return None

        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed for {self.instance_name} when querying enterprise users for email {email}: {str(e)}")
            return None

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

def write_updated_map_file(placeholder_users: List[Dict], user_mapping: Dict, output_file: str) -> None:
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

    # Update placeholder users with GitLab information
    updated_users = []
    for user in placeholder_users:
        source_username = user.get("Source username")

        if source_username and source_username in user_mapping:
            mapping_data = user_mapping[source_username]

            # Update GitLab username if there's a destination match
            if mapping_data.get("destination_username"):
                user["GitLab username"] = mapping_data["destination_username"]
                user["GitLab public email"] = mapping_data.get("destination_email", "")

        # Keep only the required fields
        updated_user = {field: user.get(field, "") for field in fieldnames}
        updated_users.append(updated_user)

    try:
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(updated_users)

        logging.info(f"Successfully wrote {len(updated_users)} rows to {output_file}")
    except IOError as e:
        logging.error(f"Error writing to CSV file {output_file}: {str(e)}")
        sys.exit(1)

def write_source_username_emails(source_emails: List[Dict], output_file: str) -> None:
    """
    Write source username and email information to a CSV file.

    Fields:
    - source_username
    - source_email
    - is_public
    - is_primary
    """
    fieldnames = ["source_username", "source_email", "is_public", "is_primary"]

    try:
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(source_emails)

        logging.info(f"Successfully wrote {len(source_emails)} rows to {output_file}")
    except IOError as e:
        logging.error(f"Error writing to CSV file {output_file}: {str(e)}")
        sys.exit(1)

def write_error_file(error_entries: List[Dict], fieldnames: List[str], output_file: str) -> None:
    """Write error entries to a CSV file."""
    try:
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(error_entries)

        logging.info(f"Successfully wrote {len(error_entries)} error entries to {output_file}")
    except IOError as e:
        logging.error(f"Error writing to error file {output_file}: {str(e)}")
        sys.exit(1)

def get_environment_variable(var_name: str, required: bool = True) -> Optional[str]:
    """Get environment variable with error handling."""
    value = os.environ.get(var_name)
    if required and not value:
        logging.error(f"Required environment variable {var_name} is not set")
        sys.exit(1)
    return value

def find_destination_user_by_emails(destination_client: GitLabGraphQLClient, emails: List[Dict],
                                    use_enterprise_api: bool) -> Optional[Dict]:
    """
    Search for a destination user by trying emails in order of preference:
    1. Public email
    2. Primary email
    3. Other emails in the order they are listed
    """
    # First, get public emails
    public_emails = [e["email"] for e in emails if e["is_public"]]

    # Then, get primary emails
    primary_emails = [e["email"] for e in emails if e["is_primary"]]

    # Then, get other emails
    other_emails = [e["email"] for e in emails if not e["is_public"] and not e["is_primary"]]

    # Combine in order of preference, skipping duplicates
    preferred_order = []
    seen_emails = set()

    for email in public_emails + primary_emails + other_emails:
        if email not in seen_emails:
            preferred_order.append(email)
            seen_emails.add(email)

    # Try each email until we find a match
    for email in preferred_order:
        destination_user = destination_client.query_user_by_email(email, use_enterprise_api)
        if destination_user:
            # Return the matching email along with the user data
            destination_user["matched_email"] = email
            return destination_user

    return None

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Map GitLab users between instances by username and email.")
    parser.add_argument("placeholder_file", help="Path to placeholder mappings CSV file")
    parser.add_argument("--enterprise-users", action="store_true",
                        help="Use the group enterprise users API for destination search")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                       help="Set the logging level (default: INFO)")
    args = parser.parse_args()

    # Setup logging with the specified level
    global logger
    logger = setup_logging(args.log_level)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Define output files
    updated_map_file = f"updated_map_{timestamp}.csv"
    source_username_emails_file = f"source_username_emails_{timestamp}.csv"
    source_username_not_found_file = f"source_username_not_found_{timestamp}.csv"
    destination_email_not_found_file = f"destination_email_not_found_{timestamp}.csv"

    logging.info("Starting GitLab user mapping process (username-based version)")

    # Get environment variables
    try:
        source_url = get_environment_variable("SOURCE_GITLAB_ROOT")
        source_token = get_environment_variable("SOURCE_ADMIN_ACCESS_TOKEN")
        destination_url = get_environment_variable("DESTINATION_GITLAB_ROOT")
        destination_token = get_environment_variable("DESTINATION_ADMIN_ACCESS_TOKEN")
        # Only needed if enterprise_users flag is set
        destination_group_id = get_environment_variable("DESTINATION_GROUP_ID", required=args.enterprise_users)
    except SystemExit:
        return

    # Initialize GraphQL clients
    source_client = GitLabGraphQLClient(source_url, source_token, "source")
    destination_client = GitLabGraphQLClient(destination_url, destination_token, "destination", destination_group_id)

    if args.enterprise_users:
        logging.info(f"Using enterprise users API with destination group ID: {destination_group_id}")

    # Read placeholder users
    placeholder_users = read_placeholder_users(args.placeholder_file)

    # Extract source usernames from placeholder users
    source_usernames = [user.get("Source username") for user in placeholder_users if user.get("Source username")]
    unique_source_usernames = list(set(source_usernames))

    logging.info(f"Processing {len(unique_source_usernames)} unique source usernames")

    # Process each source username
    source_username_emails = []  # For the source_username_emails.csv output
    username_errors = []  # For tracking usernames not found in source
    email_errors = []  # For tracking emails not found in destination
    user_mapping = {}  # For mapping source_username to destination information

    for i, username in enumerate(unique_source_usernames, 1):
        # Log progress
        if i % 10 == 0 or i == 1 or i == len(unique_source_usernames):
            logging.info(f"Processing username {i}/{len(unique_source_usernames)}: {username}")

        # Query source GitLab for the username
        source_user = source_client.query_user_by_username(username)

        if not source_user:
            # Record username not found
            username_errors.append({"source_username": username})
            continue

        # Extract emails from source user
        source_emails = source_user.get("emails", [])

        # Create entries for the source_username_emails.csv output
        for email_info in source_emails:
            source_username_emails.append({
                "source_username": username,
                "source_email": email_info["email"],
                "is_public": str(email_info["is_public"]).lower(),
                "is_primary": str(email_info["is_primary"]).lower()
            })

        # Use these emails to search for the destination user
        destination_user = find_destination_user_by_emails(
            destination_client,
            source_emails,
            args.enterprise_users
        )

        if destination_user:
            # Record the mapping
            user_mapping[username] = {
                "destination_username": destination_user["username"],
                "destination_email": destination_user.get("public_email") or destination_user.get("matched_email", ""),
                "matched_email": destination_user.get("matched_email")
            }
        else:
            # Record all emails not found in destination
            for email_info in source_emails:
                email_errors.append({
                    "source_username": username
                })

    # Write output files

    # Write source username emails file
    write_source_username_emails(source_username_emails, source_username_emails_file)

    # Write error files
    write_error_file(username_errors, ["source_username"], source_username_not_found_file)
    write_error_file(email_errors, ["source_username"], destination_email_not_found_file)

    # Update the placeholder mappings and write to the output file
    write_updated_map_file(placeholder_users, user_mapping, updated_map_file)

    # Log summary
    logging.info("GitLab user mapping process completed")
    logging.info(f"Total unique source usernames processed: {len(unique_source_usernames)}")
    logging.info(f"Source usernames with valid user data: {len(user_mapping)}")
    logging.info(f"Source usernames not found: {len(username_errors)}")
    logging.info(f"Source emails not found in destination: {len(email_errors)}")
    logging.info(f"Output files:")
    logging.info(f"  - Updated map: {updated_map_file}")
    logging.info(f"  - Source username emails: {source_username_emails_file}")
    logging.info(f"  - Source username not found: {source_username_not_found_file}")
    logging.info(f"  - Destination email not found: {destination_email_not_found_file}")

if __name__ == "__main__":
    main()