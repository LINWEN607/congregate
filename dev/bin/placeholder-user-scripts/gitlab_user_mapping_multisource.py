"""
Multi-Source GitLab User Mapping Script
======================================

This script maps users between various source code management systems and GitLab.
It supports multiple source systems (GitHub, BitBucket Server, Gitea, GitLab) and
provides options for enterprise API usage.

It takes a CSV file of downloaded placeholder mappings and:
1. Queries the source system for each username to get all associated emails
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
    python3 gitlab_user_mapping.py placeholder_mappings.csv --source-type TYPE [OPTIONS]

Arguments:
    placeholder_mappings.csv   Path to a CSV file containing placeholder mappings

Required Options:
    --source-type TYPE         Specify the source system type: gitlab, github, bitbucket, gitea

Options:
    --source-enterprise        Use the enterprise users API for source GitLab (requires --source-type gitlab)
    --destination-enterprise   Use the enterprise users API for destination GitLab
    --log-level LEVEL          Set logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)
    --help                     Show this help message and exit

Environment Variables:
---------------------------------
    # Required for all source types
    DESTINATION_GITLAB_ROOT     Base URL for the destination GitLab instance (e.g., https://gitlab.dest.com)
    DESTINATION_ADMIN_ACCESS_TOKEN  Admin access token for the destination GitLab instance

    # Required when --destination-enterprise is used
    DESTINATION_GROUP_ID        Group ID to search in for destination enterprise users API

    # Required for GitLab source (--source-type gitlab)
    SOURCE_GITLAB_ROOT          Base URL for the source GitLab instance (e.g., https://gitlab.source.com)
    SOURCE_ADMIN_ACCESS_TOKEN   Admin access token for the source GitLab instance

    # Required when --source-enterprise is used
    SOURCE_GROUP_ID             Group ID to search in for source enterprise users API

    # Required for GitHub source (--source-type github)
    GITHUB_API_URL              Base URL for GitHub API (e.g., https://api.github.com or https://github.company.com/api/v3)
    GITHUB_TOKEN                Personal access token for GitHub API

    # Required for Bitbucket Server source (--source-type bitbucket)
    BITBUCKET_API_URL           Base URL for Bitbucket Server API
    BITBUCKET_USERNAME          Username for Bitbucket Server API
    BITBUCKET_PASSWORD          Password or token for Bitbucket Server API

    # Required for Gitea source (--source-type gitea)
    GITEA_API_URL               Base URL for Gitea API
    GITEA_TOKEN                 Access token for Gitea API

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
    - Supports multiple source systems (GitLab, GitHub, BitBucket Server, Gitea)
    - Maps users between systems by looking up emails for source usernames
    - Updates placeholder user IDs for migration processes
    - Records emails not found in destination GitLab instance
    - Provides detailed logging and progress reporting
    - Options to use enterprise users API for both source and destination GitLab

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
    - The script uses appropriate APIs for each source system
    - It handles cases where users exist in only one of the systems
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
from typing import List, Dict, Optional, Any

# Configure logging - moved to main function to allow for command-line level selection

def setup_logging(level_name: str) -> logging.Logger:
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

    def __init__(self, gitlab_url: str, access_token: str, instance_name: str, group_id: Optional[str] = None,
                 use_enterprise: bool = False):
        self.gitlab_url = gitlab_url.rstrip('/')
        self.api_url = f"{self.gitlab_url}/api/graphql"
        self.rest_api_url = f"{self.gitlab_url}/api/v4"
        self.access_token = access_token
        self.instance_name = instance_name
        self.group_id = group_id
        self.use_enterprise = use_enterprise
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

    def query_user_by_username(self, username: str) -> Optional[Dict]:
        """Query a user by username using GraphQL or Enterprise API based on settings."""
        if self.use_enterprise:
            if not self.group_id:
                if self.instance_name == "source":
                    var_name = "SOURCE_GROUP_ID"
                else:  # destination
                    var_name = "DESTINATION_GROUP_ID"
                logging.error(f"{var_name} environment variable is required when using enterprise users API")
                sys.exit(1)
            return self._query_user_by_username_enterprise(username)
        else:
            return self._query_user_by_username_standard(username)

    def _query_user_by_username_standard(self, username: str) -> Optional[Dict]:
        """Query a user by username using standard GraphQL API."""
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

    def _query_user_by_username_enterprise(self, username: str) -> Optional[Dict]:
        """Query a user by username using the group enterprise users API."""
        try:
            # Search enterprise users by username using REST API
            endpoint = f"{self.rest_api_url}/groups/{self.group_id}/enterprise_users"
            params = {"username": username}

            response = requests.get(
                endpoint,
                headers=self.headers,
                params=params
            )
            response.raise_for_status()

            users = response.json()

            # Find the user with the matching username (exact match)
            matching_user = None
            for user in users:
                if user.get("username", "").lower() == username.lower():
                    matching_user = user
                    break

            if not matching_user:
                logging.warning(f"No enterprise user found in {self.instance_name} for username: {username}")
                return None

            # Extract email information
            emails = []
            public_email = matching_user.get("public_email")
            primary_email = None

            for email_data in matching_user.get("emails", []):
                email = email_data.get("email")
                if not email:
                    continue

                is_primary = email_data.get("primary", False)
                is_public = (email == public_email)

                if is_primary:
                    primary_email = email

                emails.append({
                    "email": email,
                    "is_primary": is_primary,
                    "is_public": is_public
                })

            return {
                "username": matching_user.get("username"),
                "emails": emails,
                "public_email": public_email,
                "primary_email": primary_email,
                "gid": matching_user.get("id")
            }

        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed for {self.instance_name} when querying enterprise users for username {username}: {str(e)}")
            return None

    def query_user_by_email(self, email: str) -> Optional[Dict]:
        """
        Query a user by email using GraphQL or REST API based on settings.
        Returns the user details if found.
        """
        if self.use_enterprise:
            if not self.group_id:
                if self.instance_name == "source":
                    var_name = "SOURCE_GROUP_ID"
                else:  # destination
                    var_name = "DESTINATION_GROUP_ID"
                logging.error(f"{var_name} environment variable is required when using enterprise users API")
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

class GitHubClient:
    """Client to interact with GitHub API."""

    def __init__(self, api_url: str, token: str):
        self.api_url = api_url.rstrip('/')
        self.token = token
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def query_user_by_username(self, username: str) -> Optional[Dict]:
        """Query a user by username and return their details including email."""
        try:
            # Get user details
            user_url = f"{self.api_url}/users/{username}"
            response = requests.get(user_url, headers=self.headers)
            response.raise_for_status()

            user_data = response.json()

            # Get user's public email from profile
            public_email = user_data.get("email")

            # Get user's commit emails (for GitHub Enterprise)
            # This is a heuristic approach as GitHub API doesn't expose all emails
            emails = []

            if public_email:
                emails.append({
                    "email": public_email,
                    "is_public": True,
                    "is_primary": True  # Assume public email is primary
                })

            # Try to get additional emails from the emails API endpoint (works for authenticated user only)
            # This might not work for all users depending on permissions
            try:
                email_url = f"{self.api_url}/user/emails"
                email_response = requests.get(email_url, headers=self.headers)

                if email_response.status_code == 200:
                    email_data = email_response.json()

                    for email_item in email_data:
                        email = email_item.get("email")
                        if email and email not in [e["email"] for e in emails]:
                            is_primary = email_item.get("primary", False)

                            emails.append({
                                "email": email,
                                "is_public": False,  # These are typically private emails
                                "is_primary": is_primary
                            })
            except Exception as e:
                logging.warning(f"Could not fetch additional emails for GitHub user {username}: {str(e)}")

            if not emails:
                logging.warning(f"No emails found for GitHub user {username}")
                return None

            # Find primary email
            primary_email = None
            for email_info in emails:
                if email_info.get("is_primary"):
                    primary_email = email_info.get("email")
                    break

            if not primary_email and emails:
                primary_email = emails[0].get("email")  # Use first email as primary if none marked

            return {
                "username": username,
                "emails": emails,
                "public_email": public_email,
                "primary_email": primary_email
            }

        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed when querying GitHub username {username}: {str(e)}")
            return None

class BitbucketServerClient:
    """Client to interact with Bitbucket Server API."""

    def __init__(self, api_url: str, username: str, password: str):
        self.api_url = api_url.rstrip('/')
        self.username = username
        self.password = password
        self.auth = (username, password)

    def query_user_by_username(self, username: str) -> Optional[Dict]:
        """Query a user by username and return their details including email."""
        try:
            # Get user details
            user_url = f"{self.api_url}/users/{username}"
            response = requests.get(user_url, auth=self.auth)
            response.raise_for_status()

            user_data = response.json()

            # Bitbucket Server typically has a single email per user
            email = user_data.get("emailAddress")

            if not email:
                logging.warning(f"No email found for Bitbucket Server user {username}")
                return None

            # Create formatted email info
            emails = [{
                "email": email,
                "is_public": True,  # Assume email is public
                "is_primary": True  # Only one email, so it's primary
            }]

            return {
                "username": username,
                "emails": emails,
                "public_email": email,
                "primary_email": email
            }

        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed when querying Bitbucket Server username {username}: {str(e)}")
            return None

class GiteaClient:
    """Client to interact with Gitea API."""

    def __init__(self, api_url: str, token: str):
        self.api_url = api_url.rstrip('/')
        self.token = token
        self.headers = {
            "Authorization": f"token {token}",
            "Content-Type": "application/json"
        }

    def query_user_by_username(self, username: str) -> Optional[Dict]:
        """Query a user by username and return their details including email."""
        try:
            # Get user details
            user_url = f"{self.api_url}/users/{username}"
            response = requests.get(user_url, headers=self.headers)
            response.raise_for_status()

            user_data = response.json()

            # Gitea typically exposes a single email per user
            email = user_data.get("email")

            if not email:
                logging.warning(f"No email found for Gitea user {username}")
                return None

            # Create formatted email info
            emails = [{
                "email": email,
                "is_public": True,  # Assume email is public
                "is_primary": True  # Only one email, so it's primary
            }]

            return {
                "username": username,
                "emails": emails,
                "public_email": email,
                "primary_email": email
            }

        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed when querying Gitea username {username}: {str(e)}")
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

def find_destination_user_by_emails(destination_client: GitLabGraphQLClient, emails: List[Dict]) -> Optional[Dict]:
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
        destination_user = destination_client.query_user_by_email(email)
        if destination_user:
            # Return the matching email along with the user data
            destination_user["matched_email"] = email
            return destination_user

    return None

def initialize_source_client(source_type: str, args) -> Any:
    """Initialize the appropriate client for the source system."""
    if source_type == "gitlab":
        # Get GitLab source environment variables
        source_url = get_environment_variable("SOURCE_GITLAB_ROOT")
        source_token = get_environment_variable("SOURCE_ADMIN_ACCESS_TOKEN")
        source_group_id = None

        if args.source_enterprise:
            source_group_id = get_environment_variable("SOURCE_GROUP_ID", required=True)
            logging.info(f"Using enterprise users API for source GitLab with group ID: {source_group_id}")

        # Initialize GitLab source client
        return GitLabGraphQLClient(
            source_url,
            source_token,
            "source",
            source_group_id,
            args.source_enterprise
        )

    elif source_type == "github":
        # Get GitHub environment variables
        github_api_url = get_environment_variable("GITHUB_API_URL")
        github_token = get_environment_variable("GITHUB_TOKEN")

        # Initialize GitHub client
        return GitHubClient(github_api_url, github_token)

    elif source_type == "bitbucket":
        # Get Bitbucket Server environment variables
        bitbucket_api_url = get_environment_variable("BITBUCKET_API_URL")
        bitbucket_username = get_environment_variable("BITBUCKET_USERNAME")
        bitbucket_password = get_environment_variable("BITBUCKET_PASSWORD")

        # Initialize Bitbucket Server client
        return BitbucketServerClient(bitbucket_api_url, bitbucket_username, bitbucket_password)

    elif source_type == "gitea":
        # Get Gitea environment variables
        gitea_api_url = get_environment_variable("GITEA_API_URL")
        gitea_token = get_environment_variable("GITEA_TOKEN")

        # Initialize Gitea client
        return GiteaClient(gitea_api_url, gitea_token)

    else:
        logging.error(f"Unsupported source type: {source_type}")
        sys.exit(1)

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Map users between various source systems and GitLab.")
    parser.add_argument("placeholder_file", help="Path to placeholder mappings CSV file")
    parser.add_argument("--source-type", required=True, choices=["gitlab", "github", "bitbucket", "gitea"],
                        help="Specify the source system type")
    parser.add_argument("--source-enterprise", action="store_true",
                        help="Use the enterprise users API for source GitLab (requires --source-type gitlab)")
    parser.add_argument("--destination-enterprise", action="store_true",
                        help="Use the enterprise users API for destination GitLab")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                       help="Set the logging level (default: INFO)")
    args = parser.parse_args()

    # Validate source-enterprise is only used with gitlab source type
    if args.source_enterprise and args.source_type != "gitlab":
        print("Error: --source-enterprise can only be used with --source-type gitlab")
        sys.exit(1)

    # Setup logging with the specified level
    logger = setup_logging(args.log_level)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Define output files
    updated_map_file = f"updated_map_{timestamp}.csv"
    source_username_emails_file = f"source_username_emails_{timestamp}.csv"
    source_username_not_found_file = f"source_username_not_found_{timestamp}.csv"
    destination_email_not_found_file = f"destination_email_not_found_{timestamp}.csv"

    logging.info(f"Starting user mapping process with source type: {args.source_type}")

    # Get destination environment variables
    try:
        destination_url = get_environment_variable("DESTINATION_GITLAB_ROOT")
        destination_token = get_environment_variable("DESTINATION_ADMIN_ACCESS_TOKEN")

        # Only needed if destination_enterprise flag is set
        destination_group_id = None
        if args.destination_enterprise:
            destination_group_id = get_environment_variable("DESTINATION_GROUP_ID", required=True)
            logging.info(f"Using enterprise users API for destination GitLab with group ID: {destination_group_id}")
    except SystemExit:
        return

    # Initialize the appropriate source client based on source type
    source_client = initialize_source_client(args.source_type, args)

    # Initialize destination GitLab client
    destination_client = GitLabGraphQLClient(
        destination_url,
        destination_token,
        "destination",
        destination_group_id,
        args.destination_enterprise
    )

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

        # Query source system for the username
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
        destination_user = find_destination_user_by_emails(destination_client, source_emails)

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
    logging.info("User mapping process completed")
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