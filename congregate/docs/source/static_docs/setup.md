## Setup

### TL;DR Install

Copy the following code snippet to a file in the Congregate directory and run it

```bash
#!/bin/bash

# Install pip for different OSs

# mac os x
brew install pip

# debian/ubuntu
apt install python-pip

# rhel/centos
yum install python-pip

# Install with pip
pip install poetry

# If pip install poetry doesn't work
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python

source $HOME/.poetry/env
poetry --version

# install python dependencies
poetry install

# install NVM for Node Version Management
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.35.3/install.sh | bash
nvm install 11.13.0
nvm use 11.13.0

# install UI dependencies
npm install

# create congregate path
CONGREGATE_PATH=$(pwd)

# copy congregate script to a bin directory
cp congregate.sh /usr/local/bin/congregate

# Initialize additional congregate directories
congregate init

echo "export CONGREGATE_PATH=$CONGREGATE_PATH" >> ~/.bash_profile
```

Once all of the dependencies are installed, run `congregate configure` to set up the Congregate config.

### Config staging location

The only fully supported method for both group and project export / import is:

* **filesystem** - export, download and import data locally.

The following method is supported only for project export / import:

* **aws** - export and download data directly to an S3 bucket and import directly from the S3 bucket.
  * AWS (S3) user attributes are **not yet** available on the Group export / import API.

The following method may be supported in the future ([issue](https://gitlab.com/gitlab-com/customer-success/tools/congregate/issues/119)):

* **filesystem-aws** - export and download data locally, copy it to an S3 bucket for storage, then delete the data locally. Copy the data back from S3, import it and then delete the local data again.
  * This is used to help work with company policies like restricting presigned URLs or in case any of the source instances involved in the migration cannot connect to an S3 bucket while the destination instance can.

### Install & Use Poetry and Node (required for end-user and development setups)

```bash

# Install poetry with different OSs

# osx/Linux/bash on Windows Install Instructions
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python

# windows powershell Install Instructions
Invoke-WebRequest -Uri https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py -UseBasicParsing).Content | python

# Install with pip
pip install poetry

# Install dependencies from Pipfile
cd <path_to_congregate>
poetry install

# Start-up python virtualenv
cd <path_to_congregate>
poetry shell

# Install NVM for managing node versions
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.35.3/install.sh | bash
nvm install 11.13.0
nvm use 11.13.0

# Install ui dependencies
cd <path_to_congregate>
npm install
```

### Installing and configuring Congregate (end-user)

From **docker**:

1. Pull the docker image from the container registry
    * For official versioned releases, pull from registry.gitlab.com/gitlab-com/customer-success/tools/congregate
    * For rolling releases, pull from registry.gitlab.com/gitlab-com/customer-success/tools/congregate/master
2. Run the following command:

```bash
docker login registry.gitlab.com/gitlab-com/customer-success/tools/congregate -u <user name> -p <personal token>
docker run \
--name <name> \
-v /var/run/docker.sock:/var/run/docker.sock \ # expose docker socket as volume
-v <path_to_local_storage>:/opt/congregate/data \ # expose data directory as volume
-p 8000:8000 \ # expose UI port
-it registry.gitlab.com/gitlab-com/customer-success/tools/congregate:latest \
/bin/bash
./congregate.sh configure
./congregate.sh list
```

To resume the container:

```bash
docker start <container-id>
docker exec -it <container-id> /bin/bash
```

**N.B.** To bring up docker aliases and others run:

`. dev/bin/env`

From **tar.gz**:

1. Navigate to the project's *Repository -> Files* page
2. Download the latest tar.gz
3. Run the following commands:

```bash
tar -zxvf congregate-${version}.tar.gz
export CONGREGATE_PATH=<path_to_congregate>
cp congregate.sh /usr/local/bin
```

From **source**:

1. Clone this repo
2. Run the following commands:

```bash
cd <path_to_congregate>
export CONGREGATE_PATH=<path_to_congregate>
cp congregate.sh /usr/local/bin
```

#### Configuring

Before you start make sure to have a source and destination instance available and accessible from Congregate.

**N.B.** Congregate is currently only configurable to migrate from GitLab -> GitLab (either SaaS or self-managed).
Migrating from and to other external instances (BitBucket, GitHub, etc.) is currently not supported.

Using the `root` user account create a Personal Access Token or PAT (preferably create a separate user with Admin privileges) on both instances.
From the user profile's *Settings -> Access Tokens* enter a name and check `api` from *Scopes*. This may change once more granular rights are introduced for PATs as described [here](https://gitlab.com/groups/gitlab-org/-/epics/637).
Make sure to safely store the tokens before configuring.

As part of project migrations Congregate extends the Project export/import API by migrating registries (docker images).
Make sure to enable the **Container Registry** on both instances as you will need the hostnames during configuration.
Apart from the `/etc/gitlab/gitlab.rb` file you may lookup the hostname on an empty project's *Packages -> Container Registry* page.

Run the following commands to configure Congregate and retrieve info from the source instance:

```bash
congregate configure
congregate list
```

All secrets (PATs, S3 keys) are obfuscated in your `congregate.conf` configuration file.

With Congregate configured and projects, groups, and users retrieved, you should be ready to use the tool or test your changes.

**N.B.** Instead of exporting an environment variable within your shell session, you can also add `CONGREGATE_PATH` to `bash_profile` or an `init.d` script.
This is a bit more of a permanent solution than just exporting the variable within the session.