# Migrating data in an air gapped environment

## Source data export

Assuming a Congregate node on the source low-side network exists, you can trigger an export request by making the following cURL request:

```bash
curl --request POST \
  --url http://<congregate-source-node>:8000/api/airgap/export \
  --header 'Content-Type: application/json' \
  --data '{
    "host": "https://<source-gitlab-instance>",
    "token": "<project-access-token>",
    "pid": <project-id>
  }'
```

The project access token will need **Owner** privileges and **API** scope enabled.

This will create a job on the Congregate node to trigger an export. For the end user, this is all they have to do. Node Admins will need to wire up where the data is exported in Congregate to whatever mechanism is being used to move data up to the destination network.

## Destination data import

Importing to the destination network should be handled by the GitLab Admins on the destination. Assuming a Congregate node has been set up on the destination network, you can trigger an import request by making the following cURL request:

```bash
curl --request POST \
  --url https://<congregate-destination-node>:8000/api/airgap/import \
  --header 'Content-Type: multipart/form-data;' \
  --form host=https://<destination-gitlab-instance> \
  --form token=<personal-access-token> \
  --form gid=<gitlab-group-id> \
  --form 'file=@/path/to/exported/project'
```

**NOTE:** A personal access token is needed because [group access tokens cannot be used to import projects](https://docs.gitlab.com/ee/user/project/settings/import_export_troubleshooting.html#import-using-the-rest-api-fails-when-using-a-group-access-token)

### Automated bulk import example

This is a `bash` script example for migrating all project export files within a folder:

```bash
for f in /path/to/downloaded/project/exports/*; do if [[ "$f" == *_artifact.tar.gz ]]; then curl --request POST \
  --url https://localhost:8000/api/airgap/import \
  --header 'Content-Type: multipart/form-data;' \
  --form host=https://<destination-hostname> \
  --form token=<destination-token> \
  --form gid=<destination-group-id> \
  --form 'file=@$f’; fi; done
```

To follow the progress open the `flower` UI from the browser: `https://localhost:5555`.

**NOTE:** Make sure the number of files is even i.e. both the `_artifact.tar.gz` and `.tar.gz` files are present for each downloaded project export.
