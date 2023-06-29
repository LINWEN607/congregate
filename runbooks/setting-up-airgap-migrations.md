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
- In `$CONGREGATE_DATA`, create a directory called `logs`
- Run the following commands in the container

```bash
congregate init
supervisorctl start all
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

## Troubleshooting

### Checking logs

There are multiple log files you can check for any errors or statuses. They should all be located in `/opt/congregate/data/logs`

- congregate.log: the overall application log of congregate. This will show statuses of exports and imports running
- audit.log: any POST/PUT/DELETE requests will be logged here
- gunicorn.log: stdout of the gunicorn service go here
- gunicorn_err.log: stderr of the gunicorn service go here
- celery.log: stdout of the celery service will go here, which may include similar content to congregate.log
- celery_err.log: stderr of the celery service is logged here. This can show if celery fails to connect to mongo or redis
- flower_err.log: the output of the flower service. Everything appears to be logged to stderr with the flower service

### Managing congregate services

There are three services managed by supervisorctl:

- Gunicorn: The web server for Congregate
- Celery: The job queue manager for Congregate
- Flower: The job queue monitor web app for Celery

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
