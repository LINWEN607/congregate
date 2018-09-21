# Congregate

Come together, right now

...over me

## Dependencies

- Python 2.7
- [AWS CLI](https://aws.amazon.com/cli/)
- [PipEnv](https://docs.pipenv.org/)

## Setup

### Installing Congregate

1. Navigate to the CI/CD section of this project
2. Download the latest tar.gz of congregate
3. Run the following commands:

```bash
tar -zxvf congregate-${version}.tar.gz
export CONGREGATE_PATH=/path/to/congregate
cp congregate /usr/local/bin
```

Note: Instead of exporting an environment variable within your shell session, you can also add `CONGREGATE_PATH` to `bash_profile` or an init.d script. This is a bit more of a permanent solution than just exporting the variable within the session. 

### Install & Use PipEnv

```bash
pip install pipenv
# install depdencies from Pipfile
pipenv install
# start up python virtualenv
pipenv shell
```

## Usage

`congregate <command> <added-parameters>`

- `config`: configure parameters like instance hosts, tokens, storage locations
- `list`: List all available projects
- `stage <project-id or project name>`: Stage projects to be migrated
- `migrate`: Queue migration
- `retrieve-groups`: Retrieve groups from child instance. This is bundled into `list`
- `retrieve-users`: Retrieve users from child instance. This is bundled into `list`
- `do_all`: Performs configuration, project staging, and migration

## Major Goal - CLI Tool

Assist with migrating contents of multiple GitLab instances into a single (monolithic?) GitLab instance.

This tool covers the following processes:
- Define instances that need to be migrated
- Export the projects of those instances to a storage location of your choice (S3, GCP, bare metal, etc)
- Import those projects to the parent GitLab instance
- Provide logs to document and monitor the process

## Far Away Goal - Native UI integration (Since congregate has a basic UI)

The UI integration will help provide all of the features of the CLI directly within a GitLab instance and leverage Meltano for metrics.