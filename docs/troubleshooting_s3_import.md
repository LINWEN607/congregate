
# Troubleshooting File-Based Import Failures and Switching to Direct Transfer

When dealing with GitLab file-based imports, particularly those using [S3](https://docs.gitlab.com/ee/api/project_import_export.html#import-a-file-from-aws-s3), you might encounter prolonged delays or import failures. This troubleshooting guide walks through diagnosing such issues and switching to Direct Transfer to resolve them.

## Potential Errors

- {"message":"Limit reached You cannot create projects in your personal namespace. Contact your GitLab administrator."}

This usually occurs when you've entered `data` for the curl request improperly. The example can be confusing as it seems to conflict with nomenclature from other import sources. The proper form example is below:

```bash
curl --request POST \
  --url "https://gitlab.com/api/v4/projects/remote-import-s3" \
  --header "PRIVATE-TOKEN: admin_token" \
  --header 'Content-Type: application/json' \
  --data '{
  "name": "Project Display Name",
  "path": "parent-group-piece-of-url",
  "region": "us-east-2",
  "bucket_name": "source-bucket",
  "file_key": "my-export.tar.gz",
  "access_key_id": "secretID",
  "secret_access_key": "Secret Password",
  "namespace": "id-of-parent-group"
}'
```

`path` in particular is confusing. It should just be the URL piece of the parent group. So, in `https://gitlab.com/gitlab-org/gitlab` the `gitlab-org` piece. Namespace should be the ID of that parent group.

## Step 1: Diagnosing the Import with Kibana

If a file-based import is taking longer than expected, diagnose the issue using available logs. Start by checking the API endpoint `/api/v4/projects/:ID/import` for the project to locate the correlation ID.

This endpoint provides the correlation ID, which can then be used in Kibana to search for logs. To search in Kibana, target `pubsub-sidekiq-inf-gprd*` using the following query:

```txt
json.class: "RepositoryImportWorker" AND json.correlation_id.keyword: "<Correlation ID from API>"
```

### Step 2: Finding Errors Using the `jid`

After running the query, you will retrieve a `json.jid`. Use this `jid` to search for error messages with the following query:

```txt
json.message: "<json.jid we found>"
```

Review the error messages for clues. If you find that the import worker failed due to interruptions, consider moving to Direct Transfer.

## Step 3: Switching to Direct Transfer

If the import worker fails or the job is taking too long, switch to Direct Transfer, which is less prone to interruptions.

### Step 4: Enabling Direct Transfer

Once Direct Transfer is enabled, verify that it is active on both the source and destination instances. The GitLab.com SaaS instance is usually pre-configured, but you may need to enable Direct Transfer on the source instance manually. After enabling and saving changes, you may experience a brief delay before the API call becomes functional.

If you encounter an error indicating that Direct Transfer is not enabled on both instances, wait a few moments and retry the API call until you receive a different error message.

## Step 5: Initiating Direct Transfer

Once Direct Transfer is enabled, trigger the [bulk import API endpoint](https://docs.gitlab.com/api/bulk_imports/#start-a-new-group-or-project-migration), e.g.

```bash
curl --request POST \
  --url "https://destination-gitlab-instance.example.com/api/v4/bulk_imports" \
  --header "PRIVATE-TOKEN: <your_access_token_for_destination_gitlab_instance>" \
  --header "Content-Type: application/json" \
  --data '{
    "configuration": {
      "url": "https://source-gitlab-instance.example.com",
      "access_token": "<your_access_token_for_source_gitlab_instance>"
    },
    "entities": [
      {
        "source_full_path": "source/full/path",
        "source_type": "project_entity",
        "destination_slug": "destination_slug",
        "destination_namespace": "destination/namespace/path"
      }
    ]
  }'
```

This request will return an ID, e.g.

```bash
{
  "id": 1,
  "status": "created",
  "source_type": "gitlab",
  "source_url": "https://gitlab.example.com",
  "created_at": "2021-06-18T09:45:55.358Z",
  "updated_at": "2021-06-18T09:46:27.003Z",
  "has_failures": false
}
```

Use this ID (1) to [monitor the status of the bulk import](https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate/-/snippets/4818709).

To access the entire bulk import history of the import user on destination, go to https://destination-gitlab-instance.example.com/import/bulk_imports/history.

## Step 6: Reaching Out for Assistance

If you continue to experience issues after following the steps above, reach out to the import team on Slack at `#g_manage_and_integrate` for further assistance.
