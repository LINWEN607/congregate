* TODO: Add build badge for at least master
* TODO: Add coverage report link from htmlcov

# Congregate

[TOC]

## About

* Congregate is a Professional Services utility for migrating one or more GitLab instances into another, single GitLab instance.
* Users are migrated using individual API endpoints.
* Congregate leverages both the [Project](https://docs.gitlab.com/ee/api/project_import_export.html) and [Group](https://docs.gitlab.com/ee/api/group_import_export.html) export / import API to migrate projects and groups.
* Missing project and group export / import features are migrated using individual API endpoints.

```text
Come together, right now

...over me
```

## Dependencies

* Python 2.7
* [AWS CLI](https://aws.amazon.com/cli/)
* [Poetry](https://python-poetry.org/)

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

### Install & Use Poetry (required for end-user and development setups)

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

# Install ui dependencies
cd <path_to_congregate>
poetry run dnd install
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

### Usage

``` text
Usage:
    congregate list
    congregate configure
    congregate stage <projects>... [--commit]
    congregate migrate [--processes=<n>] [--skip-users] [--skip-group-export] [--skip-group-import] [--skip-project-export] [--skip-project-import] [--commit]
    congregate rollback [--hard-delete] [--skip-users] [--skip-groups] [--skip-projects] [--commit]
    congregate ui
    congregate export-projects
    congregate do-all [--commit]
    congregate do-all-users [--commit]
    congregate do-all-groups-and-projects [--commit]
    congregate update-staged-user-info [--commit]
    congregate update-aws-creds
    congregate add-users-to-parent-group [--commit]
    congregate remove-blocked-users [--commit]
    congregate update-user-permissions [--access-level=<level>] [--commit]
    congregate get-total-count
    congregate find-unimported-projects [--commit] # TODO: Refactor, project name matching does not seem correct
    congregate stage-unimported-projects [--commit] # TODO: Refactor, broken
    congregate remove-users-from-parent-group [--commit]
    congregate migrate-variables-in-stage [--commit]
    congregate mirror-staged-projects [--commit]
    congregate remove-all-mirrors [--commit]
    congregate find-all-non-private-groups
    congregate make-all-internal-groups-private # TODO: Refactor or rename, as it does not make any changes
    congregate check-projects-visibility # TODO: Refactor or rename, as it's not a check but does an update. Add dry-run
    congregate set-default-branch [--commit]
    congregate enable-mirroring [--commit]
    congregate count-unarchived-projects
    congregate archive-staged-projects [--commit]
    congregate unarchive-staged-projects [--commit]
    congregate find-empty-repos
    congregate compare-groups [--staged]
    congregate staged-user-list
    congregate generate-seed-data [--commit] # TODO: Refactor, broken
    congregate validate-staged-groups-schema
    congregate validate-staged-projects-schema
    congregate map-users [--commit]
    congregate generate-diff [--staged]
    congregate clean [--commit]
    congregate obfuscate
    congregate -h | --help

Options:
    -h, --help                              Show Usage.

Arguments:
    processes                               Set number of processes to run in parallel.
    commit                                  Disable the dry-run and perform the full migration with all reads/writes. 
    skip-users                              Migrate: Skip migrating users; Rollback: Remove only groups and projects.
    hard-delete                             Remove user contributions and solely owned groups.
    skip-groups                             Rollback: Remove only users and projects.
    skip-group-export                       Skip exporting groups from source instance.
    skip-group-import                       Skip importing groups to destination instance.
    skip-projects                           Rollback: Remove only users and empty groups.
    skip-project-export                     Skips the project export and assumes that the project file is already ready
                                                for rewrite. Currently does NOT work for exports through filesystem-aws.
    skip-project-import                     Will do all steps up to import (export, re-write exported project json,
                                                etc). Useful for testing export contents.
    access-level                            Update parent group level user permissions (Guest/Reporter/Developer/Maintainer/Owner).
    staged                                  Compare using staged data

Commands:
    list                                    List all projects of a source instance and save it to {CONGREGATE_PATH}/data/project_json.json.
    configure                               Configure congregate for migrating between two instances and save it to {CONGREGATE_PATH}/data/congregate.conf.
    stage                                   Stage projects to {CONGREGATE_PATH}/data/stage.json,
                                                users to {CONGREGATE_PATH}/data/staged_users.json,
                                                groups to {CONGREGATE_PATH}/data/staged_groups.json.
                                                All projects can be staged with a '.' or 'all'.
    migrate                                 Commence migration based on configuration and staged assets.
    rollback                                Remove staged users/groups/projects on destination.
    ui                                      Deploy UI to port 8000.
    export-projects                         Export and update source instance projects. Bulk project export without user/group info.
    do-all*                                 Configure system, retrieve all projects, users, and groups, stage all information, and commence migration.
    update-staged-user-info                 Update staged user information after migrating only users.
    update-aws-creds                        Run awscli commands based on the keys stored in the config. Useful for docker updates.
    add-users-to-parent-group               If a parent group is set, all users staged will be added to the parent group.
    remove-blocked-users                    Remove all blocked users from staged projects and groups.
    update-user-permissions                 Update parent group member access level. Mainly for lowering to Guest/Reporter.
    get-total-count                         Get total count of migrated projects. Used to compare exported projects to imported projects.
    find-unimported-projects                Return a list of projects that failed import.
    stage-unimported-projects               Stage unimported projects based on {CONGREGATE_PATH}/data/unimported_projects.txt.
    remove-users-from-parent-group          Remove all users with at most reporter access from the parent group.
    migrate-variables-in-stage              Migrate CI variables for staged projects.
    mirror-staged-projects                  Set up project mirroring for staged projects.
    remove-all-mirrors                      Remove all project mirrors for staged projects.
    find-all-non-private-groups             Return list of all groups on destination that are either internal or public.
    make-all-internal-groups-private        Make all internal migrated groups private.
    check-projects-visibility               Return list of all migrated projects' visibility.
    set-default-branch                      Set default branch to master for all projects on destination.
    enable-mirroring                        Start pull mirror process for all projects on destination.
    count-unarchived-projects               Return total number and list of all anarchived projects on source.
    find-empty-repos                        Inspect project repo sizes between source and destination instance in search for empty repos.
                                                This could be misleading as it sometimes shows 0 (zero) commits/tags/bytes for fully migrated projects.
    compare-groups                          Compare source and destination group results.
    staged-user-list                        Output a list of all staged users and their respective user IDs. Used to confirm IDs were updated correctly.
    archive-staged-projects                 Archive projects that are staged, not necessarily migrated.
    unarchive-staged-projects               Unarchive projects that are staged, not necessarily migrate.
    generate-seed-data                      Generate dummy data to test a migration.
    validate-staged-groups-schema           Check staged_groups.json for missing group data.
    validate-staged-projects-schema         Check stage.json for missing project data.
    clean                                   Delete all retrieved and staged data
    generate-diff                           Generates HTML files containing the diff results of the migration
    map-users                               Maps staged user emails to emails defined in the user-provided user_map.csv
    obfuscate                               Obfuscate a secret or password that you want to manually update in the config.
```

#### Important Notes

* The GitLab Project export / import API versions need to match between instances. [This documentation](https://docs.gitlab.com/ee/user/project/settings/import_export.html) shows which versions of the API exist in each version of GitLab.
* The GitLab Group export / import API versions need to match between instances and be at least on **12.8**.

#### Migration steps

##### Dry-run

For all API facing commands `dry_run` is the default mode.
To revert it add `--commit` at the end.

##### Migrate users

Best practice is to first migrate ONLY users by running:

* `congregate ui &` - Open the UI in your browser (by default `localhost:8000`), select and stage all users.
* `congregate update-staged-user-info` - Check output for found and NOT found users on destination.
  * Inspect `data/staged_users.json` if any of the NOT found users are blocked as, by default, they will not be migrated.
  * To explicitly remove blocked users from staged users, groups and projects run `congregate remove-blocked-users`.
* `congregate migrate --skip-group-export --skip-group-import --skip-project-export --skip-project-import` - Inspect the output in:
  * `data/dry_run_user_migration.json`
  * `data/congregate.log`
* `congregate migrate --skip-group-export --skip-group-import --skip-project-export --skip-project-import --commit`

##### Migrate groups and sub-groups

Once all the users are migrated:

* Go back to the UI, select and stage all groups and sub-groups
* Only the top level groups will be staged as they comprise the entire tree structure.
* `congregate migrate --skip-users --skip-project-export --skip-project-import` - Inspect the output in:
  * `data/dry_run_group_migration.json`
  * `data/congregate.log`
* `congregate migrate --skip-users --skip-project-export --skip-project-import --commit`

##### Migrate projects

Once all the users and groups (w/ sub-groups) are migrated:

* Go back to the UI, select and stage projects (either all, or in waves).
* `congregate update-staged-user-info` - Check output for found and NOT found users on destination.
  * All users should be found.
  * Inspect `data/staged_users.json` if any of the NOT found users are blocked as, by default, they will not be migrated.
  * To explicitly remove blocked users from staged users, groups and projects run `congregate remove-blocked-users`.
* `congregate migrate --skip-users --skip-group-export --skip-group-import` - Inspect the output in:
  * `data/dry_run_project_migration.json`
  * `data/congregate.log`
* `congregate migrate --skip-users --skip-group-export --skip-group-import --commit`

##### Rollback

To remove all of the staged users, groups (w/ sub-groups) and projects on destination run:

* `congregate rollback` - Inspect the output in:
  * `data/congregate.log`
* `congregate rollback --commit`
* For more granular rollback see [Usage](#usage).

##### do-all commands

For a CLI only based migration, the following commands are available:

* `do-all` - Migrate all users, projects and their groups
* `do-all-users` - Migrate all users
* `do-all-groups-and-projects` - Migrate all projects and their groups

**N.B.** By default these commands will run in `dry_run` mode. To revert it add `--commit` at the end.

### Development Environment Setup

#### Live reloading for UI development and backend development without a debugger

You will need to turn on debugging in the flask app to see a mostly live reload of the UI. Create the following environment variable before deploying the UI

```bash
export FLASK_DEBUG=1
```

For the UI, you will still need to save the file in your editor and refresh the page, but it's better than restarting flask every time. The app will live reload every time a .py file is changed and saved.

#### Configuring VS Code for Debugging

Refer to [this how-to](https://code.visualstudio.com/docs/python/debugging) for setting up the base debugging settings for a python app in VS Code. Then replace the default `launch.json` flask configuration for this:

```json

{
    "name": "Python: Flask (0.11.x or later)",
    "type": "python",
    "request": "launch",
    "module": "flask",
    "env": {
        "PYTHONPATH": "${workspaceRoot}",
        "CONGREGATE_PATH": "<path_to_congregate>",
        "FLASK_APP": "${CONGREGATE_PATH}/ui"
    },
    "args": [
        "run",
        "--no-debugger",
        "--no-reload"
    ]
}

```

To reload the app in debugging mode, you will need to click the `refresh` icon in VS code (on the sidebar's Explorer tab). Currently VS code doesn't support live reloading flask apps on save.

#### If VS Code doesn't pick up poetry virtualenv

Find virtualenv path

```bash
poetry config --list
```

Add the following line to .vscode/settings.json:

```text
"python.venvPath": "/path/to/virtualenv"
```

You may need to refresh VS Code. VS Code will also call this python interpreter PipEnv, but if you check out the virtualenv directory poetry has stored, you can compare the virtualenv folder names to double check.

## Migration features

:white_check_mark: = supported

:heavy_minus_sign: = not yet supported / in development

:x: = not supported

| Main           | Feature                     | Sub-feature                                                                                                                                                       | GitLab             | Congregate         |
| -------------- | --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------ | ------------------ |
| **Group**      |
|                | Milestones                  |                                                                                                                                                                   | :white_check_mark: | :white_check_mark: |
|                | Badges                      |                                                                                                                                                                   | :white_check_mark: | :white_check_mark: |
|                | Labels                      |                                                                                                                                                                   | :white_check_mark: | :white_check_mark: |
|                | Boards                      | Board Assignee, Labels, Lists                                                                                                                                     | :white_check_mark: | :white_check_mark: |
|                | Members                     |                                                                                                                                                                   | :white_check_mark: | :white_check_mark: |
|                | Epics                       | Parent, Award Emoji, Events, Notes                                                                                                                                | :white_check_mark: | :white_check_mark: |
|                | CI variables                |                                                                                                                                                                   | :x:                | :white_check_mark: |
|                | Hooks                       |                                                                                                                                                                   | :x:                | :heavy_minus_sign: |
|                | Audit Events                |                                                                                                                                                                   | :x:                | :x:                |
|                | Avatars                     |                                                                                                                                                                   | :x:                | :x:                |
| **Project**    |
|                | Labels                      |                                                                                                                                                                   | :white_check_mark: | :white_check_mark: |
|                | Milestones                  | Events                                                                                                                                                            | :white_check_mark: | :white_check_mark: |
|                | Issues                      | Events, Timelogs, Notes, Label Links, Milestone, Resource Label Events, Issue Assignees, Zoom Meetings, Sentry Issue, Award Emoji, Designs, Design Versions, Epic | :white_check_mark: | :white_check_mark: |
|                | Snippets                    | Notes, Award Emoji                                                                                                                                                | :white_check_mark: | :white_check_mark: |
|                | Releases                    |                                                                                                                                                                   | :white_check_mark: | :white_check_mark: |
|                | Members                     |                                                                                                                                                                   | :white_check_mark: | :white_check_mark: |
|                | Group Members               |                                                                                                                                                                   | :white_check_mark: | :white_check_mark: |
|                | Merge requests              | Metrics, Award Emoji, Notes, Merge Request Diff, Events, Timelogs, Label Links, Milestone, Resource Label Events                                                  | :white_check_mark: | :white_check_mark: |
|                | CI Pipelines                | Notes, Stages, External Pull Requests, Merge Request                                                                                                              | :white_check_mark: | :white_check_mark: |
|                | Pipeline schedules          |                                                                                                                                                                   | :white_check_mark: | :white_check_mark: |
|                | External Pull Requests      |                                                                                                                                                                   | :white_check_mark: | :white_check_mark: |
|                | Auto DevOps                 |                                                                                                                                                                   | :white_check_mark: | :white_check_mark: |
|                | Triggers                    |                                                                                                                                                                   | :white_check_mark: | :white_check_mark: |
|                | Services                    |                                                                                                                                                                   | :white_check_mark: | :white_check_mark: |
|                | Protected Branches          | Merge Access Levels, Push Access Levels, Unprotect Access Levels                                                                                                  | :white_check_mark: | :white_check_mark: |
|                | Branches                    |                                                                                                                                                                   | :white_check_mark: | :white_check_mark: |
|                | Default Branch              |                                                                                                                                                                   | :white_check_mark: | :white_check_mark: |
|                | Protected Environments      | Deploy Access Levels                                                                                                                                              | :white_check_mark: | :white_check_mark: |
|                | Protected Tags              | Create Access Levels                                                                                                                                              | :white_check_mark: | :white_check_mark: |
|                | Project Feature             |                                                                                                                                                                   | :white_check_mark: | :white_check_mark: |
|                | Custom Attributes           |                                                                                                                                                                   | :white_check_mark: | :white_check_mark: |
|                | Badges                      |                                                                                                                                                                   | :white_check_mark: | :white_check_mark: |
|                | CI/CD Settings              |                                                                                                                                                                   | :white_check_mark: | :white_check_mark: |
|                | Error Tracking Setting      |                                                                                                                                                                   | :white_check_mark: | :white_check_mark: |
|                | Metrics Setting             |                                                                                                                                                                   | :white_check_mark: | :white_check_mark: |
|                | Boards                      | Lists                                                                                                                                                             | :white_check_mark: | :white_check_mark: |
|                | Service Desk Setting        |                                                                                                                                                                   | :white_check_mark: | :white_check_mark: |
|                | CI variables                |                                                                                                                                                                   | :x:                | :white_check_mark: |
|                | Avatars                     |                                                                                                                                                                   | :white_check_mark: | :white_check_mark: |
|                | Uploads                     |                                                                                                                                                                   | :white_check_mark: | :white_check_mark: |
|                | LFS Objects                 |                                                                                                                                                                   | :white_check_mark: | :white_check_mark: |
|                | Wikis                       |                                                                                                                                                                   | :white_check_mark: | :white_check_mark: |
|                | Push rules                  |                                                                                                                                                                   | :x:                | :white_check_mark: |
|                | Merge request approvals     |                                                                                                                                                                   | :x:                | :white_check_mark: |
|                | Shared Groups               |                                                                                                                                                                   | :x:                | :white_check_mark: |
|                | Registry Repositories       |                                                                                                                                                                   | :x:                | :white_check_mark: |
|                | Container Expiration Policy |                                                                                                                                                                   | :white_check_mark: | :white_check_mark: |
|                | Deploy keys                 |                                                                                                                                                                   | :x:                | :white_check_mark: |
|                | Awards                      |                                                                                                                                                                   | :white_check_mark: | :white_check_mark: |
|                | Webhooks (w/o token)        |                                                                                                                                                                   | :x:                | :white_check_mark: |
|                | Environments                |                                                                                                                                                                   | :x:                | :white_check_mark: |
|                | Audit Events                |                                                                                                                                                                   | :x:                | :x:                |
| **User**       |
|                | Avatars                     |                                                                                                                                                                   | :x:                | :white_check_mark: |
|                | User info                   |                                                                                                                                                                   | :x:                | :white_check_mark: |
|                | User preferences            |                                                                                                                                                                   | :x:                | :white_check_mark: |
| **Standalone** |
|                | Version                     |                                                                                                                                                                   | :x:                | :white_check_mark: |
|                | System hooks (w/o token)    |                                                                                                                                                                   | :x:                | :white_check_mark: |
|                | Services                    |                                                                                                                                                                   | :x:                | :x:                |
|                | Deploy keys                 |                                                                                                                                                                   | :x:                | :x:                |
|                | ToDos                       |                                                                                                                                                                   | :x:                | :x:                |

## Notes from Migration Merge
* Unit tests won't run unless there is a config file in `data/config.json`
* Use `pipenv run pytest` to run tests. `pipenv run python -m unittest discover congregate/` has issues with module relationships on import
* Follow the instructions for setting up a local BitBucket server in Docker. Use version 4.14 of the server from `https://hub.docker.com/r/atlassian/bitbucket-server/`
    * Create one project, two repos, two additional users (beyond the admin)
* Run congregate.sh in the local project directory in the `pipenv shell`
    * `./congregate.sh configure`
    * `./congregate.sh migrate`
* Missing items from the "simple" config found when running migrate
    * `location`: Expecting something like 'aws'
    * `external_source`: Code expects boolean, not string like `BitBucket`
        * `repo_list`: If `external_source` expects `repo_list` which looks to be a file name.
            * Not known what the file format should be
* Command order is `config, list, stage`?
* Coverage is installed. `pytest --cov=congregate/helpers`

### Example JSONs
#### List
* Generated through `./congregate.sh list`
##### users.json
```json
[
    {
        "twitter": "",
        "shared_runners_minutes_limit": null,
        "linkedin": "",
        "color_scheme_id": 1,
        "skype": "",
        "is_admin": false,
        "identities": [],
        "projects_limit": 100000,
        "state": "active",
        "location": null,
        "email": "migrate2@abc.com",
        "website_url": "",
        "username": "migrate_2",
        "bio": null,
        "private_profile": null,
        "external": false,
        "organization": null,
        "public_email": "",
        "extra_shared_runners_minutes_limit": null,
        "name": "Migrate 2",
        "can_create_group": true,
        "reset_password": true,
        "theme_id": 1
    }
]
```
##### groups.json
```json
[
    {
        "lfs_enabled": true,
        "request_access_enabled": false,
        "description": "Drupal",
        "avatar_url": null,
        "visibility": "public",
        "parent_id": null,
        "members": [
            {
                "username": "root",
                "web_url": "https://pse.tanuki.cloud/root",
                "name": "Administrator",
                "expires_at": null,
                "access_level": 50,
                "state": "active",
                "avatar_url": "https://secure.gravatar.com/avatar/e64c7d89f26bd1972efa854d13d7dd61?s=80&d=identicon",
                "id": 1
            }
        ],
        "path": "drupal",
        "file_template_project_id": null,
        "id": 67,
        "full_path": "drupal",
        "name": "Drupal"
    }
]
```
##### project_json.json
```json
[
    {
        "lfs_enabled": true,
        "request_access_enabled": false,
        "mirror_overwrites_diverged_branches": null,
        "approvals_before_merge": 0,
        "forks_count": 0,
        "only_allow_merge_if_all_discussions_are_resolved": false,
        "http_url_to_repo": "https://pse.tanuki.cloud/test_project_1/repo_2.git",
        "web_url": "https://pse.tanuki.cloud/test_project_1/repo_2",
        "mirror": true,
        "mirror_trigger_builds": false,
        "wiki_enabled": true,
        "id": 100,
        "merge_requests_enabled": true,
        "archived": false,
        "snippets_enabled": true,
        "packages_enabled": true,
        "merge_method": "merge",
        "namespace": {
            "kind": "group",
            "web_url": "https://pse.tanuki.cloud/groups/test_project_1",
            "name": "test_project_1",
            "parent_id": null,
            "avatar_url": null,
            "path": "test_project_1",
            "id": 71,
            "full_path": "test_project_1"
        },
        "star_count": 0,
        "ci_default_git_depth": 50,
        "_links": {
            "repo_branches": "https://pse.tanuki.cloud/api/v4/projects/100/repository/branches",
            "merge_requests": "https://pse.tanuki.cloud/api/v4/projects/100/merge_requests",
            "self": "https://pse.tanuki.cloud/api/v4/projects/100",
            "labels": "https://pse.tanuki.cloud/api/v4/projects/100/labels",
            "members": "https://pse.tanuki.cloud/api/v4/projects/100/members",
            "events": "https://pse.tanuki.cloud/api/v4/projects/100/events",
            "issues": "https://pse.tanuki.cloud/api/v4/projects/100/issues"
        },
        "resolve_outdated_diff_discussions": false,
        "issues_enabled": true,
        "path_with_namespace": "test_project_1/repo_2",
        "repository_storage": "default",
        "ci_config_path": null,
        "shared_with_groups": [],
        "description": null,
        "mirror_user_id": 1,
        "default_branch": null,
        "visibility": "private",
        "readme_url": null,
        "ssh_url_to_repo": "git@pse.tanuki.cloud:test_project_1/repo_2.git",
        "public_jobs": true,
        "path": "repo_2",
        "import_status": "failed",
        "only_allow_merge_if_pipeline_succeeds": false,
        "empty_repo": true,
        "open_issues_count": 0,
        "last_activity_at": "2019-07-01T17:13:05.506Z",
        "name": "repo_2",
        "printing_merge_request_link_enabled": true,
        "name_with_namespace": "test_project_1 / repo_2",
        "created_at": "2019-07-01T17:13:05.506Z",
        "shared_runners_enabled": true,
        "creator_id": 1,
        "avatar_url": null,
        "container_registry_enabled": true,
        "only_mirror_protected_branches": null,
        "external_authorization_classification_label": null,
        "tag_list": [],
        "permissions": {
            "group_access": {
                "notification_level": 3,
                "access_level": 50
            },
            "project_access": null
        },
        "jobs_enabled": true
    }
]
```
#### Staging
* Generated through `congregate.sh stage`
##### stage.json
```json
[
    {
        "members": [],
        "http_url_to_repo": "https://pse.tanuki.cloud/test_project_1/repo_2.git",
        "name": "repo_2",
        "project_type": "group",
        "default_branch": null,
        "namespace": "test_project_1",
        "id": 100,
        "visibility": "private",
        "description": null
    }
]
```
##### staged_groups.json
```json
[
    {
        "lfs_enabled": true,
        "request_access_enabled": false,
        "description": "",
        "visibility": "private",
        "parent_id": null,
        "avatar_url": null,
        "members": [
            {
                "username": "root",
                "name": "Administrator",
                "avatar_url": "https://secure.gravatar.com/avatar/e64c7d89f26bd1972efa854d13d7dd61?s=80&d=identicon",
                "expires_at": null,
                "access_level": 50,
                "state": "active",
                "web_url": "https://pse.tanuki.cloud/root",
                "id": 1
            },
            {
                "username": "migrate_1",
                "name": "Migrate 1",
                "avatar_url": "https://secure.gravatar.com/avatar/eb71b11762e9a1f7e8e417ffda6b4853?s=80&d=identicon",
                "expires_at": null,
                "access_level": 30,
                "state": "active",
                "web_url": "https://pse.tanuki.cloud/migrate_1",
                "id": 53
            },
            {
                "username": "migrate_2",
                "name": "Migrate 2",
                "avatar_url": "https://secure.gravatar.com/avatar/2c6b06bf40ad99d5f39600566e94ac6d?s=80&d=identicon",
                "expires_at": null,
                "access_level": 30,
                "state": "active",
                "web_url": "https://pse.tanuki.cloud/migrate_2",
                "id": 54
            }
        ],
        "path": "test_project_1",
        "file_template_project_id": null,
        "id": 71,
        "full_path": "test_project_1",
        "name": "test_project_1"
    }
]
```
##### staged_users.json
```json
[
    {
        "twitter": "",
        "shared_runners_minutes_limit": null,
        "linkedin": "",
        "color_scheme_id": 1,
        "skype": "",
        "identities": [],
        "projects_limit": 100000,
        "state": "active",
        "location": null,
        "email": "migrate1@abc.com",
        "website_url": "",
        "username": "migrate_1",
        "bio": null,
        "private_profile": null,
        "can_create_group": true,
        "is_admin": false,
        "external": false,
        "theme_id": 1,
        "public_email": "",
        "extra_shared_runners_minutes_limit": null,
        "name": "Migrate 1",
        "reset_password": true,
        "organization": null
    },
    {
        "twitter": "",
        "shared_runners_minutes_limit": null,
        "linkedin": "",
        "color_scheme_id": 1,
        "skype": "",
        "identities": [],
        "projects_limit": 100000,
        "state": "active",
        "location": null,
        "email": "migrate2@abc.com",
        "website_url": "",
        "username": "migrate_2",
        "bio": null,
        "private_profile": null,
        "can_create_group": true,
        "is_admin": false,
        "external": false,
        "theme_id": 1,
        "public_email": "",
        "extra_shared_runners_minutes_limit": null,
        "name": "Migrate 2",
        "reset_password": true,
        "organization": null
    }
]
```
#### Config
* Generated through `congregate.sh config`
Note: Your destination and source info will be different in a true scenario. This is to show formatting.
##### config.json
###### Internal
```json
{
    "config": {
        "external_source": false,
        "source_instance_token": "junktoken",
        "number_of_threads": 2,
        "destination_instance_host": "https://pse.tanuki.cloud",
        "destination_instance_token": "junktoken",
        "location": "filesystem",
        "source_instance_host": "https://pse.tanuki.cloud",
        "import_user_id": 1,
        "path": "/Users/gmiller/projects/congregate"
    }
}
```
###### External
```json
{
    "config": {
        "external_source": true,
        "destination_instance_host": "https://pse.tanuki.cloud",
        "external_user_password": "ePb-84m7ZriB3NfbP_Z!eQFM7cE7ewp8",
        "external_user_name": "gmiller",
        "number_of_threads": 2,
        "destination_instance_token": "junktoken",
        "import_user_id": 1,
        "location": "aws",
        "external_source_url": "http://gmiller@bbhost:7990",
        "repo_list_path": "data/repos.json"
    }
}
```
#### Repo Items?
* Currently hand-generated.
* BitBucket specific?
##### repos.json
```json
[
  {
    "name": "repo_1",
    "web_repo_url": "http://gmiller@bbhost:7990/scm/tp1/repo_1.git",
    "group": "test_project_1",
    "project_users": [
      {
        "displayName": "Migrate 1",
        "name": "Migrate 1",
        "username": "migrate_1",
        "email": "migrate1@abc.com",
        "permission": "PROJECT_WRITE"
      },
      {
        "displayName": "Migrate 2",
        "name": "Migrate 2",
        "username": "migrate_2",
        "email": "migrate2@abc.com",
        "permission": "PROJECT_READ"
      }],
    "repo_users": [
      {
        "displayName": "Migrate 2",
        "name": "Migrate 2",
        "username": "migrate_2",
        "email": "migrate2@abc.com",
        "permission": "REPO_WRITE"
      }
    ]
  },
  {
    "name": "repo_2",
    "web_repo_url": "http://gmiller@bbhost:7990/scm/tp1/repo_2.git",
    "group": "test_project_1",
    "project_users": [
      {
        "displayName": "Migrate 2",
        "name": "Migrate 2",
        "username": "migrate_2",
        "email": "migrate2@abc.com",
        "permission": "PROJECT_READ"
      }
    ],
    "repo_users": [
      {
        "displayName": "Migrate 2",
        "name": "Migrate 2",
        "username": "migrate_2",
        "email": "migrate2@abc.com",
        "permission": "REPO_READ"
      }
    ]
  }
]
```
