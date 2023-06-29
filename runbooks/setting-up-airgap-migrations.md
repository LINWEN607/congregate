# Setting up Congregate for air-gapped migrations

Congregate's default configuration relies on the node running Congregate to be able to communicate with the source and destination instance during a migration run.
The two instances do not need to know of each other's existence because Congregate can act as the intermediary.

In an air-gapped environment, specifically where the source and destination instances are on completely different networks with no way to communicate, Congregate cannot act as the intermediary between the two instances. Instead, two separate Congregate nodes need to be set up.

## Pre-requisites

- A VM with a container runtime (docker, podman, rancher, etc) and docker-compose installed
- Access to the [congregate container registry](https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate/container_registry/2394823)
- Ability to download MongoDB and Redis images

## Setting up the Congregate nodes

- Set up a VM with your container runtime of choice and docker-compose on the source and destination network
- On each VM, pull down [this docker-compose.yml](https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate/-/blob/master/docker/release/docker-compose.yml) file. This file will spin up a Congregate, MongoDB, and Redis container.
  - Congregate relies on MongoDB to store data during the export and import as well as track any export and import job statuses. Redis is used to act as the message broker for the export and import job requests
- Set an environment variable called `$CONGREGATE_DATA` to point to a location where you want to store any data from the container
- Create a `cache` directory in the same location where the docker-compose file will be run. This will be used for the redis cache
- Start up the docker-compose file
- In `$CONGREGATE_DATA`, edit or create the `congregate.conf` file to match the configurations below. Update any paths or URLs accordingly
- Run the following commands in the container

```bash
congregate ui &
cd /opt/congregate && poetry run celery -A congregate.ui.wsgi.celery_app worker &
cd /opt/congregate && poetry run celery -A congregate.ui.wsgi.celery_app flower --port=5566 &
```

- Finally on the destination GitLab instance, create a user dedicated to migrating the data. This user needs to exist because we cannot use a [group access token to import a project](https://docs.gitlab.com/ee/user/project/settings/import_export_troubleshooting.html#import-using-the-rest-api-fails-when-using-a-group-access-token), so we will need to use a personal access token to handle those requests

## Configuration for source low-side environment

```bash
[EXPORT]
location = filesystem
filesystem_path = /path/to/docker/data/mount

[APP]
airgap = True
airgap_export = True
mongo_host = mongo
redis_host = redis
```

## Configuration for destination high-side environment

```bash
[DESTINATION]
dstn_hostname = https://gitlab.example.com

[EXPORT]
location = filesystem
filesystem_path = /path/to/docker/data/mount

[APP]
airgap = True
airgap_import = True
mongo_host = localhost
```

## Optional configurations

### Certification issues

If you are using a self-signed certificate, you will either need to add the certificate to the VM or Docker image running congregate or add the following setting to the `[APP]` section of `congregate.conf`:

```bash
ssl_verify = False
```

### Exports and imports taking over an hour

By default, Congregate will poll the source and destination to check the status of an ongoing export/import.
Larger GitLab projects may take longer than an hour to finish exporting or importing.
This timeout is configurable. To extend the timeout, add the following setting to the `[APP]` section of `congregate.conf`:

```bash
export_import_timeout = <number-of-seconds>
# for example, setting the timeout to 6 hours
export_import_timeout = 21600
```
