"""
File: check_merge_request_sizes.py

This script analyzes merge request sizes for GitLab projects within a specified group and its subgroups.
It uses the GitLab API to retrieve information about projects, merge requests, and subgroups.
The script performs the following main tasks:

1. Connects to a GitLab instance using a provided URL and private token.
2. Recursively processes a root group and all its subgroups.
3. For each project found, it retrieves all merge requests.
4. Calculates the size of each merge request by converting it to a JSON string.
5. Writes the results to a CSV file, including:
   - Project ID
   - Merge Request IID
   - Merge Request Title
   - JSON Size in MB
   - Whether the size exceeds a specified maximum

The script uses pagination to handle large numbers of results from the GitLab API.
It's useful for identifying oversized merge requests that may cause performance issues or exceed GitLab's limits.

Usage: Update the configuration variables in the main() function before running the script.

Note: The current settings is 50 MB per item based on the code located here : https://gitlab.com/gitlab-org/gitlab/-/blob/master/lib/gitlab/import_export/json/ndjson_reader.rb?ref_type=heads#L7
"""

import requests
import csv
import json
from typing import Generator
import sys

class GitLabAPI:
    def __init__(self, base_url: str, private_token: str):
        self.base_url = base_url.rstrip('/')
        self.headers = {'PRIVATE-TOKEN': private_token}
        
    def get_paginated_results(self, url: str) -> Generator[dict, None, None]:
        """Generator function to handle GitLab API pagination"""
        page = 1
        while True:
            response = requests.get(f"{url}?page={page}&per_page=100", 
                                 headers=self.headers)
            if response.status_code != 200:
                print(f"Error accessing {url}: {response.status_code}", 
                      file=sys.stderr)
                break
                
            results = response.json()
            if not results:
                break
                
            yield from results
            page += 1

    def get_subgroups(self, group_id: int) -> Generator[dict, None, None]:
        """Get all subgroups for a given group ID"""
        url = f"{self.base_url}/api/v4/groups/{group_id}/subgroups"
        yield from self.get_paginated_results(url)

    def get_projects(self, group_id: int) -> Generator[dict, None, None]:
        """Get all projects for a given group ID"""
        url = f"{self.base_url}/api/v4/groups/{group_id}/projects"
        yield from self.get_paginated_results(url)

    def get_merge_requests(self, project_id: int) -> Generator[dict, None, None]:
        """Get all merge requests for a given project ID"""
        url = f"{self.base_url}/api/v4/projects/{project_id}/merge_requests"
        yield from self.get_paginated_results(url)

def process_group(api: GitLabAPI, group_id: int, csv_writer: csv.writer, max_size: int):
    """Process a group and all its subgroups recursively"""
    
    # Process all projects in the current group
    for project in api.get_projects(group_id):
        project_id = project['id']
        print(f"Processing project: {project['name']}")
        
        # Process all merge requests in the project
        for mr in api.get_merge_requests(project_id):
            # Convert merge request to JSON string to calculate size
            mr_json = json.dumps(mr)
            size_mb = len(mr_json.encode('utf-8')) / (1024 * 1024)  # Convert bytes to MB
            over_size = True if size_mb > max_size else False
            # Write row to CSV
            csv_writer.writerow([
                project_id,
                mr['iid'],
                mr['title'],
                f"{size_mb:.8f}",
                over_size
            ])
    
    # Process all subgroups recursively
    for subgroup in api.get_subgroups(group_id):
        print(f"Processing subgroup: {subgroup['name']}")
        process_group(api, subgroup['id'], csv_writer, max_size)

def main():
    # Configuration
    GITLAB_URL = "https://gitlab.com"  # Replace with your GitLab instance URL
    PRIVATE_TOKEN = "TESTING"
    ROOT_GROUP_ID = 123  # Replace with your root group ID
    OUTPUT_FILE = "merge_requests.csv"
    PER_ITEM_SIZE_MAX = 50 # Size in MB

    # Initialize GitLab API client
    api = GitLabAPI(GITLAB_URL, PRIVATE_TOKEN)
    
    # Set up CSV file
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        
        # Write header
        csv_writer.writerow(['Project_ID','IID', 'Title', 'JSON Size (MB)', 'Over?'])
        
        # Process root group and all its subgroups
        print(f"Starting processing from group ID: {ROOT_GROUP_ID}")
        process_group(api, ROOT_GROUP_ID, csv_writer, PER_ITEM_SIZE_MAX)
        
    print(f"Processing complete. Results written to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
