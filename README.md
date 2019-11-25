* TODO: Add build badge for at least master
* TODO: Add coverage report link from htmlcov

# Congregate

[TOC]

## About

Congregate is a utility for migrating one or more GitLab instances into another, single GitLab instance.

```text
Come together, right now

...over me
```

## Dependencies

- Python 2.7
- [AWS CLI](https://aws.amazon.com/cli/)
- [PipEnv](https://docs.pipenv.org/)

## Setup

### TL;DR Install

Copy the following code snippet to a file in the congregate directory and run it

```bash
#!/bin/bash

# install pipenv
pip install pipenv

# install python dependencies
pipenv install

# install UI dependencies
pipenv run dnd install

# create congregate path
CONGREGATE_PATH=$(pwd)

# copy congregate script to a bin directory
cp congregate /usr/local/bin

echo "export CONGREGATE_PATH=$CONGREGATE_PATH" >> ~/.bash_profile
```

Once all of the dependencies are installed, run `congregate config` to set up the congregate config.

There are currently *three* different methods for migrating projects (groups and users are all through the API):

- **filesystem** - download all projects locally and import them locally.
- **filesystem-aws** - download all projects locally, copy the exports to an S3 bucket for storage, then delete the project locally. Copy the files back from S3, import the file, then delete the local file again.
- **aws** - export all projects directly to an S3 bucket and import directly from the S3 bucket.

`filesystem-aws` is used to help work with company policies like restricting presigned URLs or in case any of the source instances involved in the migration cannot connect to an S3 bucket while the destination instance can.

### Install & Use PipEnv (required for end-user and development setups)

```bash
pip install pipenv

# install dependencies from Pipfile
cd /path/to/congregate
pipenv install

# start-up python virtualenv
cd /path/to/congregate
pipenv shell

# install ui dependencies
cd /path/to/congregate
pipenv run dnd install
```

### Installing Congregate (end-user)

From **docker**:

1. Pull the docker image from the container registry
2. Run the following command:

```bash
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

### Usage

``` text
Usage:
    congregate list
    congregate config
    congregate stage <projects>...
    congregate migrate [--threads=<n>] [--dry-run] [--skip-users] [--skip-project-import] [--skip-project-export]
    congregate cleanup [--dry-run] [--hard-delete] [--skip-users] [--skip-groups] [--skip-projects]
    congregate ui
    congregate export-projects
    congregate import-projects
    congregate do_all
    congregate update-staged-user-info
    congregate update-aws-creds
    congregate add-users-to-parent-group
    congregate remove-blocked-users [--dry-run]
    congregate update-user-permissions [--access-level=<level>]
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
    congregate set-default-branch
    congregate enable_mirroring
    congregate count-unarchived-projects
    congregate archive-staged-projects [--dry-run]
    congregate unarchive-staged-projects [--dry-run]
    congregate find-empty-repos
    congregate compare-groups [--staged]
    congregate staged-user-list
    congregate generate-seed-data
    congregate map-new-users-to-groups-and-projects [--dry-run]
    congregate validate-staged-groups-schema
    congregate validate-staged-projects-schema
    congregate map-users
    congregate -h | --help

Options:
    -h, --help                              Show Usage.

Arguments:
    threads                                 Set number of threads to run in parallel.
    dry-run                                 Perform local listing of metadata that would be handled during the migration.
    skip-users                              Include groups and projects.
    hard-delete                             Remove user contributions and solely owned groups.
    skip-groups                             Include users and projects.
    skip-projects                           Include ONLY users (removing ONLY groups is not possible).
    skip-project-import                     Will do all steps up to import (export, re-write exported project json,
                                                etc). Useful for testing export contents.
    skip-project-export                     Skips the project export and assumes that the project file is already ready
                                                for rewrite. Currently does NOT work for exports through filesystem-aws.
    access-level                            Update parent group level user permissions (Guest/Reporter/Developer/Maintainer/Owner).
    staged                                  Compare two groups that are staged for migration.

Commands:
    list                                    List all projects of a source instance and save it to {CONGREGATE_PATH}/data/project_json.json.
    config                                  Configure congregate for migrating between two instances and save it to {CONGREGATE_PATH}/data/config.json.
    stage                                   Stage projects to {CONGREGATE_PATH}/data/stage.json,
                                                users to {CONGREGATE_PATH}/data/staged_users.json,
                                                groups to {CONGREGATE_PATH}/data/staged_groups.json.
                                                All projects can be staged with a '.' or 'all'.
    migrate                                 Commence migration based on configuration and staged assets.
    cleanup                                 Remove staged users/groups/projects on destination.
    ui                                      Deploy UI to port 8000.
    export-projects                         Export and update source instance projects. Bulk project export without user/group info.
    import-projects                         Import exported and updated projects onto destination instance. Destination user/group info required.
    do_all                                  Configure system, retrieve all projects, users, and groups, stage all information, and commence migration.
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
    add-all-mirrors                         Set up project mirroring for staged projects.
    remove-all-mirrors                      Remove all project mirrors for staged projects.
    find-all-internal-projects              Find all internal projects.
    make-all-internal-groups-private        Make all internal migrated groups private.
    check-projects-visibility               Return list of all migrated projects' visibility.
    find-empty-repos                        Inspect project repo sizes between source and destination instance in search for empty repos.
                                                This could be misleading as it sometimes shows 0 (zero) commits/tags/bytes for fully migrated projects.
    compare-groups                          Compare source and destination group results.
    staged-user-list                        Output a list of all staged users and their respective user IDs. Used to confirm IDs were updated correctly.
    archive-staged-projects                 Archive projects that are staged, not necessarily migrated.
    unarchive-staged-projects               Unarchive projects that are staged, not necessarily migrate.
    generate-seed-data                      Generate dummy data to test a migration.
    map-new-users-to-groups-and-projects    Map new_users.json to the staged_groups.json and stage.json (projects) files without making API calls.
                                                Requires that update-staged-user-info has been called, first, to create new_users.json.
    validate-staged-groups-schema           Check staged_groups.json for missing group data.
    validate-staged-projects-schema         Check stage.json for missing project data.
    map-users                               Maps staged user emails to emails defined in the user-provided user_map.csv
```

#### Migration steps

##### Migrate users

Best practice is to first migrate ONLY users by running:

* `congregate ui &` - Open the UI in your browser (by default `localhost:8000`), select and stage all users.
* `congregate update-staged-user-info` - Check output for found and NOT found users on destination.
  * Inspect `data/staged_users.json` if any of the NOT found users are blocked as, by default, they will not be migrated.
  * To explicitly remove blocked users from staged users, groups and projects run `congregate remove-blocked-users`.
* `congregate migrate --dry-run` - Inspect the output in
  * `data/dry_run_user_migration.json`
  * `data/congregate.log`
* `congregate migrate`

##### Migrate groups and projects

Once all the users are migrated:

* Go back to the UI, select and stage all projects, groups and users.
* `congregate update-staged-user-info` - Check output for found and NOT found users on destination.
  * All users should be found.
  * Inspect `data/staged_users.json` if any of the NOT found users are blocked as, by default, they will not be migrated.
  * To explicitly remove blocked users from staged users, groups and projects run `congregate remove-blocked-users`.
* `congregate map-new-users-to-groups-and-projects --dry-run` - Check output for any remaining unmapped users.
* `congregate migrate --skip-users --dry-run` - Inspect the output in
  * `dry_run_project_migration.json`
  * `dry_run_group_migration.json`
  * `congregate.log` (especially `more congregate.log | grep "REWRITE"`)
* `congregate migrate --skip-users`

##### Cleanup

To remove all of the staged users, groups and projects on destination run:

* `congregate cleanup --dry-run` - Inspect the output.
* `congregate cleanup`
* For more granular cleanup see [Usage](#usage).

#### Important Note

The GitLab import/export API versions need to match between instances. [This documentation](https://docs.gitlab.com/ee/user/project/settings/import_export.html) shows which versions of the API exist in each version of GitLab

### Development Environment Setup

Once congregate is installed

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

To reload the app in debugging mode, you will need to click the `refresh` icon in VS code (on the sidebar's Explorer tab). Currently VS code doesn't support live reloading flask apps on save.

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

To reload the app in debugging mode, you will need to click the `refresh` icon in VS code (on the sidebar's Explorer tab). Currently VS code doesn't support live reloading flask apps on save.

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

To reload the app in debugging mode, you will need to click the `refresh` icon in VS code (on the sidebar's Explorer tab). Currently VS code doesn't support live reloading flask apps on save.

## Migration features

| Main | Feature | Sub-feature | Status |
|-|-|-|-|
| BitBucket ||| :heavy_minus_sign: |
| Groups |
|| Sub-groups || :white_check_mark: |
|| Group CI variables || :white_check_mark: |
|| Members || :white_check_mark: |
|| Group info || :white_check_mark: |
|| Badges || :white_check_mark: |
| Projects |
|| Branches || :white_check_mark: |
|| Members || :white_check_mark: |
|| Avatars || :white_check_mark: |
|| Push rules || :white_check_mark: |
|| Merge requests || :white_check_mark: |
|| Merge request approvers || :white_check_mark: |
|| Protected branches || :white_check_mark: |
|| Project info || :white_check_mark: |
|| CI variables || :white_check_mark: |
|| Container Registry || :white_check_mark: |
|| Services || :x: |
|| Deploy keys || :white_check_mark: |
|| Awards || :white_check_mark: |
|| Pipeline schedules || :white_check_mark: |
|| Badges || :white_check_mark: |
| Standalone |
|| Users |
||| Avatars | :white_check_mark: |
||| User info | :white_check_mark: |
|| Version || :white_check_mark: |
|| Services || :x: |
|| Deploy keys || :x: |

:x: = not supported

:white_check_mark: = supported

:heavy_minus_sign: = not yet supported / in development

## Features matrix

| Features  |  Import/Export API |  Congregate |
|---|---|---|
| Project and wiki repositories  |  :white_check_mark:   |  :white_check_mark: |
| Project uploads  | :white_check_mark:  | :white_check_mark:  |
| Project configuration, including services  |  :white_check_mark: |  :white_check_mark: |
| Issues with comments, merge requests with diffs and comments, labels, milestones, snippets, and other project entities  |  :white_check_mark: |  :white_check_mark: |
| LFS objects  |  :white_check_mark: |  :white_check_mark: |
| Project badges  | :white_check_mark: (URL data not propagated)  | :white_check_mark: (update only) |
| Protected branches  |  :white_check_mark: (unstable) |  :white_check_mark: |
| Pipelines schedules  |  :white_check_mark: (unstable) |  :white_check_mark: |
| Build traces and artifacts  |  :x: |  :x: |
| Container Registry  |  :x:  |  :white_check_mark:  |
| CI variables  | :x:  |  :white_check_mark:  |
| Webhooks  | :x:  | :heavy_minus_sign:   |
| Deploy Keys | :x: | :white_check_mark: (project only) |
| Any encrypted tokens  |  :x: | :heavy_minus_sign:   |
| Merge Request Approvers  | :x:  | :white_check_mark:  |
| Group badges  | :x:  | :white_check_mark:  |
| Push Rules  |  :x: |  :white_check_mark: |
| Users  | :x:  |  :white_check_mark: |
| Groups  | :x:  | :white_check_mark:  |

:x: = not supported

:white_check_mark: = supported

:heavy_minus_sign: = not yet supported / in development



## Notes from Migration Merge
* Unit tests won't run unless there is a config file in `data/config.json`
* Use `pipenv run pytest` to run tests. `pipenv run python -m unittest discover congregate/` has issues with module relationships on import
* Follow the instructions for setting up a local BitBucket server in Docker. Use version 4.14 of the server from `https://hub.docker.com/r/atlassian/bitbucket-server/`
    * Create one project, two repos, two additional users (beyond the admin)
* Run congregate.sh in the local project directory in the `pipenv shell`
    * `./congregate.sh config`
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
* Generated through `congregate.sh list`
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
