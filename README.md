# Congregate

Come together, right now

...over me

## Dependencies

- Python 2.7
- [AWS CLI](https://aws.amazon.com/cli/)
- [PipEnv](https://docs.pipenv.org/)

## Setup

### Install & Use PipEnv (required for end-user and development setups)

```bash
pip install pipenv
# install depdencies from Pipfile
pipenv install
# start up python virtualenv
pipenv shell
# install ui dependencies
pipenv run dnd install
```

### Installing Congregate (end-user)

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

Run the following commands to configure congregate and retrieve info from the child instance:

```bash
congregate config
congregate list
```

With congregate configured and projects, groups, and users retrieved, you should be ready to use the tool or test your changes.

Note: Instead of exporting an environment variable within your shell session, you can also add `CONGREGATE_PATH` to `bash_profile` or an init.d script. This is a bit more of a permanent solution than just exporting the variable within the session. 

### Usage

`congregate <command> <added-parameters>`

- `config`: configure parameters like instance hosts, tokens, storage locations
- `list`: List all available projects
- `stage <project-id or project name>`: Stage projects to be migrated
- `migrate`: Queue migration
- `retrieve-groups`: Retrieve groups from child instance. This is bundled into `list`
- `retrieve-users`: Retrieve users from child instance. This is bundled into `list`
- `do_all`: Performs configuration, project staging, and migration
- `ui`: Deploys UI to localhost:5000

**Important Note**

The GitLab import/export API versions need to match between instances. [This documentation](https://docs.gitlab.com/ee/user/project/settings/import_export.html) shows which versions of the API exist in each version of GitLab

### Development Environment Setup

Once congregate is installed

**Live reloading for UI development and backend development without a debugger**

You will need to turn on debugging in the flask app to see a mostly live reload of the UI. Create the following environment variable before deploying the UI

```bash
export FLASK_DEBUG=1
```

For the UI, you will still need to save the file in your editor and refresh the page, but it's better than restarting flask every time. The app will live reload every time a .py file is changed and saved.

**Configuring VS Code for Debugging**

Refer to [this how-to](https://code.visualstudio.com/docs/python/debugging) for setting up the base debugging settings for a python app in VS Code. Then replace the default flask configuration for this:

```json

{
    "name": "Python: Flask (0.11.x or later)",
    "type": "python",
    "request": "launch",
    "module": "flask",
    "env": {
        "PYTHONPATH": "${workspaceRoot}",
        "CONGREGATE_PATH": "/path/to/congregate",
        "FLASK_APP": "${CONGREGATE_PATH}/ui"
    },
    "args": [
        "run",
        "--no-debugger",
        "--no-reload"
    ]
}

```

To reload the app in debugging mode, you will need to click the `refresh` icon in VS code. Currently VS code doesn't support live reloading flask apps on save.

## Major Goal - CLI Tool

Assist with migrating contents of multiple GitLab instances into a single (monolithic?) GitLab instance.

This tool covers the following processes:
- Define instances that need to be migrated
- Export the projects of those instances to a storage location of your choice (S3, GCP, bare metal, etc)
- Import those projects to the parent GitLab instance
- Provide logs to document and monitor the process

## Far Away Goal - Native UI integration (Since congregate has a basic UI)

The UI integration will help provide all of the features of the CLI directly within a GitLab instance and leverage Meltano for metrics.