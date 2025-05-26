[TOC]

# Migrating data in an air gapped environment

Applicable **only** to GitLab -> GitLab migrations.

## GitLab features in scope

- [Group export items](https://docs.gitlab.com/user/project/settings/import_export/#group-items-that-are-exported)
- [Project export items](https://docs.gitlab.com/user/project/settings/import_export/#project-items-that-are-exported)
  - Additional project features handled by Congregate:
    - Environments
    - CI/CD Variables
    - Pipeline Schedule Variables
    - Merge Request Approvals

## Source data export

Assuming a Congregate node on the source low-side network exists, you can use the CLI to perform the following:

- List
- Stage
- Export groups
- Export projects w/ [additional features](#gitlab-features-in-scope) (separate `_artifact.tar.gz`)

Transfer the `/opt/congregate/data` folder to your import node before you move on to [the import phase](#destination-data-import).

### Using the CLI on export

- Stage all users
  - E.g. `congregate stage-users . --commit`
- Set `public_email` on source for all users, before exporting groups and projects
  - E.g. `congregate set-staged-users-public-email --commit`
- Stage groups and projects in scope of migration wave
- Export staged groups and projects
  - E.g. `congregate migrate --skip-users --skip-group-import --skip-project-import`
  - Add `--commit` to execute
  - Add `--retain-contributors` to preserve project contributions from former members

**NOTE:** Group export only triggers the [GitLab group export endpoint](https://docs.gitlab.com/api/group_import_export/#schedule-new-export), w/o additional [Congregate supported features](/customer/gitlab-migration-features-matrix.md).

### Using bare API to export projects

Make the following cURL request:

```bash
curl --request POST \
  --url http://localhost:8000/api/airgap/export \
  --header 'Content-Type: application/json' \
  --data '{
    "host": "https://<source-hostname>",
    "token": "<source-access-token>",
    "pid": <source-project-id>
  }'
```

The source access token requires **Owner** privileges and `api` scope. For convenience we recommend using a **personal** access token.

This will create a job on the Congregate node to trigger an export. For the end user, this is all they have to do. Node Admins will need to wire up where the data is exported in Congregate to whatever mechanism is being used to move data up to the destination network.

## Destination data import

Importing to the destination network should be handled by the GitLab Admins on the destination. Assuming a Congregate node has been set up on the destination network, make sure all the [source exported data](#source-data-export) is transferred. Only then can you perform the following actions:

- Create users
- Import groups w/o additional [Congregate supported features](/customer/gitlab-migration-features-matrix.md)
- Import projects w/ [additional features](#gitlab-features-in-scope)

### Using the CLI on import

- Stage all users
  - E.g. `congregate stage-users . --commit`
- Migrate users
  - E.g. `congregate migrate --skip-group-export --skip-group-import --skip-project-export --skip-project-import`
- Stage groups in scope of migration wave
- Import staged groups
  - E.g. `congregate migrate --skip-users --skip-group-export --skip-project-export --skip-project-import`
  - Add `--commit` to execute
- Import projects by using [bare API](#automated-bulk-import-example)

### Using bare API to import projects

Make the following cURL request:

```bash
curl --request POST \
  --url http://localhost:8000/api/airgap/import \
  --header 'Content-Type: multipart/form-data;' \
  --form host=https://<destination-hostname> \
  --form token=<destination-access-token> \
  --form gid=<destination-group-id> \
  --form 'file=@/path/to/exported/project'
```

**NOTE:** A personal access token is needed because [group access tokens cannot be used to import projects](https://docs.gitlab.com/ee/user/project/settings/import_export_troubleshooting.html#import-using-the-rest-api-fails-when-using-a-group-access-token)

#### Automated bulk import example

- Make sure all project exports and their `_artifact.tar.gz` files are in the *downloads* folder w/ `ps-user:ps-user` permissions
- Example `bash` script to migrate all project export files within a folder:

```bash
for f in /path/to/downloaded/project/exports/*; do if [[ "$f" == *_artifact.tar.gz ]]; then curl --request POST \
  --url http://localhost:8000/api/airgap/import \
  --header 'Content-Type: multipart/form-data;' \
  --form host=https://<destination-hostname> \
  --form token=<destination-access-token> \
  --form gid=<destination-group-id> \
  --form "file=@$f"; fi; done
```

To follow the progress open the `flower` UI from the browser: `https://localhost:5555`.
