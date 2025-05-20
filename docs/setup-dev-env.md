# Table of Contents

- [Setup a local development environment](#setup-a-local-development-environment)
- [Using Congregate Development Toolkit](#using-congregate-development-toolkit)

# Setup a local development environment

You can either work from [source code](#basic-environment-from-source), or work out of [Congregate Development Toolkit](#congregate-development-toolkit) docker containers. Start by git cloning [the Congregate repo](https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate) to a directory of your choice.

```bash
git clone git@gitlab.com:gitlab-org/professional-services-automation/tools/migration/congregate.git
```

Once you get the basic environment setup, you will need to add the testing and validation tools.

## Dependencies

These instructions assume you have a working python 3 environment and docker environment
* Python 3.8
* [AWS CLI](https://aws.amazon.com/cli/)
* [Poetry](https://python-poetry.org/)
* [Node v12.18.4](https://www.npmjs.com/)
* [MongoDB](https://www.mongodb.com/docs/manual/tutorial/install-mongodb-community-with-docker/)

:warning: This document assumes you have a working python 3.8.12 installed, you know how to clone a repo in terminal, and switch to its directory.  If you do not have a working python, you will need to take appropriate OS specific steps to install it, or consider using the docker container.

### Basic Environment from SOURCE

Basic Environment from source would be used when you need to work on file based migrations, or other tooling, but don't need to test DT or Air-Gapped itself.  No special volume mounts are required to edit the code base.  The following should install a basic environment that is capable of doing a migration

1. Install Python Poetry
   * <details><summary>For Mac users, using brew:</summary>

      1. `brew update`
      2. Upgrade to `python@3.8`: `brew upgrade python@3.8`
      3. Restart terminal or open separate tab (shell)
      4. `pip3 install poetry`
      5. `pip3 -V` (e.g. `pip 20.1.1 from /usr/local/lib/python3.8/site-packages/pip (python 3.8)`)
      6. `poetry -V` (e.g. `Poetry version 1.0.9`)
      7. `python -V` Currently congregate only works in Python 3. Your python needs to be `Python 3.8.12` or greater.
      8. In case of multiple poetry virtualenvs (`<HOME>/Library/Caches/pypoetry/virtualenvs/`), perform the following steps to set Python 3 as the active one:
         1. Set your Python to point (via `~/.bashrc` alias or symlink) to Python 3
         2. Run `poetry env use python3.8`
         3. Run `poetry install -v` (resolves the `pyproject.toml` dependencies, and installs the versions specified in the `poetry.lock` file)

         **NOTE:** By removing the `poetry.lock` file or running `poetry update` you are deviating from the default set versions of the dependencies. When in doubt add `--no-dev` (Do not install dev dependencies) and `--dry-run` (`poetry update` only) to avoid dev dependencies i.e. inspect new versions before updating to them.

   </details>

   * <details><summary>For Linux or Other users (untested on Windows):</summary>

      ```bash
      curl -sSL https://install.python-poetry.org | python3.8 - && \
      export PATH="/home/$USER/.local/bin:$PATH" && \
      poetry --version && \
      poetry install
      ```

      Alternatively, use a virtual environment manager (`pip`): `pip install poetry`

   </details>
   
1. Source the poetry environment: `source $HOME/.poetry/env`
1. Verify poetry works: `poetry --version`. If this doesn't work, add the following line to your appropriate rc file, usually `.zshrc`: \
`export PATH=$HOME/.poetry/bin:$PATH` and retry `poetry --version`
1. Install python dependencies `poetry install`
   * To update dependencies run `poetry update`
1. Setup Mongo (File based Migrations)
   1. `docker pull mongodb/mongodb-community-server:latest`
   1. `docker run --name mongodb -p 27017:27017 -d mongodb/mongodb-community-server:latest`
   1. Make sure the `congregate.conf` is configured correctly for a stand alone Mongo;

   ```ini
   ### Mongo DB configuration
   mongo_host = localhost
   mongo_port = 27017
      ```

### Congregate Development Toolkit

Use the CDT when you need to work on DT or Air-Gapped migrations.  You can either map a docker volume to work on the code base, or work on it inside the container

#### Prerequisites

Before you begin, ensure you have the following installed on your local machine:

- Docker: [Install Docker](https://docs.docker.com/get-docker/)
- Docker Compose: [Install Docker Compose](https://docs.docker.com/compose/install/)

#### Install
   * Mongo & Redis using the Congregate Development Toolkit (DT and Air-Gapped Migrations)
      1. Open a Terminal and Navigate to the `<CONGREGATE-DIR>/docker/dev/cdk` directory and create a `.env` file. Insert the following content in the `.env` file, changing path as appropriate:

         ```ini
            CONGREGATE_DATA=/path/to/congregate/data
            CONGREGATE_PATH=/path/to/congregate/root/folder
         ```
      1. Make sure the congregate.conf file uses the following configuration. You need to make sure you use service names (mongo and redis, respectively) as hostnames. This is allowing containers to communicate with each other by their service names.

         ```ini
         ### Mongo DB configuration
         mongo_host = mongo
         ### Redis configuration
         redis_host = redis
         ```
      1. Start the docker compose file

         ```bash
            docker compose up -d # The -d starts in the background
         ```

      1. Get inside the container, optionally, copy congregate script to a bin directory and start using congregate

         ```bash
         docker exec -it congregate_dev bash
         cd /opt/congregate
         cp congregate.sh /usr/local/bin/congregate
         congregate help
         congregate init
         ```

### Adding requirements for Testing

1. Install NVM for Node Version Management \
 `curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.35.3/install.sh | bash`
1. If you are using zsh (mac default) copy this into `.zshrc`.  If not, copy into `.bashrc`.  Both of these files are generally found at `~/` \
`export NVM_DIR="$HOME/.nvm"` \
`[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm` \
`[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion`
1. Source whatever filed you copied the lines into. i.e.; `source .zshrc`
1. Install nvm: `nvm install 12.18.4`
1. Use specific nvm version: `nvm use 12.18.4`
1. Install UI dependencies: `npm install`
1. Create congregate path: `CONGREGATE_PATH=$(pwd)`
1. Copy congregate script to a bin directory: `cp congregate.sh /usr/local/bin/congregate`
1. Initialize additional congregate directories \
`congregate init` \
`echo "export CONGREGATE_PATH=$CONGREGATE_PATH" >> ~/.bash_profile`

### Validation

If we made it this far without errors, we are done with the basic install for development! The next bash command will run the UT and verify your installation is working.  This command could be pulled from the [.gitlab-ci.yml](.gitlab-ci.yml) or the `pt` alias in [./dev/bin/env](dev/bin/env).

```bash
poetry run pytest -m 'unit_test' --cov-report html --cov-config=.coveragerc --cov=congregate congregate/tests/
```

Success looks like;
![SUCCESS](/img/ut_success.png)

**NOTE:** Warnings should not be ignored, as they may cause the remote unit test job to fail. To easily discover and allow warnings comment out the following line in `congregate/tests/pytest.ini`:

```python
filterwarnings = error
```

## Install & Use Poetry and Node

_Required for end-user and development setups._

```bash
# Install poetry with different OSs

   # From source - OSX/Linux/Bash on Windows Install Instructions
   curl -sSL https://install.python-poetry.org | python3.8 - && \
   export PATH="/home/$USER/.local/bin:$PATH" && \
   poetry --version && \
   poetry install

   # TODO: Windows PowerShell Install Instructions
   #Invoke-WebRequest -Uri https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py -UseBasicParsing).Content | python

   # Using pip
   pip install poetry

# Install dependencies from Pipfile
cd <path_to_congregate>
poetry install

# Start-up python virtualenv
cd <path_to_congregate>
poetry shell

# Install NVM for managing node versions
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.35.3/install.sh | bash
nvm install 12.18.4
nvm use 12.18.4

# Install ui dependencies
cd <path_to_congregate>/frontend
npm install
```

## Style guide

Congregate uses the `autopep8` tool to automatically format Python code conform the PEP 8 style guide.
If you are using VS Code as your IDE please enable `autopep8` with the following settings:

* *Python > Formatting: Autopep8 Args* - Add item `--max-line-length=79` (this length and setting applies to any other IDE you may be using)
* *Python > Formatting: Autopep8 Path* - `autopep8`
* *Python > Formatting: Provider* - `autopep8`
