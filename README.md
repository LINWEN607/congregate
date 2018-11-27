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
cd /path/to/congregate
pipenv install
# start up python virtualenv
cd /path/to/congregate
pipenv shell
# install ui dependencies
cd /path/to/congregate
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
```
Usage:
    congregate list
    congregate config
    congregate stage <projects>...
    congregate migrate
    congregate ui
    congregate import-projects
    congregate do_all
    congregate update-staged-user-info
    congregate update-new-users
    congregate add-users-to-parent-group
    congregate remove-blocked-users
    congregate lower-user-permissions
    congregate get-total-count
    congregate find-unimported-projects
    congregate stage-unimported-projects
    congregate remove-users-from-parent-group
    congregate migrate-variables-in-stage
    congregate add-all-mirrors
    congregate remove-all-mirrors
    congregate find-all-internal-projects
    congregate make-all-internal-groups-private
    congregate check-projects-visibility
    congregate -h | --help

Options:
    -h --help     Show this screen.

Commands:
    list                                List all projects of a child instance and save it to {CONGREGATE_PATH}/data/project_json.json
    config                              Configure congregate for migrating between two instances and save it to {CONGREGATE_PATH}/data/config.json
    stage                               Stage projects to {CONGREGATE_PATH}/data/stage.json,
                                        users to {CONGREGATE_PATH}/data/staged_users.json,
                                        groups to {CONGREGATE_PATH}/data/staged_groups.json.
                                        All projects can be staged with a '.' or 'all'.
    migrate                             mmence migration based on configuration and staged assets
    ui                                  Deploy UI to port 5000
    import-projects                     Kick off import of exported projects onto parent instance
    do_all                              Configure system, retrieve all projects, users, and groups, stage all information, and commence migration
    update-staged-user-info             Update staged user information after migrating only users
    update-new-users                    Update user IDs in staged groups and projects after migrating users
    add-users-to-parent-group           If a parent group is set, all users staged will be added to the parent group
    remove-blocked-users                Removes all blocked users from staged projects and groups
    lower-user-permissions              Sets all reporter users to guest users
    get-total-count                     Get total count of migrated projects. Used to compare exported projects to imported projects.
    find-unimported-projects            Returns a list of projects that failed import
    stage-unimported-projects           Stage unimported projects based on {CONGREGATE_PATH}/data/unimported_projects.txt
    remove-users-from-parent-group      Remove all users with at most reporter access from the parent group
    migrate-variables-in-stage          Migrate CI variables for staged projects
    add-all-mirrors                     Sets up project mirroring for staged projects
    remove-all-mirrors                  Remove all project mirrors for staged projects
    find-all-internal-projects          Finds all internal projects
    make-all-internal-groups-private    Makes all internal migrated groups private
    check-projects-visibility           Returns list of all migrated projects' visibility
```

#### Important Note

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