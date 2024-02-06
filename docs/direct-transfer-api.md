# Migrating data via Direct Transfer

[Direct Transfer](https://docs.gitlab.com/ee/api/bulk_imports.html) is the new standard for importing GitLab data into another GitLab instance. Congregate can utilize Direct Transfer to handle a large portion of the import process. Once groups and projects have been imported to GitLab via Direct Transfer, Congregate will run its own post-migration tasks to import additional components of a GitLab project or group that is excluded from Direct Transfer.

This documentation covers setting up a Congregate instance to use Direct Transfer.

## Pre-requisites

- A VM with a container runtime (docker, podman, rancher, etc) and docker-compose installed
- Access to the [congregate container registry](https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate/container_registry/2394823)
- Ability to download MongoDB and Redis images from a container registry
- Direct transfer and GitLab export/import [enabled in the admin settings](https://docs.gitlab.com/ee/administration/settings/import_and_export_settings.html#configure-allowed-import-sources) on the source and destination instances

## Setting up the Congregate nodes

- Set up a VM with your container runtime of choice and docker-compose on the source and destination network
- On each VM, pull down [this docker-compose.yml](https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate/-/blob/master/docker/release/docker-compose.yml) file. This file will spin up a Congregate, MongoDB, and Redis container.
  - Congregate relies on MongoDB to store data during the export and import as well as track any export and import job statuses. Redis is used to act as the message broker for the export and import job requests
- Set an environment variable called `$CONGREGATE_DATA` to point to a location where you want to store any data from the container
- Create a `cache` directory in the same location where the docker-compose file will be run. This will be used for the redis cache
- In `$CONGREGATE_DATA`, edit or create the `congregate.conf` file to match the configurations below. Update any paths or URLs accordingly
- In `$CONGREGATE_DATA`, create a directory called `logs`
- Start up the docker-compose file in the background and open a shell in the congregate container:

```bash
docker-compose up -d
docker exec -it congregate /bin/bash
```

- Run the following commands in the `congregate` container:

```bash
congregate init
congregate validate-config
supervisorctl start all
```

## Example configuration for direct transfer migrations (when using the supplied docker-compose.yml file)

```bash
[SOURCE]
src_hostname = https://<gitlab-source>
src_access_token = <base64-encoded-token>
src_type = GitLab

[DESTINATION]
dstn_hostname = https://<gitlab-destination>
dstn_access_token = <base64-encoded-token>
import_user_id = <id-corresponding-to-the-owner-of-the-token>

[APP]
mongo_host = mongo
redis_host = redis
direct_transfer = true
```

If you are familiar with using file-based export/import for migrating data from
one GitLab instance to another, you will notice the `[EXPORT]` section is completely
omitted from this configuration.
