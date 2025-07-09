# Migrating data in an air gapped environment

Applicable **only** to GitLab -> GitLab migrations.

[TOC]

## Airgapped Migration Flow

![airgap-flow](/runbooks/uploads/airgapflow.png)

This is the process of moving GitLab data (Users/Groups/Projects) between the customer environment that is completely isolated from external networks (air-gapped environments) and destination GitLab instance. Congregate plays an important role in migrating the data.

Above is a generic flow diagram for an airgapped migration. Like you see in the flow diagram, there are two Congregate VMs:

1. VM1: Inside customer's network
2. VM2: Outside customer's network. This VM is GitLab GCP Hosted.

### Object Storage

There are two options:

1. Customer provides their own Object storage and allowlist our Congregate VM2 hosted outside their VPN
2. PS team uses GitLab owned AWS/GCP cloud storage. AWS storage is used mostly in migrations

### Migration Flow

Migration should be performed in the following sequence to ensure proper dependencies: user accounts, followed by groups, and then projects

#### Users migration

Verify that all users have been migrated to the destination by running the following command:

`congregate search-for-staged-users --table`

The `user_stats.csv` file provides comprehensive user details, including their migration status (found/not found) on the destination system. Use this information to:

1. Identify users that are missing from the destination
2. Migrate any remaining users
3. Verify all users are present before moving on to Groups and Projects migration

#### Groups/Projects migration

1. Congregate exporting the tar files of Groups/Projects from GitLab source
2. AWS → Upload the tar files
3. AWS → Download the tar files
4. Congregate import the tar files on GitLab destination

### Setting up Congregate for air-gapped migrations

Congregate's default configuration relies on the node running Congregate to be able to communicate with the source and destination instance during a migration run.
The two instances do not need to know of each other's existence because Congregate can act as the intermediary.

In an air-gapped environment, specifically where the source and destination instances are on completely different networks with no way to communicate, Congregate cannot act as the intermediary between the two instances. Instead, two separate Congregate nodes need to be set up.

### Pre-requisites

- A VM with a container runtime (docker, podman, rancher, etc) and docker-compose installed
- Access to the [congregate container registry](https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate/container_registry/2394823)
- Admin access on source and destination. Refer to [this document](/runbooks/migration-pre-and-post-requisites.md) to perform all pre-requisite tasks before migration.

### Setting up the Congregate nodes

