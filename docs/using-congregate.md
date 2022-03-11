# How to use Congregate

## Quick Start

1. Download and install docker, podman, or any other application that can run docker containers
1. Run `git clone git@gitlab.com:gitlab-org/professional-services-automation/tools/migration/congregate.git` to pull the congregate repo to your local environment.
1. Generate a personal access token from your gitlab.com account that has the read_registry permission by clicking `User Icon (top right) > Settings > Access Tokens > Generate Access Token`.
1. Then run `docker login registry.gitlab.com` and provide your username and paste the access token when prompted for a password.
1. Pull the docker image from the [container registry](https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate/container_registry/2394823):
    * :white_check_mark: For official versioned releases, `docker pull registry.gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate:<version>` (or `:latest-<debian|centos>`)
    * :warning: For rolling releases, `docker pull registry.gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate:rolling-debian` (or `:rolling-centos`)
1. Run `docker images -a` to list and copy the `image-id` of the congregate image.
1. Create and run the Congregate docker container:

    ```bash
    docker run \
    --name <name> \
    -v /var/run/docker.sock:/var/run/docker.sock \   # expose docker socket as volume
    -v /etc/hosts:/etc/hosts \   # expose DNS mapping
    -p 8000:8000 \   # expose UI port
    -it <image-id> \
    /bin/bash   # or zsh
    ```

1. Set `/var/run/docker.sock` permissions for `ps-user` by running `sudo chmod 666 /var/run/docker.sock`.
1. Exit (*Ctrl+d*) the container (stops it).
1. Run `docker ps` to get the `container-id`.
1. To resume the container and keep it up:

    ```bash
    docker start <container-id>
    docker exec -it <container-id> /bin/bash   # OR -itd (zsh)
    ```

