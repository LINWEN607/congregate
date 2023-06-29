# Migrating data in an air gapped environment

## Source data export

Assuming a Congregate node on the source low-side network exists, you can trigger an export request by making the following cURL request:

```bash
curl --request POST \
  --url http://<congregate-source-node>:8000/airgap/export \
  --header 'Content-Type: application/json' \
  --data '{
	"host": "https://<source-gitlab-instance>",
	"token": "<project-access-token>",
	"pid": <project-id>
}'
```

This will create a job on the congregate node to trigger an export. For the end user, this is all they have to do. Admins will need to wire up where the data is exported in Congregate to whatever mechanism is being used to move data up to the destination network.

## Destination data import

Importing to the destination network should be handled by the GitLab admins on the destination. Assuming a Congregate node has been set up on the destination network, you can trigger an import request by making the following cURL request:

```bash
curl --request POST \
  --url https://<congregate-destination-node>:8000/airgap/import \
  --header 'Content-Type: multipart/form-data;' \
  --form host=https://<destination-gitlab-instance> \
  --form token=<personal-access-token> \
  --form gid=<gitlab-group-id> \
  --form 'file=@/path/to/exported/project'
```

A personal access token is needed because [group access tokens cannot be used to import projects](https://docs.gitlab.com/ee/user/project/settings/import_export_troubleshooting.html#import-using-the-rest-api-fails-when-using-a-group-access-token)