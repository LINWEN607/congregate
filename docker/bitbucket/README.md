# BitBucket Development in Congregate

This directory contains a Dockerfile and docker-compose file for standing up a test BitBucket Server instance with some populated test data.

To spin all of this up, perform the following actions:

Retrieve the bitbucket evaluation license and root password from the project variables (congregate -> settings -> CI/CD -> variables).
If you do not have maintainer privileges, reach out to @leopardm or @pprokic for the license.

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

## Troubleshooting

### Docker image won't build

If you are having trouble building the docker image, you can replace `bitbucket-seed:latest` in `docker-compose.yml` with the bitbucket seed image stored in the container registry:

```
registry.gitlab.com/gitlab-com/customer-success/tools/congregate/bitbucket-seed:latest
```

This will require you to login to the GitLab container registry (`docker login registry.gitlab.com`) before spinning up the containers

### Stuck on Migrating Home Directory
If bitbucket is getting stuck on the "Migrating Home Directory" stage when you navigate to http://localhost:7990, then you might have a situation where the postgreSQL database is locked. To verify this, look at the postgreSQL container log to see `ERROR: function aurora_version() does not exist at character 8`. Accompanying this error in the bitbucket server container, you will see lots of

``` 
Waiting for BitBucket to start
Waiting for BitBucket to start
Waiting for BitBucket to start
```

Once you confirm this is your problem, ssh into the postgres container (can be done easily through docker desktop UI) and run the following command:
```bash
sql -c 'UPDATE DATABASECHANGELOGLOCK SET LOCKED=false, LOCKGRANTED=null, LO
CKEDBY=null where ID=1;' --dbname=bitbucket --username=db_user -W
```
where the Password is `db_password`

Once you do this, you should see the logs of the bitbucket container unstick.

Reference: https://community.atlassian.com/t5/Bitbucket-questions/starting-bitbucket-hangs-on-quot-migrating-home-directory-quot/qaq-p/785834
