<!-- 
    Copy the contents of this runbook into an issue when running through a migration wave.
    Post the link to the issue on the Slack channel dedicated to this migration. 
-->

# <customer name> Migration Wave <insert-number-here>

This runbook covers the process of migrating a wave of **groups and projects** from a source GitLab instance to a self-managed destination GitLab instance. This is assuming all users have already been migrated.

## Migration Blackout Period

<!--
    Specify the date and time of this migration wave. For example

    3:00PM 2020-09-07 - 3:00AM 2020-09-07
-->

## Slack channel for communication

<!--
    Provide the name and link of the Slack channel dedicated to communicating the status and events of the migration
-->

## Points of contact

<!--
    Provide the gitlab handles for the various people involved in this migration wave and their specific role in the migration. 
    
    For example:

    ### GitLab

    * @leopardm: PSE conducting the migration

    ### John Doe

    * @jdoe: Customer point of contact
-->

## Groups to migrate

### Legend

* :x: = not started
* :heavy_minus_sign: = in progress (optional)
* :white_check_mark: = finished

<!--
Copy the following data and add subsequent rows for wave migration or migration of nested groups and personal projects

| Completed | Group Name / User Username | Total Projects   | Size            |
| --------- | -------------------------- | ---------------- | --------------- |
| :x:       | [name / username]          | [total-projects] | [size]          |
| **Total** | [total-number]             | [sum-of-column]  | [sum-of-column] |

Copy the following data and add subsequent rows for single group migration

| Completed | Project Path | Repo Size   |
| --------- | ------------ | ----------- |
| :x:       | [name]       | [repo-size] |
-->

## Professional Services Steps to Complete Migration Wave

### User migration

#### Prepare users

* [ ] Review migration schedule (see customer migration schedule)
* [ ] Login to the migration VM using `ssh -L 8000:localhost:8000 <vm_alias_ip_or_hostname>` to expose UI port `8000` outside of the docker container
* [ ] Check the status of self-managed instances
  * [ ] Confirm you can reach the UI of the instance
  * [ ] Confirm you can reach the API through cURL or a REST client
* [ ] Create a directory called "waves" in `/opt/congregate/data` in the container if it doesn't already exist
* [ ] Create a directory called `user_wave` in `/opt/congregate/data/waves` if it doesn't already exist
* [ ] Run `nohup ./congregate.sh list > data/waves/listing.log 2>&1 &` at the beginning of the migration blackout period
* [ ] Stage ALL users
  * **NOTE:** Make sure no groups and projects are staged
* [ ] Copy `data/staged_users.json` to `/opt/congregate/data/waves/user_wave`
* [ ] Lookup whether the staged users (emails) already exist on the destination by running `./congregate.sh search-for-staged-users`
  * This will output a list of FOUND, NOT FOUND and DUPLICATE user `email`, along with their `id` and `state`
* [ ] Determine with customer whether to (configure):
  * `keep_inactive_users` (`False` by default),
  * `reset_pwd` (`True` by default),
  * `force_rand_pwd` (`False` by default)
* By default inactive users are skipped during user migration. To be sure they are removed from staged users, groups and projects run the following command:
  * [ ] Dry run: `./congregate.sh remove-inactive-users`
  * [ ] Live: `./congregate.sh remove-inactive-users --commit`
* [ ] Notify in the internal Slack channel dedicated to this migration you have completed preparation for the user wave

#### Dry run users

* [ ] Run the following command: `nohup ./congregate.sh migrate > data/waves/user_wave/user_wave_dry_run.log 2>&1 &`
  * **NOTE:** The command assumes you have no groups or projects staged
* [ ] Confirm everything looks correct and move on to the next step in the runbook
  * Specifically, review the API requests and make sure the paths look correct.
  * If anything looks wrong in the dry run, make a note of it in the issue and reach out to @pprokic or @leopardm for review. Do not proceed with the migration if the dry run data looks incorrect. If this is incorrect, the data we send will be incorrect.
* [ ] Copy `data/results/dry_run_user_migration.json` to `/opt/congregate/data/waves/user_wave/` and attach to this issue
* [ ] Notify in the internal Slack channel dedicated to this migration you have completed dry run for the user wave
* [ ] Request customer sign-off

#### Migrate users

