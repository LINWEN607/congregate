# Migrating data via Direct Transfer - Setup

[Direct Transfer](https://docs.gitlab.com/ee/api/bulk_imports.html) is the new standard for importing GitLab data into another GitLab instance. Congregate can utilize Direct Transfer to handle a large portion of the import process. Once groups and projects have been imported to GitLab via Direct Transfer, Congregate will run its own post-migration tasks to import additional components of a GitLab project or group that is excluded from Direct Transfer.

This documentation covers setting up a Congregate instance to use Direct Transfer.

## Pre-requisites

- A VM with a container runtime (docker, podman, rancher, etc) and docker-compose installed
- Access to the [congregate container registry](https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate/container_registry/2394823)
- Ability to download MongoDB and Redis images from a container registry
- Direct transfer [enabled in the admin settings](https://docs.gitlab.com/ee/administration/settings/import_and_export_settings.html#configure-allowed-import-sources) on the source and destination instances

## Setting up the Congregate node

- Set up a VM with your container runtime of choice and docker-compose on the source and destination network.
- On the VM, pull down or create [this docker-compose.yml](https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate/-/blob/master/docker/release/docker-compose.yml) file into it's own directory. This file will spin up a Congregate, MongoDB, and Redis container.
  - Congregate relies on MongoDB to store data during the export and import as well as track any export and import job statuses. Redis is used to act as the message broker for the export and import job requests.

## 1. Install Docker and Docker Compose (if not already installed)

Follow the official Docker installation guide for your operating system:

- [Install Docker](https://docs.docker.com/get-docker/)
- [Install Docker Compose](https://docs.docker.com/compose/install/)

## 2. Set Up Environment Variables

Ensure the `$CONGREGATE_DATA` environment variable is set and points to your data directory. For example:

```bash
export CONGREGATE_DATA=/root/congregate_work/data
```

Make sure the following directories exist:

```bash
mkdir -p $CONGREGATE_DATA/congregate-data/logs
mkdir -p $CONGREGATE_DATA/mongo-data
mkdir -p $CONGREGATE_DATA/redis-cache
```

Create a `cache` directory in the same location where the docker-compose file will be run. This will be used for the Redis cache.

## 3. Create and Enable Swap

To ensure that Docker services have sufficient memory, create a 2GB swap file (recommended):

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
sudo swapon --show
```

To make the swap file persistent across reboots, add it to `/etc/fstab`:

```bash
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

## 4. Start the Docker Services in Detached Mode

Navigate to the directory where the docker-compose.yml file exists:

Start the services in detached mode:

```bash
docker-compose up -d
```

## 5. Manual Permission Fix

After starting the containers, log into the `congregate` container as `root` to manually change the ownership of the `data` folder and the Docker socket to ensure `ps-user` has the necessary permissions.

```bash
docker exec -u root -it congregate /bin/bash
chown -R ps-user:ps-user /opt/congregate/data
chown root:ps-user /var/run/docker.sock
exit
```

This ensures `ps-user` has proper permissions to access the data directory and Docker socket, avoiding issues during the initialization process.

## 6. Post-Initialization Steps

After ensuring the permissions are set, follow the initialization steps to initialize and validate the configuration:

```bash
congregate init
congregate validate-config
supervisorctl start all
```

## 7. Troubleshooting Supervisorctl

If the `supervisorctl` command gives any errors like `connection refused`, attempt to reboot `supervisord` with the default config and try again:

```bash
sudo supervisord -c /etc/supervisor/conf.d/supervisord.conf
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

If you are familiar with using file-based export/import for migrating data from one GitLab instance to another, you will notice the `[EXPORT]` section is completely omitted from this configuration.
