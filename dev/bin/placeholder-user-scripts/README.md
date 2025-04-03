# GitLab User Migration and Placeholder Management Guide

This guide outlines the end-to-end process for managing user migrations in GitLab, specifically for mapping users from a source GitLab instance to a destination instance and handling placeholder users.

## Overview

The migration process follows these steps:

1. Receive a list of user emails from the customer
2. Download placeholder users from the target GitLab group
3. Create user mappings between source and destination GitLab instances
4. Update placeholder user assignments on the destination GitLab instance
5. (Optional) Cancel any reassignments that haven't been accepted by end users

## Prerequisites

Before beginning the migration process, ensure you have:

- Admin access tokens for both source and destination GitLab instances
- The full path of the target GitLab group
- A list of user email addresses to be migrated

Set the following environment variables:

```bash
# For source GitLab instance
export SOURCE_GITLAB_ROOT="https://gitlab.source.com"
export SOURCE_ADMIN_ACCESS_TOKEN="glpat-xxxxxxxxxxxxxxxxxxxx"

# For destination GitLab instance
export DESTINATION_GITLAB_ROOT="https://gitlab.example.com"
export DESTINATION_ADMIN_ACCESS_TOKEN="glpat-xxxxxxxxxxxxxxxxxxxx"
```

## Step 1: Receive User Email List

Obtain a text file from the customer containing one email address per line for all users to be migrated:

```txt
user1@example.com
user2@example.com
user3@example.com
```

## Step 2: Download Placeholder Users

Run the script to retrieve placeholder users from the target GitLab group:

```bash
python retrieve-placeholder-users-for-namespace.py
```

Before running, set the required environment variables:

```bash
export DESTINATION_GITLAB_ROOT="https://gitlab.example.com"
export DESTINATION_ADMIN_ACCESS_TOKEN="somepat-xxxxxxxxxxxxxxxxxxxx"
export DESTINATION_CUSTOMER_NAME="demo"
export DESTINATION_TOP_LEVEL_GROUP="import-target"
```

This scripts calls the [API](https://docs.gitlab.com/api/group_placeholder_reassignments/#download-the-csv-file) and will generate a CSV file containing details about placeholder users. Example:

```
Source host,Import type,Source user identifier,Source user name,Source username,GitLab username,GitLab public email
http://gitlab.example,gitlab_migration,11,Bob,bob,"",""
http://gitlab.example,gitlab_migration,9,Alice,alice,"",""
```
The data is written to a CSV named with the pattern:

```python
output_file = f"{customer_name}_{group_full_path}_{timestamp}_placeholder_users.csv"  # Name of the output CSV file
```

## Step 3: Create User Mappings

Use the mapping script to match users between source and destination GitLab instances. It receives the file created in [Step 2](#step-2-download-placeholder-users) as input

```bash
python gitlab_user_mapping.py email_list.txt placeholder_users_from_step_2.csv [OPTIONS]
```

### Command Line Options:

Options:
    --log-level LEVEL          Set logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)
    --help                     Show this help message and exit

### Example:

```bash
python gitlab_user_mapping.py email_list.txt customer_topgroup_20250401081822_placeholder_users.csv --log-level INFO
```

This script will:

- Maps users between GitLab instances by email address
- Update placeholder user IDs for migration processes
- Validate mappings by cross-checking emails and usernames
- Record emails not found in GitLab instances
- Provide detailed logging and progress reporting

See the [gitlab_user_mapping.py](./gitlab_user_mapping.py) script for more details on the process and output.

## Step 4: Update Placeholder Mappings

Upload the user mappings to reassign placeholder users to actual GitLab users:

```bash
python update-placeholder-mapping.py [--commit] [input_csv_file]
```

By default, the script runs in dry-run mode. Use the `--commit` flag to apply the changes.

This script will:

1. Read the updated placeholder users CSV generated in [Step 3](#step-3-create-user-mappings)
2. Make [API](https://docs.gitlab.com/api/group_placeholder_reassignments/#reassign-placeholders) calls to the destination GitLab instance that will reassign placeholder users to actual GitLab users

## Step 5: Cancel Reassignments (Optional)

If needed, you can cancel any user reassignments that haven't been accepted:

```bash
python cancel_reassignments.py placeholder_users-generated.csv
```

This will process the CSV file and call a GraphQL mutation to cancel the pending reassignments.

## Output Files

Throughout this process, several files will be generated:

1. `placeholder_users.csv`: Initial export of placeholder users
2. `gitlab_user_mapping_YYYYMMDD_HHMMSS.csv`: Mapping between source and destination users
3. `placeholder_users-generated.csv`: Updated placeholder users with assignee IDs
4. `gitlab_user_mapping_YYYYMMDD_HHMMSS.log`: Detailed log of the mapping process
5. (Optional) CSV files recording emails not found in GitLab instances

## Troubleshooting

- **API Request Errors**: Check that your access tokens have sufficient permissions
- **User Not Found**: Ensure email addresses are correct and users exist in both GitLab instances
- **Failed Reassignments**: Review the log files and retry the process for failed entries
- **Pending Reassignments**: Use the cancellation script to clear any pending reassignments before retrying

## Notes

- The scripts use GitLab's GraphQL API for efficient querying
- Matching is done by email address (case-insensitive)
- Admin-level API tokens are required to access user information
- For placeholder updating, source_username is used as the matching key