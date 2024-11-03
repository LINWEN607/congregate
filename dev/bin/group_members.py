# Small script to return the actual source group names and path  of group members that are groups themselves

# export SRC_TOKEN=your_gitlab_token
# export SRC_HOST=http://your.gitlab.hostname  # Include http:// or https://
# export CONGREGATE_PATH=/path/to/your/data


import json
import os
import requests
import sys
import urllib3
import time
from multiprocessing import Pool, current_process
import argparse

# Suppress SSL warning if verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def extract_all_full_paths():
    # Get the directory path from environment variable 'CONGREGATE_PATH'
    base_path = os.getenv('CONGREGATE_PATH')
    if not base_path:
        sys.exit("Error: Environment variable 'CONGREGATE_PATH' is not set.")
    
    # Construct the full path to the JSON file
    file_path = os.path.join(base_path, 'data', 'groups.json')

    # Check if the file exists
    if not os.path.isfile(file_path):
        sys.exit(f"Error: File '{file_path}' not found.")

    unique_paths = set()  # Use a set to automatically handle uniqueness

    # Open and read the JSON file
    with open(file_path, 'r') as json_file:
        data = json.load(json_file)

        # Iterate over the list to find all "full_path" keys
        for item in data:
            if isinstance(item, dict) and "full_path" in item:
                unique_paths.add(item["full_path"])

    return list(unique_paths)

def query_gitlab_api(group_full_path):
    # Get GitLab API token from environment variable 'SRC_TOKEN'
    token = os.getenv('SRC_TOKEN')
    if not token:
        sys.exit("Error: Environment variable 'SRC_TOKEN' is not set.")
    
    # Get GitLab hostname from environment variable 'SRC_HOST'
    hostname = os.getenv('SRC_HOST')
    if not hostname:
        sys.exit("Error: Environment variable 'SRC_HOST' is not set.")

    # SSL verification option from environment variable 'VERIFY_SSL'
    verify_ssl = os.getenv('VERIFY_SSL', 'True').lower() in ['true', '1', 't', 'yes']

    # GitLab GraphQL endpoint
    url = f'{hostname}/api/graphql'

    # GraphQL query using variables
    query = """
    query($groupFullPath: ID!) {
      group(fullPath: $groupFullPath) {
        groupMembers(relations: [SHARED_FROM_GROUPS]) {
          nodes {
            id
            group {
              id
              name
            }
          }
        }
      }
    }
    """

    # Define the variables for the query
    variables = {
        "groupFullPath": group_full_path
    }

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    # Exponential back-off parameters
    backoff_time = 1  # Start with 1 second
    max_backoff = 60  # Maximum back-off time is 60 seconds

    while True:
        response = requests.post(url, json={'query': query, 'variables': variables}, headers=headers, verify=verify_ssl)

        # Check for a successful response
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            print(f"Rate limit reached for group '{group_full_path}', backing off for {backoff_time} seconds.")
            time.sleep(backoff_time)
            backoff_time = min(backoff_time * 2, max_backoff)  # Exponential back-off
        else:
            raise Exception(f"Query failed with status code {response.status_code}: {response.text}")

def process_group(group_full_path):
    try:
        # Progress output for each group processed
        process_name = current_process().name
        print(f"{process_name}: Processing group '{group_full_path}'")

        result = query_gitlab_api(group_full_path)
        group_names = set()

        if result:
            # Extract group names from the response
            group_members = result.get("data", {}).get("group", {}).get("groupMembers", {}).get("nodes", [])
            for member in group_members:
                group = member.get("group")
                if group and "name" in group:
                    group_names.add(group["name"])

        return group_full_path, list(group_names)

    except Exception as e:
        return group_full_path, f"Error: {e}"

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Run GitLab GraphQL queries with multiprocessing.")
    parser.add_argument("-p", "--processes", type=int, default=4, help="Number of worker processes to use")
    args = parser.parse_args()

    # Extract all full paths
    all_full_paths = extract_all_full_paths()

    # Use multiprocessing Pool to query API in parallel
    with Pool(processes=args.processes) as pool:
        results = pool.map(process_group, all_full_paths)

    # Collect unique group names from all results
    output_data = []
    total_checked = 0
    groups_with_subgroups = 0

    # Print results and prepare data for output
    for full_path, result in results:
        total_checked += 1
        if isinstance(result, list) and result:
            output_data.append({"group_full_path": full_path, "group_names": result})
            groups_with_subgroups += 1
            print(f"Results for group '{full_path}': {result}")
        elif isinstance(result, str):
            print(f"Results for group '{full_path}': {result}")

    # Get output path from environment variable
    base_path = os.getenv('CONGREGATE_PATH')
    if not base_path:
        sys.exit("Error: Environment variable 'CONGREGATE_PATH' is not set.")
    
    output_file_path = os.path.join(base_path, 'data', 'results', 'group_members_as_groups.json')

    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

    # Write results to JSON file (excluding empty group_names)
    if output_data:
        with open(output_file_path, 'w') as output_file:
            json.dump(output_data, output_file, indent=2)

    # Print summary
    print(f"\nSummary:")
    print(f"Total groups checked: {total_checked}")
    print(f"Total groups with subgroup members found: {groups_with_subgroups}")
