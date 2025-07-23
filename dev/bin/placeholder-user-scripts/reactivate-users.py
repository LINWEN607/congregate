#!/usr/bin/env python3
"""
GitLab User Reactivation Script
Reactivates deactivated user accounts based on a list of emails.

Usage:

# Default dry-run mode (safe - no changes made)
python reactivate-users.py emails.txt --url https://your-gitlab.com --token YOUR_TOKEN

# Execute mode (actually reactivates users)
python reactivate-users.py emails.txt --url https://your-gitlab.com --token YOUR_TOKEN --execute
"""

import argparse
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Set, Any

import gitlab
import requests


def read_email_list(filename: str) -> List[str]:
    """Read email addresses from a text file."""
    try:
        return Path(filename).read_text().strip().splitlines()
    except FileNotFoundError:
        sys.exit(f"Error: File '{filename}' not found.")
    except Exception as e:
        sys.exit(f"Error reading file: {e}")


def find_users_by_emails(
    gl: gitlab.Gitlab,
    emails: List[str],
    gitlab_url: str,
    token: str
) -> Tuple[Dict[str, Any], Set[str]]:
    """Find GitLab users by their email addresses using GraphQL."""
    users_by_email = {}
    not_found = set(emails)

    print("Searching for users...")

    query = """
    query($email: String!) {
        users(search: $email, first: 10) {
            nodes {
                id
                username
                state
                emails {
                    nodes {
                        email
                    }
                }
            }
        }
    }
    """

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    graphql_url = f"{gitlab_url}/api/graphql"

    for email in emails:
        try:
            response = requests.post(
                graphql_url,
                json={'query': query, 'variables': {'email': email}},
                headers=headers
            )
            response.raise_for_status()
            data = response.json()

            users = data.get('data', {}).get('users', {}).get('nodes', [])

            for user_data in users:
                user_emails = {e['email'] for e in user_data['emails']['nodes']}
                if email in user_emails:
                    # Extract user ID from GraphQL ID (format: gid://gitlab/User/123)
                    user_id = int(user_data['id'].split('/')[-1])
                    users_by_email[email] = gl.users.get(user_id)
                    not_found.discard(email)
                    break

        except requests.exceptions.RequestException as e:
            print(f"Error searching for user with email {email}: {e}")
        except Exception as e:
            print(f"Error processing user with email {email}: {e}")

    return users_by_email, not_found


def reactivate_users(
    users: Dict[str, Any],
    dry_run: bool = True
) -> Tuple[List[str], List[str], List[Tuple[str, str]]]:
    """Reactivate deactivated users."""
    reactivated = []
    already_active = []
    errors = []

    for email, user in users.items():
        try:
            if user.state == 'deactivated':
                if not dry_run:
                    user.activate()
                reactivated.append(email)
            elif user.state == 'active':
                already_active.append(email)
            else:
                print(f"Warning: User {email} has state '{user.state}' (not deactivated)")

        except gitlab.exceptions.GitlabError as e:
            errors.append((email, str(e)))

    return reactivated, already_active, errors


def print_results(
    emails: List[str],
    users_found: Dict[str, Any],
    not_found: Set[str],
    reactivated: List[str],
    already_active: List[str],
    errors: List[Tuple[str, str]],
    dry_run: bool
) -> None:
    """Print formatted results and summary."""
    if not_found:
        print(f"\nUsers not found for {len(not_found)} email(s):")
        for email in sorted(not_found):
            print(f"  - {email}")

    if not users_found:
        print("\nNo users found to process.")
        return

    print(f"\nFound {len(users_found)} user(s) in GitLab")

    # Print mode
    mode = "DRY RUN" if dry_run else "LIVE"
    print(f"\n{'='*50}")
    print(f"Running in {mode} mode")
    print(f"{'='*50}")

    # Print results
    if reactivated:
        action = "Would reactivate" if dry_run else "Reactivated"
        print(f"\n{action} {len(reactivated)} user(s):")
        for email in sorted(reactivated):
            print(f"  ✓ {email}")

    if already_active:
        print(f"\nAlready active: {len(already_active)} user(s):")
        for email in sorted(already_active):
            print(f"  • {email}")

    if errors:
        print(f"\nErrors encountered for {len(errors)} user(s):")
        for email, error in errors:
            print(f"  ✗ {email}: {error}")

    # Summary
    print(f"\n{'='*50}")
    print("SUMMARY:")
    print(f"  Total emails provided: {len(emails)}")
    print(f"  Users found: {len(users_found)}")
    print(f"  Users not found: {len(not_found)}")

    if dry_run:
        print(f"  Would reactivate: {len(reactivated)}")
    else:
        print(f"  Reactivated: {len(reactivated)}")

    print(f"  Already active: {len(already_active)}")
    print(f"  Errors: {len(errors)}")
    print(f"{'='*50}")

    if dry_run and reactivated:
        print("\nTo apply changes, run with --execute flag")


def main():
    parser = argparse.ArgumentParser(
        description='Reactivate deactivated GitLab users from a list of emails'
    )
    parser.add_argument(
        'email_file',
        help='Text file containing email addresses (one per line)'
    )
    parser.add_argument(
        '--url',
        required=True,
        help='GitLab instance URL (required for self-hosted instances)'
    )
    parser.add_argument(
        '--token',
        required=True,
        help='GitLab personal access token with admin privileges'
    )
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Execute the reactivation (default is dry-run mode)'
    )

    args = parser.parse_args()
    dry_run = not args.execute

    # Read and validate emails
    emails = read_email_list(args.email_file)
    emails = [email.strip() for email in emails if email.strip()]

    print(f"Found {len(emails)} email addresses in {args.email_file}")

    if not emails:
        print("No email addresses found. Exiting.")
        return

    # Initialize GitLab connection
    try:
        gl = gitlab.Gitlab(args.url, private_token=args.token)
        gl.auth()
    except gitlab.exceptions.GitlabAuthenticationError:
        sys.exit("Error: Authentication failed. Check your token and permissions.")
    except Exception as e:
        sys.exit(f"Error connecting to GitLab: {e}")

    # Find users and reactivate
    users_by_email, not_found = find_users_by_emails(gl, emails, args.url, args.token)

    if users_by_email:
        reactivated, already_active, errors = reactivate_users(users_by_email, dry_run)
    else:
        reactivated, already_active, errors = [], [], []

    # Display results
    print_results(
        emails, users_by_email, not_found,
        reactivated, already_active, errors, dry_run
    )


if __name__ == '__main__':
    main()