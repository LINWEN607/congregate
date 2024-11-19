# As implied by the name, this looks on the destination for a user based on a primary email provided from the source system
# The source primary email would require an admin token unless ALL public_emails are set for users on the source system (which we usually require)
# Likewise on the destination, we are using an admin token to search for users primary (not public) email
# With some small updates, this could be used to search for public_email as well
# The idea of this one in the context of placeholder user mapping is to use the primary email as a pivot to retrieve destination usernames
# to populate the mapping CSV file for ingestion
# The source CSV should have one field:
# 	source_primary_email : The primary email on source that should match the primary email on destination
# The outpu destination file will have the fields:
# 	destination_username : The username found by the search
# 	destination_primary_email : The destination primary email, which should match the source_primary_email
# Replace the file names in the main() func
#     input_file = "source-usernames-and-emails.csv"
#     output_file = "destination-usernames-and-emails.csv"


import csv
import requests
import os
from typing import List, Dict
import logging
from requests.exceptions import RequestException

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# GitLab API endpoint and access token
DESTINATION_GITLAB_ROOT  = os.environ.get("DESTINATION_GITLAB_ROOT", "")
DESTINATION_GITLAB_GRAPHQL_URL = f"{DESTINATION_GITLAB_ROOT}/api/graphql"
DESTINATION_ADMIN_ACCESS_TOKEN = os.environ.get("DESTINATION_ADMIN_ACCESS_TOKEN", "")

def read_email_addresses(file_path: str) -> List[str]:
    """
    Read email addresses from the CSV file.

    Args:
        file_path (str): The path to the CSV file containing email addresses.

    Returns:
        List[str]: A list of email addresses extracted from the CSV file.
    """
    email_addresses = []
    with open(file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            email_addresses.append(row['source_primary_email'])
    return email_addresses

def find_users_by_email(email_addresses: List[str]) -> List[Dict]:
    """
    Find users by email using GitLab GraphQL API.

    Args:
        email_addresses (List[str]): A list of email addresses to search for.

    Returns:
        List[Dict]: A list of dictionaries containing user information.
        Each dictionary has 'destination_username' and 'destination_primary_email' keys.
        If a user is not found, the 'destination_username' will be an empty string.
    """
    headers = {
        "Authorization": f"Bearer {DESTINATION_ADMIN_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    query = """
    query($email: String!) {
      users(search: $email) {
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

    users = []
    for email in email_addresses:
        variables = {"email": email}
        try:
            response = requests.post(DESTINATION_GITLAB_GRAPHQL_URL, json={"query": query, "variables": variables}, headers=headers)
            response.raise_for_status()  # Raises an HTTPError for bad responses

            data = response.json()
            if 'errors' in data:
                logging.error(f"GraphQL error for email {email}: {data['errors']}")
                continue

            if 'data' not in data or 'users' not in data['data']:
                logging.error(f"Unexpected response structure for email {email}")
                continue

            user_nodes = data['data']['users']['nodes']
            if len(user_nodes) == 1:
                users.append({
                    "destination_username": user_nodes[0]['username'],
                    "destination_primary_email": email,
                    "destination_gid": user_nodes[0]['id']
                })
            elif len(user_nodes) > 1:
                logging.warning(f"Found multiple users for email {email}. Skipping...")
            else:
                users.append({
                    "destination_username": "",
                    "destination_primary_email": email,
                    "destination_gid": ""
                })

        except RequestException as e:
            logging.error(f"Request failed for email {email}: {str(e)}")
        except KeyError as e:
            logging.error(f"Unexpected data structure in response for email {email}: {str(e)}")
        except Exception as e:
            logging.error(f"Unexpected error processing email {email}: {str(e)}")

    return users

def write_output_csv(users: List[Dict], output_file: str):
    """
    Write user data to output CSV file.

    Args:
        users (List[Dict]): A list of dictionaries containing user information.
            Each dictionary should have 'destination_username' and 'destination_primary_email' keys.
        output_file (str): The path to the output CSV file.

    Returns:
        None
    """
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['destination_username', 'destination_primary_email', 'destination_gid']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for user in users:
            writer.writerow({
                'destination_username': user['destination_username'],
                'destination_primary_email': user['destination_primary_email'],
                'destination_gid': user['destination_gid']
            })

def main():
    """
    Main function to orchestrate the process of reading email addresses,
    finding users, and writing the results to a CSV file.
    """
    input_file = "source-usernames-and-emails.csv"
    output_file = "destination-usernames-and-emails.csv"

    email_addresses = read_email_addresses(input_file)
    users = find_users_by_email(email_addresses)
    write_output_csv(users, output_file)

    print(f"Process completed. Output written to {output_file}")

if __name__ == "__main__":
    main()