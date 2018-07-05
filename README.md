# Congregate

Come together, right now

...over me

## Dependencies

- [jq](https://stedolan.github.io/jq/download/)
- [cURL](https://curl.haxx.se/download.html)
- [PipEnv](https://docs.pipenv.org/)

## Setup

### Install & Use PipEnv

```
pip install pipenv
# install depdencies from Pipfile
pipenv install
# start up python virtualenv
pipenv shell
```

### Installing jq

macOS

`brew install jq`

ubuntu/debian

`sudo apt-get install jq`

## Usage

`./congregate <command> <added-parameters>`

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

## Far Away Goal - UI integration

The UI integration will help provide all of the features of the CLI directly within a GitLab instance and leverage Meltano for metrics.