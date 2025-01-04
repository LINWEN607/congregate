"""
File: check_merge_request_sizes.py

This codebase is verified to work with python-gitlab 4.5.0, which is compatible with Python 3.8.12, which Congregate currently runs on.
python-gitlab is not installed as part of the Congregate dependencies/.venv at this time, so you will need to `poetry add python-gitlab>=4.5.0` 
before running the poetry shell

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
import gitlab
from gitlab.v4.objects import Group, Project, ProjectMergeRequest
import csv
import json
from typing import Generator
import sys

class GitLabWrapper:
    def __init__(self, url: str, private_token: str):
        self.gl = gitlab.Gitlab(url, private_token)
    
    def get_group(self, group_id: int) -> Group:
        return self.gl.groups.get(group_id)
    
    def get_subgroups(self, group: Group) -> Generator[Group, None, None]:
        """Get all subgroups for a given group"""
        yield from group.subgroups.list(all=True)

    def get_projects(self, group: Group) -> Generator[Project, None, None]:
        """Get all projects for a given group"""
        yield from group.projects.list(all=True)

    def get_full_project(self, project_id: int) -> Project:
        """Get the full project object"""
        return self.gl.projects.get(project_id)

    def get_merge_requests(self, project: Project) -> Generator[ProjectMergeRequest, None, None]:
        """Get all merge requests for a given project"""
        yield from project.mergerequests.list(all=True)

def get_object_dict(obj) -> dict:
    """Convert a GitLab object to a dictionary in a way compatible with 4.5.0"""
    return obj._attrs

def process_group(gitlab_wrapper: GitLabWrapper, group_id: int, csv_writer: csv.writer, max_size: int) -> None:
    """Process a group and all its subgroups recursively"""
    
    try:
        group = gitlab_wrapper.get_group(group_id)
        print(f"Processing group: {group.name}")
        
        # Process all projects in the current group
        for group_project in gitlab_wrapper.get_projects(group):
            print(f"Processing project: {group_project.name}")
            
            # Get the full project object
            try:
                project = gitlab_wrapper.get_full_project(group_project.id)
                
                # Process all merge requests in the project
                for mr in gitlab_wrapper.get_merge_requests(project):
                    # Convert merge request to JSON string to calculate size
                    mr_dict = get_object_dict(mr)
                    mr_json = json.dumps(mr_dict)
                    size_mb = len(mr_json.encode('utf-8')) / (1024 * 1024)
                    over_size = size_mb > max_size

                    # Write row to CSV
                    csv_writer.writerow([
                        mr.iid,
                        mr.title,
                        f"{size_mb:.8f}",
                        over_size
                    ])
            except gitlab.exceptions.GitlabError as e:
                print(f"Error processing project {group_project.name}: {e}", 
                      file=sys.stderr)
                continue
        
        # Process all subgroups recursively
        for subgroup in gitlab_wrapper.get_subgroups(group):
            process_group(gitlab_wrapper, subgroup.id, csv_writer, max_size)
            
    except gitlab.exceptions.GitlabError as e:
        print(f"Error processing group {group_id}: {e}", file=sys.stderr)

def main():
    # Configuration
    GITLAB_URL = "https://gitlab.com"  # Replace with your GitLab instance URL
    PRIVATE_TOKEN = "TOKEN"
    ROOT_GROUP_ID = GROUPID  # Replace with your root group ID
    OUTPUT_FILE = "merge_requests.csv"
    MAX_SIZE = 50 # MB

    # Initialize GitLab client
    gitlab_wrapper = GitLabWrapper(GITLAB_URL, PRIVATE_TOKEN)
    
    # Set up CSV file
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        
        # Write header
        csv_writer.writerow(['IID', 'Title', 'JSON Size (MB)', 'Oversize'])
        
        # Process root group and all its subgroups
        print(f"Starting processing from group ID: {ROOT_GROUP_ID}")
        process_group(gitlab_wrapper, ROOT_GROUP_ID, csv_writer, MAX_SIZE)
        
    print(f"Processing complete. Results written to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()