- Refer to [this document](/runbooks/setting-up-direct-transfer-migrations.md) to setup Congregate on both the VMs
- If the VM is inside a VPN and does not support `docker-compose`, one can also use the [single node](/docs/full_setup.md#installing-and-configuring-congregate-end-user) method to install Congregate

### Example Configuration for source VM1

<details><summary>congregate.conf</summary>

```bash
[SOURCE]
src_hostname = https://gitlab.example.net
src_type = GitLab
src_access_token =
src_tier =

# Optional
src_parent_group_id =
src_parent_group_path =

[APP]
airgap = True
airgap_export = True

[EXPORT]
filesystem_path = /opt/congregate
```

</details>

### Example Configuration for destination VM2

<details><summary>congregate.conf</summary>

```bash
[SOURCE]
src_type = GitLab
src_tier =

[DESTINATION]
dstn_hostname = https://gitlab.example.com
dstn_access_token =
import_user_id =
username_suffix =
dstn_parent_group_id =
dstn_parent_group_path =
shared_runners_enabled =

[EXPORT]
filesystem_path = /opt/congregate

[USER]
keep_inactive_users = True
reset_pwd = False
force_rand_pwd = True

[APP]
airgap = True
airgap_import = True
mongo_host = mongo
redis_host = redis
processes =
```

</details>

**NOTE:** Configure empty fields based on [template](congregate.conf.template).

### Optional configurations

#### Certification issues

If you are using a self-signed certificate, you will either need to add the certificate to the VM or Docker image running congregate or add the following setting to the `[APP]` section of _/opt/congregate/data/congregate.conf_:

```bash
ssl_verify = False
```

If you are seeing [SSL error](#ssl-error) while connecting to the source URL, you might need to add SSL certs. Retrieve the required cert file in `.crt` format and follow below guide.

#### SSL Error

`(Caused by SSLError(SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self signed certificate in certificate chain (_ssl.c:1149)')))'`

##### To install cert provided on Congregate VM

```bash
mv customer.crt /usr/local/share/ca-certificates/
update-ca-certificates -f
REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
```

### GitLab features in scope

- [Group export items](https://docs.gitlab.com/user/project/settings/import_export/#group-items-that-are-exported)
- [Project export items](https://docs.gitlab.com/user/project/settings/import_export/#project-items-that-are-exported)
  - Additional project features handled by Congregate:
    - Environments
    - CI/CD Variables
    - Pipeline Schedule Variables

### Source data export

Assuming a Congregate node on the source low-side network exists, you can use the CLI to perform the following:

- List
- Stage
- Export groups
- Export projects w/ [additional features](#gitlab-features-in-scope) (separate `_artifact.tar.gz`)

Transfer the `/opt/congregate/data` folder to your import node before you move on to [the import phase](#destination-data-import).

#### Using the CLI on export

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

#### Using bare API to export projects

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

### Destination data import

Importing to the destination network should be handled by the GitLab Admins on the destination. Assuming a Congregate node has been set up on the destination network, make sure all the [source exported data](#source-data-export) is transferred. Only then can you perform the following actions:

- Create users
- Import groups w/o additional [Congregate supported features](/customer/gitlab-migration-features-matrix.md)
- Import projects w/ [additional features](#gitlab-features-in-scope)

#### Using the CLI on import

- Stage all users
  - E.g. `congregate stage-users . --commit`
- Migrate users
  - E.g. `congregate migrate --skip-group-export --skip-group-import --skip-project-export --skip-project-import`
- Stage groups in scope of migration wave
- Import staged groups
  - E.g. `congregate migrate --skip-users --skip-group-export --skip-project-export --skip-project-import`
  - Add `--commit` to execute
- Import projects by using [bare API](#automated-bulk-import-example)

#### Using bare API to import projects

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

##### Automated bulk import example

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

### Troubleshooting

#### Checking logs

There are multiple log files you can check for any errors or statuses. They should all be located in `/opt/congregate/data/logs`

- _congregate.log_: the overall application log of Congregate. This will show statuses of exports and imports running
- _audit.log_: any POST/PUT/DELETE requests will be logged here
- _gunicorn.log_: `stdout` of the `gunicorn` service go here
- _gunicorn_err.log_: `stderr` of the `gunicorn` service go here
- _celery.log_: `stdout` of the `celery` service will go here, which may include similar content to _congregate.log_
- _celery_err.log_: `stderr` of the `celery` service is logged here. This can show if celery fails to connect to `mongo` or `redis`
- _flower_err.log_: the output of the `flower` service. Everything appears to be logged to `stderr` with the `flower` service

#### Managing congregate services

There are three services managed by `supervisorctl`:

- **Gunicorn**: The web server for Congregate
- **Celery**: The job queue manager for Congregate
- **Flower**: The job queue monitor web app for Celery

You can check the **status** of them by running

```bash
supervisorctl status
```

and **restart** them by running

```bash
# restart all of them
supervisorctl restart all
# restart only gunicorn for example
supervisorctl restart congregate-gunicorn
```

or **stop** them all together by running

```bash
# stop all of them
supervisorctl stop all
# stop only gunicorn for example
supervisorctl stop congregate-gunicorn
```

#### Exports and imports taking over an hour

By default, Congregate will poll the source and destination to check the status of an ongoing export/import.
Larger GitLab projects may take longer than an hour to finish exporting or importing.
This timeout is configurable. To extend the timeout, add the following setting to the `[APP]` section of _/opt/congregate/data/congregate.conf_ (for both low side and high side nodes):

```bash
export_import_timeout = <number-of-seconds>
# for example, setting the timeout to 6 hours would be: 'export_import_timeout = 21600'
```
