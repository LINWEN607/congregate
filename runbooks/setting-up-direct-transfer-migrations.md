# Migrating data via Direct Transfer - Setup

[Direct Transfer](https://docs.gitlab.com/ee/api/bulk_imports.html) is the new standard for importing GitLab data into another GitLab instance. Congregate can utilize Direct Transfer to handle a large portion of the import process. Once groups and projects have been imported to GitLab via Direct Transfer, Congregate will run its own post-migration tasks to import additional components of a GitLab project or group that is excluded from Direct Transfer.

This documentation covers setting up a Congregate instance to use Direct Transfer.

[[_TOC_]]

## Pre-requisites

- A VM with a container runtime (docker, podman, rancher, etc) and docker-compose installed
- Access to the [congregate container registry](https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate/container_registry/2394823)
- Ability to download MongoDB and Redis images from a container registry
- Direct transfer [enabled in the admin settings](https://docs.gitlab.com/ee/administration/settings/import_and_export_settings.html#configure-allowed-import-sources) on the source and destination instances

### 1. Install `docker` and `docker-compose` (if not already installed)

*Note: This generally requires root access*

Follow the official Docker installation guide for your operating system:

- [Install Docker](https://docs.docker.com/get-docker/)
- [Install Docker Compose](https://docs.docker.com/compose/install/)

### 2. Set Up Environment Variables

Ensure the `$CONGREGATE_DATA` environment variable is set and points to your data directory. For example:

```bash
export CONGREGATE_DATA=/root/congregate_work
```

Make sure the following directories exist:

```bash
mkdir -p $CONGREGATE_DATA/congregate-data/logs
mkdir -p $CONGREGATE_DATA/mongo-data
mkdir -p $CONGREGATE_DATA/redis-cache
touch $CONGREGATE_DATA/congregate-data/logs/gunicorn.log
touch $CONGREGATE_DATA/congregate-data/logs/gunicorn_err.log
touch $CONGREGATE_DATA/congregate-data/logs/celery.log
touch $CONGREGATE_DATA/congregate-data/logs/celery_err.log
touch $CONGREGATE_DATA/congregate-data/logs/flower.log
touch $CONGREGATE_DATA/congregate-data/logs/flower_err.log
```

Note: Depending on who you run as when creating these folders and files, you may need to additionally allow the application to update the conf and logs:

```bash
chmod a+wr --recursive $CONGREGATE_DATA
```

Create a `cache` directory in the same location where the docker-compose file will be run. This will be used for the Redis cache.

### 3. Create and Enable Swap

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

### 4. Start the Docker Services in Detached Mode

Navigate to the directory where the [docker-compose.yml](https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate/-/blob/master/docker/release/docker-compose.yml) file exists. In the local container with the suggested volume mounts, this will be in `/opt/congregate/docker/release/docker-compose.yml`:

Start the services in detached mode:

```bash
docker-compose up -d
```

### 5. Manual Permission Fix

After starting the containers, log into the `congregate` container as `root` to manually change the ownership of the `data` folder and the Docker socket to ensure `ps-user` has the necessary permissions.

```bash
docker exec -u root -it congregate /bin/bash
chown -R ps-user:ps-user /opt/congregate/data
chown root:ps-user /var/run/docker.sock
exit
```

This ensures the `ps-user` has proper permissions to access the Congregate container's `data` directory and Docker socket, avoiding issues during the initialization process.

### 6. Post-Initialization Steps

After ensuring the permissions are set, follow the initialization steps to:

1. initialize configuration file

    ```bash
    docker exec -it congregate /bin/bash
    congregate init
    ```

1. [configure Congregate](#example-configuration-for-direct-transfer-migrations-when-using-the-supplied-docker-composeyml-file)
1. validate configuration

    ```bash
    congregate validate-config
    ```

    **NOTE:** All secrets (PATs) must be obfuscated in your `congregate.conf` configuration file. Use `./congregate.sh obfuscate`.

1. start and validate `supervisorctl`

    ```bash
    supervisorctl start all
    supervisorctl status
    ```

#### Example (minimal) configuration for direct transfer migrations (when using the supplied docker-compose.yml file)

```bash
[SOURCE]
src_hostname = https://<gitlab-source>
src_access_token = <base64-encoded-token>
src_type = GitLab

# core (default), premium or ultimate
src_tier = <gitlab-license-tier>

# Optional
src_parent_group_id = <group-id>
src_parent_group_path = <full-group-path>

[DESTINATION]
dstn_hostname = https://<gitlab-destination>
dstn_access_token = <base64-encoded-token>
import_user_id = <id-corresponding-to-the-owner-of-the-token>

# Optional
dstn_parent_group_id = <group-id>
dstn_parent_group_path = <full-group-path>

[APP]
mongo_host = mongo
redis_host = redis
direct_transfer = true
```

**NOTE:** If you are familiar with using file-based export/import for migrating data from one GitLab instance to another, you will notice the `[EXPORT]` section is completely omitted from this configuration. For more (Optional) configuration items, e.g. source and destination parent group 👆, see [`congregate.conf` template](/congregate.conf.template).

### Troubleshooting Supervisorctl

#### Reboot supervisorctl

`supervisorctl` can give errors like `connection refused`.

Attempt to reboot `supervisord` from the container using the default config and try again:

```bash
sudo supervisord -c /etc/supervisor/conf.d/supervisord.conf
```

#### Restart docker-compose

If the UI is hanging i.e. still running expired processes best is to restart `docker-compose`.

**NOTE:** This will restart your containers and drop the job history and local (Git) changes.

1. In the `congregate` container run the following and exit:

    ```bash
    supervisorctl stop all
    ```

1. On the migration VM (outside of the container) run the following:

    ```bash
    export CONGREGATE_DATA=/root/congregate_work/data   # or custom path
    docker-compose down
    docker-compose up -d
    ```

1. Repeat [post-initialization steps](#6-post-initialization-steps).

#### Adjust concurrency (processes)

One may want to adjust the default (4) `celery` concurrency i.e. number of parallel processes/tasks handling the direct-transfer bulk import.

1. Update the `[APP]` section of your `congergate.conf` file to include the following setting:

```bash
processes = <num-of-processes>
```

The new configuration file should look something like:

```bash
[SOURCE]
src_hostname = https://<gitlab-source>
src_access_token = <base64-encoded-token>
src_type = GitLab

# Optional
src_parent_group_id = <group-id>
src_parent_group_path = <full-group-path>

[DESTINATION]
dstn_hostname = https://<gitlab-destination>
dstn_access_token = <base64-encoded-token>
import_user_id = <id-corresponding-to-the-owner-of-the-token>

# Optional
dstn_parent_group_id = <group-id>
dstn_parent_group_path = <full-group-path>

[APP]
mongo_host = mongo
redis_host = redis
direct_transfer = true
processes = <num-of-processes> # new entry added here
```

2. Once the configuration file has been updated, restart all services by running `supervisorctl restart all`