1. Modify the configuration file in `/opt/congregate/congregate.conf` using the [`congregate.conf.template`](congregate.conf.template) as a guide.
1. Check out the fundamental [congregate commands](#congregate-commands) below.

## Full Congregate setup with test environment

Follow the steps in [this issue template](./setup-dev-env.md) for a full guide on how to setup a source, destination and congregate system to test congregate functionality.

<!--
1. Download and install docker, podman, or any other application that can run docker containers
1. download  `congregate:<version>` using `docker pull registry.gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate:<version>`
     - create personal access token and store the token in a file called `gl_token.txt`
     - login into registry.gitlab.com with docker, `cat gl_token.txt | docker login --username '<email-address>' --password-stdin registry.gitlab.com`

1. navigate to `https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate` and clone the repository to your local machine
1. spin up gitlab, source, and congregate instances with data on them.
    - Create two Gitlab docker instances with `gitlab-ee` images and a `congregate` instance with the image you pulled previously in step one
       - Spin up migration test environment: `docker-compose -f migration-gitlab-to-gitlab.yaml up -d`
       - This will create 3 services and one network:
         - services:
           - `gitlab-web` (accessible on port `80`)
           - `gitlab-web-2` (accessible on port `8080`)
           - `congregate` (accessible on port `8000` if you launch the ui via the `congregate ui &` command)
         - network:
           - `migration-network`
    - manually create in `gitlab-web`:
      - personal access token under the default `root` user
      - a group (or groups) to test a migration via congregate
    - manually create in `gitlab-web-2`:
      - personal access token under the default `root` user
1. `exec` into congregate services `docker-compose -f migration-gitlab-to-gitlab.yaml exec congregate bash`
1. Run the congregate configuration with `./congregate.sh configure` and follow the prompts. Provide `http://gitlab-web` as the source and `http://gitlab-web-2` as the destination along with username and tokens. You can grab examples from the [configuration template](https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate/-/blob/master/congregate.conf.template)
1. run `./congregate.sh list` to pull all data from source systems
1. if this runs successfully, run a `less data/groups.json` to see some of the data that was pulled in.
1. migrate a specific group by finding the group id by running `cat data/groups.json | grep -i <group-name> -A 10 -B 10`
1. then take that group id that you found and run `./congregate.sh stage-groups <id> --commit` where the ids are a space delimited list
1. now that we have staged data (which you can verify by doing `ll data/staged_*` to see the `staged_groups.json`, etc files), run `./congregate.sh migrate --commit`
1. validate the migration worked by navigating to the gitlab UI on the destination (`http://localhost:8080`) and going to the admin pane (wrench top middle) and look for the migrated groups.
-->

## Congregate commands

During migrations, we generally do the same type of commands every time in roughly the same order.

![Congregate Process Flow](/img/process-flow.png)

### List

`./congregate.sh list` is the command that gathers meta data from the source system(s) to prepare for later steps of migration. Listing pulls all of the metadata from each of these systems and typically requires an admin token or read-only all credentials to be successful. To set these run `./congregate.sh configure` or modify `data/congregate.conf` with the SCM and/or CI source hostname(s) and credentials provided by the customer. Be sure to reference the [congregate config template](/congregate.conf.template) to format it correctly if you're editing the `.conf` file directly.

Listing can take quite a long time and is directly dependant on the amount of data in the source system(s). To tune the concurrency of a list, you can add `--processes=16` (GitHub only) to a `list` command. Without setting this, it will use `processes=nproc` based on the hardware number of processes. Be careful with going over 16 processes as it will increase the chances of causing undue harm to the source systems (which if their API rate limit isn't set, could cause stability problems)

If you need to re-list and don't want to overwrite any data that you have listed previously (and get a small performance boost), run it with `--partial`. Additional `--skip-*` arguments allow you to skip users, groups, projects and ci.

If you are migrating data from CI sources with an SCM source, listing will also perform a mapping function to map CI jobs to SCM repositories. This functionality will position migrations of build config xmls into repositories for future transformation into `gitlab-ci.yml`.

### Stage

Staging data for migration follows the same usage pattern as staging data does with a git-based workflow. Now that we've run a `./congregate.sh list` to get ALL of the data to the local filesystem (combination of local MongoDB and `.json` files), we need to select which users, projects, and groups to migrate. The output of any flavor of `stage` command will be the `staged_groups.json`, `staged_projects.json`, and `staged_users.json` files in the `data` directory.

When running stage in a shell (without UI), we will need to identify the project and group IDs that are in scope for the current migration. We can stage a few different ways.

### `stage-projects`

To get the project IDs from the names of the projects (that the customer should have provided) you can run a `cat data/projects.json | grep <ProjectName> -A10 -B10` where ProjectName is the name of the repository (github & bitbucket) or project (gitlab) that is in scope to migrate. From there you will see the ID that can be noted for the following command `./congregate.sh stage-projects 13 78 951 446`. Note you can list multiple project ids space delimited after the stage-projects verb. To force this command to write to the `staged_projects.json` and other staged json files use the `--commit` flag.

### `stage-groups`

This process is very similar to stage-projects, but you need to search for group ids in the `groups.json` file. Run `cat data/projects.json | grep <GroupName> -A10 -B10`. Then run `./congregate.sh stage-groups 78 651 997 --commit` to produce the `staged_*.json` files.

### `stage-wave`

For larger migrations, customers often want to define waves of migration in a spreadsheet that congregate can read in to stage many different groups and projects at once without having to do the initial investigation for project and group ids. To set this up we need to add a few lines to the `data/congregate.conf` that look like the ones from [the template](/congregate.conf.template#L170). This configuration  template refers to the [waves.csv](/templates/waves.csv) file. A more verbose description on how this configuration works is in the [configuration section](#Wave-definition-spreadsheet-ingestion) below.

Once we have this in place, you can run `./congregate.sh stage-wave <WaveName> --commit` to stage all projects and groups defined by the spreadsheet.

### Stage using the UI

If you are running congregate from a full desktop experience (not SSH'ed or BASH'ed into a container running on a cluster), you can use the UI to stage data after it is listed by using `./congregate.sh ui &`. This will give you the ability to select the specific groups, projects and users that you want to stage for a migration. Once you have checked all the boxes, you can click stage to generate the `staged_*.json` files required for the final step of migration.

### Migrate

`./congregate.sh migrate` is the action of initiating the data imports on gitlab based on the information on `staged_projects.json`, `staged_groups.json`, and `staged_users.json`. You can run to see the log output to see what projects and groups will be migrated to what locations. When you are satisfied with these results, you can add the `--commit` flag to run the migration for real. Note, if you want to adjust the concurrency, you can add the `--processes=n` flag to this command as well.

In General, we like to migrate all users into the destination system before doing any group or project migrations. This is because if the user is not found during a project or group migration, there will be attribution errors on import that manifest as MRs or other objects in gitlab being owned by or attributed to the import user which is usually root or some Admin.

#### Migrate Users

Best practice is to first migrate ONLY users by running:

- `./congregate.sh ui &` - Open the UI in your browser (by default `localhost:8000`), select and stage all users.
- `./congregate.sh migrate --skip-group-export --skip-group-import --skip-project-export --skip-project-import` - Inspect the dry-run output in:
  - `data/results/dry_run_user_migration.json`
  - `data/logs/congregate.log`
  - Inspect `data/staged_users.json` if any of the NOT found users are inactive as, by default, they will not be migrated.
  - To explicitly remove inactive users from staged users, groups and projects run `./congregate.sh remove-inactive-users --commit`.
- `./congregate.sh migrate --skip-group-export --skip-group-import --skip-project-export --skip-project-import --commit`

#### Migrate Groups and Sub-Groups

Once all the users are migrated:

- Go back to the UI, select and stage all groups and sub-groups.
- Only the top level groups will be staged as they comprise the entire tree structure.
- `./congregate.sh search-for-staged-users` - Check output for found and NOT found users on destination.
  - All users should be found.
  - Inspect `data/staged_users.json` if any of the NOT found users are inactive as, by default, they will not be migrated.
  - To explicitly remove inactive users from staged users, groups and projects run `./congregate.sh remove-inactive-users --commit`.
- `./congregate.sh migrate --skip-users --skip-project-export --skip-project-import` - Inspect the dry-run output in:
  - `data/results/dry_run_group_migration.json`
  - `data/logs/congregate.log`
- `./congregate.sh migrate --skip-users --skip-project-export --skip-project-import --commit`

#### Migrate Projects

Once all the users and groups and sub-groups are migrated:

- Go back to the UI, select and stage projects (either all, or in waves).
- `./congregate.sh search-for-staged-users` - Check output for found and NOT found users on destination.
  - All users should be found.
  - Inspect `data/staged_users.json` if any of the NOT found users are inactive as, by default, they will not be migrated.
  - To explicitly remove inactive users from staged users, groups and projects run `./congregate.sh remove-inactive-users --commit`.
- `./congregate.sh migrate --skip-users --skip-group-export --skip-group-import` - Inspect the dry-run output in:
  - `data/results/dry_run_project_migration.json`
  - `data/logs/congregate.log`
- `./congregate.sh migrate --skip-users --skip-group-export --skip-group-import --commit`

### Rollback

To remove all of the staged users, groups (w/ sub-groups) and projects on destination run:

> :warning: This will delete everything that was previously staged and migrated. If a significant period of time has passed since migration, you will risk losing data added by users in the time since migration completed. There is a default timeout on rollback 24 hours from the time of migration that acts as a guard against accidental rollbacks.

- `./congregate.sh rollback --hard-delete` - Inspect the output in:
  - `data/logs/congregate.log`
- `./congregate.sh rollback --commit`
- For more granular rollback see [Usage](#usage).

## Checking the results of a migration

Lots of this section is covered in our [runbooks](runbooks), but an overview is provided below.

### Spot checking features

- group creation
- project creation
- membership
- branches
- commits
- tags
- merge requests
- user attribution
- branch protection settings
- merge request approver settings

### Automated diff report

TODO

### Migration results.json

TODO

## Congregate Configuration Items

TODO

### Migration Reporting

Migration reporting is typically an exercise in data gathering and normalization to determine the success of a migration. At scale this can be difficult since the sign-off of a migration is distributed to many people. Congregate can be configured to automatically create issues to gather migration sign-off agreement from application owners.

To configure this functionality, we need to add some lines to the congregate.conf from [the template](/congregate.conf.template#L61). Note:

- the `issue1.md` expects this file to be in `data/issue_templates`
- `pmi_project_id` is the id of the project that will contain all of the sign-off issues
- `subs` is a key value pair dictionary that you can use to replace specific strings from the template with customer specific info.

Once we have the issues automatically being created on `./congregate.sh migrate --commit` we can configure [a stand-alone utility](https://gitlab.com/ubs-group1/ubs/UBS-Services-SOW-PSE-00169/reporting-utility) to poll these issues and build a csv that can be ingested by the customer's data-analyzer tool of choice.

TODO: Add info on this once we have it more complete.

### Wave definition spreadsheet ingestion

> This feature was developed for GitHub imports and may not work with other source systems.

The data in the [waves spreadsheet](/templates/waves.csv) represents the Repo/Project URLs that are in scope for a wave of migration. The required fields are `Wave Name`, `SCM URL` (can be repo or Org). Option arguments are `Group Path` if your customer wants to migrate the Orgs and Repos to locations in a nested Group Sub-group tree in the destination gitlab instance.

If the [migration reporting](#migration-reporting) feature is configured, there are two additional fields that are optional that will facilitate creating "sign-off" issues and assign them to application owners. The two fields are `Application ID` and `Application Owner Email`. These column names are mapped in the config file to the variable names that congregate expects.

To exercise this configuration, follow steps in the [stage wave](#stage-wave) section.
