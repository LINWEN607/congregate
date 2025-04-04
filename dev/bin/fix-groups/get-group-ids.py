import argparse
import requests
import sys
import csv
from datetime import datetime

# GitLab API base URL
GITLAB_API_BASE_URL = "https://gitlab.com/api/v4/groups"
PARENT_GROUP_ID = MYTLGID  # TODO: Replace with actual TLG ID

"""
USAGE INSTRUCTIONS:
-------------------
1. Save this script as get-group-ids.py and update instances of # TODO: Replace with actual TLG ID

2. Run the script with the group file and GitLab token:
    python get-group-ids.py -f missing_groups.txt -t <your_gitlab_token> -w <WaveName> -d <Date>

3. Ensure you have:
    - A valid GitLab Access Token with read_api scope.
    - A text file (missing_groups.txt) with one group path per line.

4. Output:
    - Generates a congregate stage-groups command (for quick fixes).
    - Creates stage-wave.csv formatted for stage-wave migration.

5. Purpose:
    - Fetches GitLab Group IDs for a list of group paths.
    - Generates a congregate command for staging the groups.
    - Outputs a structured CSV to be used with stage-wave.
"""

# Command-line argument parser
parser = argparse.ArgumentParser(description="Fetch GitLab Group IDs and generate congregate command + CSV for stage-wave.")
parser.add_argument("-f", "--file", required=True, help="Path to the file containing group paths.")
parser.add_argument("-t", "--token", required=True, help="GitLab Access Token.")
parser.add_argument("-w", "--wave", default="Wave-1", help="Wave name for stage-wave CSV (default: Wave-1).")
parser.add_argument("-d", "--date", default=datetime.today().strftime('%Y-%m-%d'), help="Wave date (default: today).")

args = parser.parse_args()

# Read file with group paths
try:
    with open(args.file, "r") as f:
        group_paths = [line.strip() for line in f.readlines()]
except FileNotFoundError:
    print(f"Error: File '{args.file}' not found.")
    sys.exit(1)

# Store group IDs
group_ids = {}

# GitLab API function to fetch group ID
def get_group_id(group_path):
    """
    Fetches the GitLab Group ID based on its full path.
    Uses the GitLab API with a search query filtered to PARENT_GROUP_ID.
    Returns the corresponding Group ID if found, else returns None.
    """
    url = f"{GITLAB_API_BASE_URL}?search={group_path}&parent_id={PARENT_GROUP_ID}"
    headers = {"PRIVATE-TOKEN": args.token}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        groups = response.json()
        for group in groups:
            if group["full_path"] == f"<TLG GOES HERE>/{group_path}": # TODO: Replace with actual TLG ID
                return group["id"]
    return None

# Fetch group IDs
for group_path in group_paths:
    group_id = get_group_id(group_path)
    if group_id:
        group_ids[group_path] = group_id

# Generate congregate stage-groups command
if group_ids:
    congregate_command = f"congregate stage-groups {', '.join(map(str, group_ids.values()))} --commit"
    print("\nGenerated Congregate Command:\n")
    print(congregate_command)
else:
    print("No valid groups found.")

# Generate stage-wave CSV file
csv_file = "stage-wave.csv"
csv_columns = ["Wave Name", "Wave Date", "Source Url", "Source Parent Path", "Destination Parent Path", "Override"]

with open(csv_file, "w", newline="") as csvfile:
    csv_writer = csv.writer(csvfile)
    csv_writer.writerow(csv_columns)

    for group_path, group_id in group_ids.items():
        # Construct source and destination paths
        source_url = f"https://gitlab.com/<TLG GOES HERE>/{group_path}" # TODO: Replace with actual TLG ID
        source_parent_path = "/".join(group_path.split("/")[:-1])  # Everything except the last segment
        destination_parent_path = source_parent_path  # Assuming destination matches source
        override = ""

        csv_writer.writerow([args.wave, args.date, source_url, source_parent_path, destination_parent_path, override])

print(f"\nCSV file '{csv_file}' generated successfully.")

# Output the results
print("\nGroup IDs Found:")
for group, gid in group_ids.items():
    print(f"{group} → {gid}")
