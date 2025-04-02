# BitBucket Development in Congregate

This directory contains a Dockerfile and docker-compose file for standing up a test BitBucket Server instance with some populated test data.

To spin all of this up, perform the following actions:

Retrieve the bitbucket evaluation license and root password from the project variables (congregate -> settings -> CI/CD -> variables).
If you do not have maintainer privileges, reach out to @gitlab-org/professional-services-automation/tools/migration for the license.

## Save the bitbucket license and bitbucket as environment variables

```bash
export BITBUCKET_LICENSE=<bitbucket-license>
export BITBUCKET_PASSWORD=<bitbucket-password>
```

You can also add these lines to a shell's rc file (~/.bashrc, ~/.zshrc, etc.) so you don't have to repeatedly export them, but you only need these values for the initial docker build.

## Build the docker image

```bash
cp $CONGREGATE_PATH/docker/bitbucket/Dockerfile $CONGREGATE_PATH
docker build -t bitbucket-seed . --build-arg BITBUCKET_LICENSE=$BITBUCKET_LICENSE --build-arg BITBUCKET_PASSWORD=$BITBUCKET_PASSWORD
```

## Spin up the docker compose file

```bash
# In a separate terminal
cd $CONGREGATE_PATH/docker/bitbucket
docker-compose up -d
# You can take out the `-d` if you want to see all the logs while the containers are running
```

This will take around 10 minutes for the first time to get the service up and all the data populated. If you aren't running docker-compose in the background (with a `-d` flag) you can watch the logs as BitBucket, Postgres, and the seed data is all spun up and populated.

Once the instance is up, navigate to localhost:7990 to see the BitBucket instance running.

To login use `admin` as username and the previously mentioned password. For more details see ***congregate/docker/butbucket/docker-compose.yml***.

### Spin up the migration test infrastructure with docker compose

```bash
# In a separate terminal
cd $CONGREGATE_PATH/docker/bitbucket
docker-compose -f  migration-bb-to-gitlab.yaml up -d
# You can take out the `-d` if you want to see all the logs while the containers are running
```

The docker-compose file `migration-bb-to-gitlab.yaml` will create 3 services: `gitlab-web`, `bitbucket`, and `congregate` and two networks. One network is for bitbucket and the other is for gitlab. The gitlab-web and congregate services will be on both networks. Congregate needs to communicate directly to the `bitbucket` and `gitlab-web` services for import and export functionality and therefore the `congregate` service must be on both networks. The `gitlab-web` service requires both networks to allow direct gitlab to bitbucket connections for streaming projects (as required by [gitlab's bitbucket import tool](https://docs.gitlab.com/ee/api/import.html#import-repository-from-bitbucket-server)).

All of the same set up times and dependency specifications mentioned above for creating bitbucket infrastructure apply to the `migration-bb-to-gitlab.yaml` infrastructure.

Once the services are started you may use congregate by exec'ing into the `congregate` container service with the command: `docker-compose -f migration-bb-to-gitlab.yaml exec congregate bash`. This will create a terminal for you in the congregate container service. Once you recieve the shell prompt you can configure congregate to migrate from the bitbucket service to the gitlab service using standard congregate functionality.

An example congregate config file can be seen below:

```ini
[DESTINATION]
dstn_hostname = http://gitlab-web # The service name for gitlab created by docker-compose
dstn_access_token = <gitlab token here>
import_user_id = 1
shared_runners_enabled = True
max_import_retries = 3
username_suffix = 
mirror_username = 
max_asset_expiration_time = 24

[SOURCE]
src_type = Bitbucket Server
src_username = admin
src_hostname = http://bitbucket:7990 # The service name for bitbucket created by docker-compose
src_access_token = <bitbucket token here>

[USER]
keep_inactive_users = False
reset_pwd = True
force_rand_pwd = False

[APP]
export_import_status_check_time = 10
ui_port = 8000
```

## Troubleshooting

### Docker image won't build

If you are having trouble building the docker image, you can replace `bitbucket-seed:latest` in `docker-compose.yml` with the bitbucket seed image stored in the container registry:

`registry.gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate/bitbucket-seed:latest`

This will require you to login to the GitLab container registry (`docker login registry.gitlab.com`) before spinning up the containers

### Stuck on Migrating Home Directory

If bitbucket is getting stuck on the "Migrating Home Directory" stage when you navigate to `http://localhost:7990`, then you might have a situation where the postgreSQL database is locked. To verify this, look at the postgreSQL container log to see `ERROR: function aurora_version() does not exist at character 8`. Accompanying this error in the bitbucket server container, you will see lots of

```bash
Waiting for BitBucket to start
Waiting for BitBucket to start
Waiting for BitBucket to start
```

Once you confirm this is your problem, ssh into the postgres container and run the following command:

```bash
sql -c 'UPDATE DATABASECHANGELOGLOCK SET LOCKED=false, LOCKGRANTED=null, LO
CKEDBY=null where ID=1;' --dbname=bitbucket --username=db_user -W
```

where the Password is `db_password`

Once you do this, you should see the logs of the bitbucket container unstick. [Reference](https://community.atlassian.com/t5/Bitbucket-questions/starting-bitbucket-hangs-on-quot-migrating-home-directory-quot/qaq-p/785834)