* [ ] Notify in the internal Slack channel dedicated to this migration you are starting the user migration wave
* [ ] Notify the customer in the customer-facing Slack channel you are starting the user migration wave
* [ ] Run the following command `nohup ./congregate.sh migrate --commit > data/waves/user_wave/user_wave.log 2>&1 &`
* [ ] Monitor the wave periodically by running `tail -f data/waves/user_wave/user_wave.log`
* [ ] Copy the following files to `/opt/congregate/data/waves/user_wave/` and attach to this issue:
  * `data/logs/congregate.log`
  * `data/logs/audit.log`
  * `data/results/user_migration_results.json`
  * `data/waves/user_wave/user_wave.log`

### Group and project migration

#### Prepare groups and projects

* [ ] Review migration schedule (see customer migration schedule)
* [ ] Check the status of the destination instance
  * [ ] Confirm you can reach the UI of the instance
  * [ ] Confirm you can reach the API through cURL or a REST client
* [ ] Create a directory called "waves" in `/opt/congregate/data` in the container if it doesn't already exist
* [ ] Create a directory called `wave_<insert_wave_number>` in `/opt/congregate/data/waves` if it doesn't already exist
* [ ] Run `nohup ./congregate.sh list > data/waves/listing.log 2>&1 &` at the beginning of the migration blackout period
* [ ] Stage groups or projects based on the wave schedule in the UI
  * [ ] If staging by group make sure to stage all sub-groups as well
* [ ] Copy all staged data to `/opt/congregate/data/waves/wave_<insert_wave_number>/`
* [ ] Notify in the internal Slack channel dedicated to this migration you have completed preparation for the wave

#### Dry run groups and projects

* [ ] Run the following command: `nohup ./congregate.sh migrate --skip-users > data/waves/wave_<insert_wave_number>/wave_<insert_wave_number>_dry_run.log 2>&1 &`
  * [ ] If only sub-groups are staged make sure to add `--subgroups-only`
* [ ] Confirm everything looks correct and move on to the next step in the runbook
  * Specifically, review the API requests and make sure the paths look correct. For example, make sure any parent IDs or namespaces are matching the parent ID and parent namespaces we have specified in the congregate config.
  * If anything looks wrong in the dry run, make a note of it in the issue and reach out to @pprokic or @leopardm for review. Do not proceed with the migration if the dry run data looks incorrect. If this is incorrect, the data we send will be incorrect.
* [ ] Copy `data/results/dry_run_*_migration.json` to `/opt/congregate/data/waves/wave_<insert_wave_number>/` and attach to this issue
* [ ] Notify in the internal Slack channel dedicated to this migration you have completed dry run for the wave
* [ ] Request customer sign-off

#### Migrate group and projects

* [ ] Notify in the internal Slack channel dedicated to this migration you are starting the migration wave
* [ ] Notify the customer in the customer-facing Slack channel you are starting the migration wave
* [ ] On the destination instance set the `Default deletion adjourned period` (*Admin Panel -> Settings -> General -> Visibility and access controls*) to 0
  * This is required in order to have Congregate immediately delete projects that fail to import or import with a failed status
* [ ] Run the following command `nohup ./congregate.sh migrate --skip-users --commit > data/waves/wave_<insert_wave_number>/wave<insert-wave-here>.log 2>&1 &`
  * [ ] If only sub-groups are staged make sure to add `--subgroups-only`
* [ ] Monitor the wave periodically by running `tail -f data/waves/wave_<insert_wave_number>/wave<insert-wave-here>.log`
* [ ] Copy the following files to `/opt/congregate/data/waves/wave_<insert_wave_number>/` and attach to this issue:
  * `data/logs/congregate.log`
  * `data/logs/audit.log`
  * `data/results/group_migration_results.json`
  * `data/results/project_migration_results.json`
  * `data/results/import_failed_relations.json`
  * `data/waves/wave_<insert_wave_number>/wave<insert-wave-here>.log`
