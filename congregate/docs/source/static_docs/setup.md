## Setup

### TL;DR Install

Copy the following code snippet to a file in the congregate directory and run it

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

source $HOME/.poetry/env
poetry --version

# install python dependencies
poetry install

# install UI dependencies
poetry run dnd install

# create congregate path
CONGREGATE_PATH=$(pwd)

# copy congregate script to a bin directory
cp congregate.sh /usr/local/bin

echo "export CONGREGATE_PATH=$CONGREGATE_PATH" >> ~/.bash_profile

```

Once all of the dependencies are installed, run `congregate config` to set up the congregate config.

There are currently *three* different methods for migrating projects (groups and users are all through the API):

* **filesystem** - download all projects locally and import them locally.
* **filesystem-aws** - download all projects locally, copy the exports to an S3 bucket for storage, then delete the project locally. Copy the files back from S3, import the file, then delete the local file again.
* **aws** - export all projects directly to an S3 bucket and import directly from the S3 bucket.

`filesystem-aws` is used to help work with company policies like restricting presigned URLs or in case any of the source instances involved in the migration cannot connect to an S3 bucket while the destination instance can.

**NOTE:** The hybrid (`filesystem-aws`) method is currently NOT supported ([issue](https://gitlab.com/gitlab-com/customer-success/tools/congregate/issues/119)).

### Install & Use Poetry (required for end-user and development setups)

```bash
# Install poetry with different OSs

# osx/Linux/bash on Windows Install Instructions
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python

# windows powershell Install Instructions
Invoke-WebRequest -Uri https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py -UseBasicParsing).Content | python

# Install with pip
pip install poetry

# install dependencies from Pipfile
cd /path/to/congregate
poetry install

# start-up python virtualenv
cd /path/to/congregate
poetry shell

# install ui dependencies
cd /path/to/congregate
poetry run dnd install
```

### Installing Congregate (end-user)

From **docker**:

1. Pull the docker image from the container registry
2. Run the following command:

```bash
docker login registry.gitlab.com/gitlab-com/customer-success/tools/congregate:latest -u <user name> -p <personal token>
docker run --name congregate -p 8000:8000 -it registry.gitlab.com/gitlab-com/customer-success/tools/congregate:latest /bin/bash
congregate config
congregate list
```

To resume the container:

```bash
docker start <container-id>
docker exec -it <container-id> /bin/bash
```

From **tar.gz**:

1. Navigate to the CI/CD section of this project
2. Download the latest tar.gz of congregate
3. Run the following commands:

```bash
tar -zxvf congregate-${version}.tar.gz
export CONGREGATE_PATH=/path/to/congregate
cp congregate /usr/local/bin
```

From **source**:

1. Clone this repo
2. Run the following commands:

```bash
cd /path/to/congregate
export CONGREGATE_PATH=/path/to/congregate
cp congregate /usr/local/bin
```

Run the following commands to configure congregate and retrieve info from the source instance:

```bash
congregate config
congregate list
```

With congregate configured and projects, groups, and users retrieved, you should be ready to use the tool or test your changes.

Note: Instead of exporting an environment variable within your shell session, you can also add `CONGREGATE_PATH` to `bash_profile` or an init.d script. This is a bit more of a permanent solution than just exporting the variable within the session.
