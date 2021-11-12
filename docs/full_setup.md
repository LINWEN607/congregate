# Installing and configuring Congregate (end-user)

## From docker

1. From local machine, login to Congregate VM using `ssh -L 8000:localhost:8000 <vm_alias_ip_or_hostname>` to expose the Congregate UI outside of the docker container.
1. From Congregate VM, login to container registry

    ```bash
    docker login registry.gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate -u <user name> -p <personal token>
    ```

1. Pull the docker image from the container registry
    * :white_check_mark: For official versioned releases, `docker pull registry.gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate:<version>` (or `:latest`)
    * :warning: For rolling releases, `docker pull registry.gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate:rolling-debian` (or `:rolling-centos`)
1. Create and run the Congregate docker container:

    ```bash
    docker run \
    --name <name> \
    -v /var/run/docker.sock:/var/run/docker.sock \ # expose docker socket as volume
    -v <path_to_local_data>:/opt/congregate/data \ # expose data directory as volume
    -v <path_to_local_downloads>:/opt/congregate/downloads \ # if migrating from GitLab expose downloads directory as volume
    -p 8000:8000 \ # expose UI port
    -it registry.gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate:<version> \
    /bin/bash
    ```

   * To `docker run` in the background use `-d=true` or just `-d` option
   * In addition, to reattach to a detached container, use `docker attach` command

      ```bash
      docker ps -a
      docker attach --name <image_name>   # OR docker attach <container_id>
      ```

   * Type *Ctrl+p* then *Ctrl+q* to go from interactive to daemon mode
   * To remove container when it exits add `--rm` option to `docker run`

1. Exit (*Ctrl+d*) the container (stops it)
1. To resume the container and keep it up:

    ```bash
    docker start <container-id>
    docker exec -it <container-id> /bin/bash   # OR -itd
    ```

**N.B.** To bring up docker and others aliases run `. dev/bin/env` in Congregate.

### Additional settings (for private networks behind proxy)

* For `docker run`:
  * `-e http_proxy="$http_proxy" -e https_proxy="$https_proxy" -e no_proxy="$no_proxy" -e HTTP_PROXY="$http_proxy" -e HTTPS_PROXY="$https_proxy"`
  * `-e REQUESTS_CA_BUNDLE="/etc/pki/tls/certs/ca-bundle.crt"`
  * `-v /etc/pki/ca-trust/source/anchors/:/etc/pki/ca-trust/source/anchors/`
  * `-v /etc/hosts:/etc/hosts`
* Run `update-ca-trust extract` in the docker container once started to load the certificates from `anchors` into `ca-bundle.crt`

## From tar.gz

1. Navigate to the project's *Repository -> Files* page
2. Download the latest tar.gz
3. Run the following commands:

```bash
tar -zxvf congregate-${version}.tar.gz
export CONGREGATE_PATH=<path_to_congregate>
cp congregate.sh /usr/local/bin
```

## From source

1. Clone this repo
2. Run the following commands:

```bash
cd <path_to_congregate>
export CONGREGATE_PATH=<path_to_congregate>
cp congregate.sh /usr/local/bin
```

## Configuring

Before you start make sure to have a source and destination instance(s) available and accessible from Congregate. To do this run a `curl -k <source-hostname>` and `curl -k <destination-hostname>` to make sure they are routable. You can leave off -k if SSL certs are configured correctly.

Using the `root` user account create a Personal Access Token or PAT (preferably create a separate user with Admin privileges) on both instances.
In Gitlab, from the user profile's *Settings -> Access Tokens* enter a name and check `api` from *Scopes*. *Note: This may change once more granular rights are introduced for PATs as described [here](https://gitlab.com/groups/gitlab-org/-/epics/637).*
Make sure to safely store the tokens before configuring.

> if you are configuring `data/congregate.conf` without using `congregate configure` make sure to base64 encode the tokens by using the `congregate obfuscate` utility. It will prompt you to paste the token in and output the encoded token. 

As part of project migrations, Congregate extends the Project export/import API by migrating registries (docker images).
Make sure to enable the **Container Registry** on both instances as you will need the hostnames during configuration.
Apart from the `/etc/gitlab/gitlab.rb` file you may lookup the hostname on an empty project's *Packages -> Container Registry* page.

Run the following commands to configure Congregate and retrieve info from the source instance:

```bash
congregate configure
congregate list
```

To enable Slack alerting via [Incoming Webhooks](https://api.slack.com/messaging/webhooks), configure the `slack_url`. This way the `ERROR` and `WARNING` logs will be also sent to a dedicated Slack channel.

All secrets (PATs, S3 keys) are obfuscated in your `congregate.conf` configuration file.

With Congregate configured and projects, groups, and users retrieved, you should be ready to use the tool or test your changes.

**N.B.** Instead of exporting an environment variable within your shell session, you can also add `CONGREGATE_PATH` to `bash_profile` or an `init.d` script. This is a bit more of a permanent solution than just exporting the variable within the session.

### Configure staging location

The only fully supported method for both group and project export / import is:

* **filesystem** - export, download and import data locally.

The following method is supported only for project export / import:

* **aws** - export and download project exports directly to an S3 bucket and import directly from the S3 bucket.
  * AWS (S3) user attributes are **not yet** available on the Group export / import API.

The following method may be supported in the future ([issue](https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate/issues/119)):

* **filesystem-aws** - export and download data locally, copy it to an S3 bucket for storage, then delete the data locally. Copy the data back from S3, import it and then delete the local data again.
  * This is used to help work with company policies like restricting presigned URLs or in case any of the source instances involved in the migration cannot connect to an S3 bucket while the destination instance can.