* [ ] Inspect `data/results/import_failed_relations` for any project import failed relations (missing feature info)
  * In case of missing MRs, Piplines, etc. that are critical to the customer and business:
    * [ ] Stage and rollback projects with critical failed relations
      * **NOTE:** `--skip-users` and `--skip-groups`
    * [ ] Repeat [migration](#migrate-group-and-projects)
    * [ ] Once complete, and in case of consistently missing info, discuss and request verbal or written sign-off from customer
      * [ ] Otherwise [rollback](#rollback) the entire wave and reschedule

### Post Migration of Failed Groups and Projects

For each migration attempt check if any project or group imports failed or have imported with a failed status.

* [ ] Make sure the groups and projects that failed to import or have imported with a failed status are not present on the destination instance.
  * To see projects pending deletion make sure to filter the Admin Panel's **Projects** list to **Show archived projects** (on **Sort by**)
  * If there are any manually delete them.
* [ ] Once the projects are confirmed deleted, prepare to migrate them again.
* [ ] If projects or groups are missing, confirm the projects and groups have successfully exported and confirm they don't actually exist on the destination instance
  * To confirm the exports have successfully exported, review the contents of `/opt/congregate/downloads` or the S3 bucket defined in the configuration. Make sure no export archive has a size of 42 bytes. That means the export archive is invalid.
  * To confirm the projects or groups don't actually exist on the destination instance, compare the results of the diff report and manually check where the project or group should be located.
  * To confirm the projects or groups don't actually exist on the destination instance, you may also `dry-run` a wave.
    * You can also search for the project with an API request to `/projects?search=<project-name>`
    * You can also search for the groups with an API request to `/groups?search=<group-name>` or `/groups/<url-encoded-full-path>`
* [ ] Stage _only_ those groups and projects and go through this runbook again, this time with the following command for the migration stage: `nohup ./congregate.sh migrate --skip-users --skip-group-export --skip-project-export --commit > data/waves/wave_<insert_wave_number>/wave<insert-wave-here>_attempt<insert-attempt>.log 2>&1 &`
  * [ ] If staging by group make sure to stage all sub-groups as well
  * [ ] If only sub-groups are staged make sure to add `--subgroups-only`
* [ ] Monitor the wave periodically by running `tail -f data/waves/wave_<insert_wave_number>/wave<insert-wave-here>_attempt<insert-attempt>.log`
* [ ] Notify in the internal Slack channel dedicated to this migration the migration has finished
* [ ] Notify the customer in the customer-facing Slack channel the migration wave has finished
* [ ] Copy the following files to `/opt/congregate/data/waves/wave_<insert_wave_number>/` and attach to this issue:
  * `data/logs/congregate.log`
  * `data/logs/audit.log`
  * `data/results/group_migration_results.json`
  * `data/results/project_migration_results.json`
  * `data/results/import_failed_relations.json`
  * `data/waves/wave_<insert_wave_number>/wave<insert-wave-here>.log`

#### Alternative Export/Import methods

* [Export/Import project via Rails console](https://docs.gitlab.com/ee/administration/troubleshooting/gitlab_rails_cheat_sheet.html#imports--exports)
  * [Import project via Rails console](https://docs.gitlab.com/ee/development/import_project.html#importing-via-the-rails-console)
  * [Export project repo via  Rails console](https://docs.gitlab.com/ee/administration/troubleshooting/gitlab_rails_cheat_sheet.html#export-a-repository)
* [Import project via Rake task](https://docs.gitlab.com/ee/development/import_project.html#importing-via-a-rake-task)

##### Trim or remove project CI pipelines

###### On migration VM

* Export project
* Unpack file
  * `tar -xzvf <archive_name>.tar.gz -C <target_directory>`
* Trim lines or completely remove `<archive_folder>/tree/project/ci_pipelines.ndjson`
* Pack back ONLY folder content
  * `tar -czvf <archive_name>.tar.gz -C <archive_name> .`
* Import project

###### Rails console on source

```bash
sudo gitlab-rails console
```

```ruby
# Assign project and user
[ gprd ] production> p=Project.find_by_full_path(‘<full_path>’)
=> #<Project id:<PID> <full_path>
[ gprd ] production> u=User.find_by(username: “<admin_or_owner_username>”)
=> #<User id:UID @<admin_or_owner_username>>

# Find out delete error
[ gprd ] production> p.delete_error
=> "PG::QueryCanceled: ERROR:  canceling statement due to statement timeout\n"

# Trim CI pipelines
[ gprd ] production> p.ci_pipelines.find_each(start: <oldest_pipeline_id>, finish: <latest_pipeline_id>, batch_size: <no_of_pipelines_to_remove_per_batch>, &:destroy)
=> nil
[ gprd ] production> p.ci_pipelines.count
=> <no_of_pipelines_left>

# Remove all pipelines
[ gprd ] production> p.ci_pipelines.find_each(batch_size: <no_of_pipelines_to_remove_per_batch>, &:destroy)
=> nil
[ gprd ] production> p.ci_pipelines.count
=> 0

# (WARNING) Completely remove the project
[ gprd ] production> ProjectDestroyWorker.new.perform(p.id, u.id, {})
=> true
```

#### Fallback if no container registry migrate

In the event container registries fail to migrate, there is a bash script built in to the container you can use as a backup.

The script is located at `<path_to_congregate>/dev/bin/manually_move_images.sh` (in the case of the container `/opt/congregate/dev/bin/manually_move_images.sh`)

The script usage is in the script, but here is a quick example of using the script:

```bash
sudo -E /opt/congregate/dev/bin/manually_move_images.sh registry.gitlab.com/gitlab-com/customer-success/professional-services-group/global-practice-development/migration/congregate registry.dest-gitlab.io/path/to/dest/registry/repo
```

This will migrate all containers from a single registry repository to another registry repository.

If you need to move several registry repositories, you can follow the usage of another script in `/dev/bin` called `docker_brute_force.py`.
In that script, you prepopulate all source and destination registry repositories in a list of tuples. It's hacky, but still faster than manually pulling and pushing all docker containers.

* Optional checklist
  * [ ] Confirm container registries failed to migrate and make a comment in this issue describing the failure
  * [ ] (Optional) Prep `docker_brute_force.py` to migrate several registry repositories
  * [ ] Execute the docker migration through one of the following commands:
      * `nohup sudo ./dev/bin/manually_move_images.sh <source-repo> <destination-repo> > data/waves/wave_<insert_wave_number>/wave<insert-wave-here>_attempt<insert-attempt>_manual_docker_migration.log 2>&1 &`
      * `nohup sudo ./dev/bin/docker_brute_force.py > data/waves/wave_<insert_wave_number>/wave<insert-wave-here>_attempt<insert-attempt>_manual_docker_migration.log 2>&1 &`
  * [ ] Monitor the logs as it runs
  * [ ] Once it finishes, attach the logs to this issue

### Post Migration of Failed User, Group and Project Info

* [ ] Monitor logs (and/or Slack) for failed migrations of single user, group and project features - everything Congregate additionally migrates after a user is created i.e. group and/or project imported
* [ ] In case of unexpected errors with the migration of post-import data (SSH keys, variables, reigistries, etc.):
  * [ ] Confirm those users/groups/projects are staged
  * [ ] Run `nohup ./congregate.sh migrate --only-post-migration-info --commit > data/waves/wave_<insert_wave_number>/wave<insert-wave-here>_attempt<insert-attempt>_post_migration.log 2>&1 &` to migrate any post-migration data
    * **NOTE:** `--only-post-migration-info` will implicitly skip group and project exports, but not imports and user creation

### Post Migration

* [ ] Once all the projects/groups are migrated, stitch together the various migration attempts by running `./congregate.sh stitch-results --result-type=<user|group|project> --no-of-files=<number-of-results-files-to-stitch>`
* [ ] Once the results have been stitched into a single JSON file, run the diff report on the newly created results file
* [ ] Notify in the internal Slack channel dedicated to this migration you are running the diff report
* [ ] Run `nohup ./congregate.sh generate-diff --staged > data/waves/wave_<insert_wave_number>/diff<insert-wave-here>.log 2>&1 &` to generate the various diff reports
  * **NOTE:** Make sure to have the correct `data/staged_*` and `data/results/*_results.json` files present
* [ ] Reach out the whoever has rails console access to the destination instance and have them run the following script where `group_paths` is a list of all expected full_paths for this migration wave:

```ruby
group_paths = ['root_group/group-1', 'root_group/group-2', '...']

groups = group_paths.map { |path| Group.find_by_full_path(path) }
projects = groups.map(&:projects).flatten

import_failures = projects.map(&:import_failures).flatten
import_failures_count = import_failures.count
mr_import_failures = import_failures.select { |failure| failure.relation_key == 'merge_requests' }
services_import_failures = import_failures.select { |failure| failure.relation_key == 'services' }
protected_branches_import_failures = import_failures.select { |failure| failure.relation_key == 'protected_branches' }

p "Total number of import failures: #{import_failures_count}"
p "Number of Merge Request import failures: #{mr_import_failures.count} (this figure might not be actual amount of missing MRs)"
p "Number of Services import failures: #{services_import_failures.count}"
p "Number of Protected Branches import failures: #{protected_branches_import_failures.count}"
```

* [ ] Review the diff reports (`data/results/*_results.html`) once they are finished generating
  * Review the following:
    * Overall accuracy of groups and projects
    * Individual accuracy of each group and project
    * Confirm correct group and project members are present.
    * Confirm nothing has an accuracy of 0. If an asset is missing (one of the causes of an accuracy of 0), take note of the missing asset in this issue and plan to restage it for another, smaller run of this wave
    * If the namespaces are incorrect, meaning a project or a group has been migrated to the wrong location, do the following:
      * For projects:
        * If the project is in an incorrect namespace within the parent group, move the project to the correct group
        * If the project is in a completely incorrect, random location on the destination, confirm the spread of the leaked data, and refer to the [rollback instructions](#Rollback)
      * For groups:
        * If the group is not within the expected parent group, make a note of the incorrectly migrated group in this issue, delete the group, and refer to the [rollback instructions](#Rollback)
    * If random users are present in a group or project, refer to the [rollback instructions](#Rollback).
      * Confirm these users are actually incorrect, look up the user through the API (`/api/v4/users/:id`)
* [ ] Post a comment in this issue containing the following information:
  * Projects: `<insert-overall-accuracy>`
  * Groups: `<insert-overall-accuracy>`
  * Users: `<insert-overall-accuracy>`
* [ ] If accuracy is greater than 90%, mark this migration as a success
* [ ] If accuracy is lower than 90%, review the diff reports again and see if any projects or groups are missing
* [ ] Attach `data/results/*_results.*` and `data/results/*_diff.json` to this issue
* [ ] Copy `data/results/*_results.*` and `data/results/*_diff.json` to `/opt/congregate/data/waves/wave_<insert_wave_number>/`
* [ ] Notify in the internal Slack channel dedicated to this migration the diff report is finished generating with a link to the comment you just posted. If you need to run another small subset of this migration, mention that in the Slack message as well.
* [ ] Notify the customer in the customer-facing Slack channel the migration wave has finished

### Archive Staged Projects

* [ ] Upon successfull migration and diff report discuss with customer when to archive staged projects on source
* [ ] Notify the customer in the customer-facing Slack channel you are archiving projects on source
* [ ] Run `nohup ./congregate.sh archive-staged-projects --commit > data/waves/user_wave/archive.log 2>&1 &`
  * **NOTE:** Make sure to have the correct `data/staged_projects` file present

### Rollback

If **any** data was migrated incorrectly (i.e. to the wrong namespace), you **must** rollback the migration wave **completely**

#### Users

* [ ] Notify in the internal Slack channel dedicated to this migration you are running a rollback due to an issue with the migration
* [ ] Dry run `nohup ./congregate.sh rollback --hard-delete --skip-groups --skip-projects > data/waves/user_wave/rollback_dry_run.log 2>&1 &`
  * **NOTE:** `--hard-delete` will also remove user contributions
* [ ] Live run `nohup ./congregate.sh rollback --hard-delete --skip-groups --skip-projects --commit > data/waves/user_wave/rollback.log 2>&1 &`
* [ ] Copy `data/logs/congregate.log` and `data/logs/audit.log` to `/opt/congregate/data/waves/user_wave/`
* [ ] Post a comment describing the reason for the rollback and attach the rollback log and `data/logs/audit.log`

#### Groups and projects

* [ ] Make sure groups and projects can be immediately deleted
  * **Group Settings:** *Group -> Settings -> General -> Permissions*
  * **Instance Settings:** *Admin Area -> Settings -> General -> Visibility and access controls*
* [ ] Notify in the internal Slack channel dedicated to this migration you are running a rollback due to an issue with the migration
* [ ] Dry run `nohup ./congregate.sh rollback --skip-users > data/waves/wave_<insert_wave_number>/rollback_dry_run.log 2>&1 &`
* [ ] Live run `nohup ./congregate.sh rollback --skip-users --commit > data/waves/wave_<insert_wave_number>/rollback.log 2>&1 &`
* [ ] Copy `data/logs/congregate.log` and `data/logs/audit.log` to `/opt/congregate/data/waves/wave_<insert_wave_number>/`
* [ ] Post a comment describing the reason for the rollback and attach the rollback log and `data/logs/audit.log`

/confidential
