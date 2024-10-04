
# Troubleshooting File-Based Import Failures and Switching to Direct Transfer

When dealing with GitLab file-based imports, particularly those using S3, you might encounter prolonged delays or import failures. This troubleshooting guide walks through diagnosing such issues and switching to Direct Transfer to resolve them.

## Step 1: Diagnosing the Import with Kibana

If a file-based import is taking longer than expected, diagnose the issue using available logs. Start by checking the API endpoint for the project to locate the correlation ID:

```
/api/v4/projects/:ID/import
```

This endpoint provides the correlation ID, which can then be used in Kibana to search for logs. To search in Kibana, target `pubsub-sidekiq-inf-gprd*` using the following query:

```
json.class: "RepositoryImportWorker" AND json.correlation_id.keyword: "<Correlation ID from API>"
```

### Step 2: Finding Errors Using the `jid`

After running the query, you will retrieve a `json.jid`. Use this `jid` to search for error messages with the following query:

```
json.message: "<json.jid we found>"
```

Review the error messages for clues. If you find that the import worker failed due to interruptions, consider moving to Direct Transfer.

## Step 3: Switching to Direct Transfer

If the import worker fails or the job is taking too long, switch to Direct Transfer, which is less prone to interruptions.

### Step 4: Enabling Direct Transfer

Once Direct Transfer is enabled, verify that it is active on both the source and destination instances. The GitLab.com SaaS instance is usually pre-configured, but you may need to enable Direct Transfer on the source instance manually. After enabling and saving changes, you may experience a brief delay before the API call becomes functional.

If you encounter an error indicating that Direct Transfer is not enabled on both instances, wait a few moments and retry the API call until you receive a different error message.

## Step 5: Initiating the Direct Transfer

Once Direct Transfer is enabled, initiate the bulk import using the following API call:

```bash
curl --request POST   --header "PRIVATE-TOKEN: dest_pat_token"   --header "Content-Type: application/json"   --data '{ 
    "configuration": { 
      "url": "https://source.gitlab.com", 
      "access_token": "source_pat_token" 
    }, 
    "entities": [ 
      { 
        "source_full_path": "group/subgroup/repo", 
        "source_type": "project_entity", 
        "destination_slug": "repo_slug", 
        "destination_namespace": "namespace/group" 
      } 
    ] 
  }' \ 
  "https://gitlab.com/api/v4/bulk_imports"
```

This request will return an ID. Use this ID to monitor the status of the Direct Transfer at:

```
https://gitlab.com/import/bulk_imports/ID/history
```

## Step 6: Reaching Out for Assistance

If you continue to experience issues after following the steps above, reach out to the import team on Slack at `#g_manage_and_integrate` for further assistance.
