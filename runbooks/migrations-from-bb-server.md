<!-- 
    Copy the contents of this runbook into an issue when running through a migration wave.
    Post the link to the issue on the Slack channel dedicated to this migration. 
-->

# <customer name> Migration Wave <insert-number-here>

This runbook covers the process of migrating a wave of **groups and projects** from a source BitBucket Server instance to a GitLab instance (gitlab.com or self-managed).

## Migration Blackout Period

<!--
    Specify the date and time of this migration wave. For example

    3:00PM 4/13/20 - 3:00AM 4/14/20
-->

## Slack channel for communication

<!--
    Provide the name and link of the Slack channel dedicated to communicating the status and events of the migration
-->

## Points of contact

<!--
    Provide the gitlab handles for the various people involved in this migration wave and their specific role in the migration. 
    
    For example:

    @leopardm: PSE conducting the migration
    @lyle: Support Manager with Rails Console access
    @pharrison: Security Manager in the loop in case anything goes wrong
-->

## BitBucket Projects (GitLab Groups) to migrate

### Legend

* :x: = not started
* :heavy_minus_sign: = in progress (optional)
* :white_check_mark: = finished

<!--

Quick reference:

BitBucket Project = GitLab Group
BitBucket Repo = GitLab Project

Copy the following data and add subsequent columns for wave migration or nested project migration

| Completed | Project Name | Total Repos   | Project Size   |
| --------- | ---------- | ---------------- | ------------ |
| :x:       | [name]     | [total-Repos] | [project-size] |

Copy the following data and add subsequent columns for single project migration

| Completed | Repo Path | Repo Size        |
| --------- | ------------ | ---------------- |
| :x:       | [name]       | [total-Repos] |

-->

## Professional Services Steps to Complete Migration Wave

### Pre-migration checklist

* [ ] PSE conducting the migration has acquired a BitBucket Server personal access token with admin privileges (top right icon in BB server -> Manage Account -> Personal Access Tokens)
* [ ] PSE conducting the migration has acquired an admin token for GitLab (top right icon in GitLab -> Settings -> Access Tokens)
* [ ] PSE has configured congregate to migrate from BitBucket Server to gitlab.com

### User migration

#### Preparation

* [ ] Review migration schedule (see customer migration schedule)
* [ ] Check the status of **gitlab.com** (https://status.gitlab.com/)
  * [ ] Confirm you can reach the UI of the instance
  * [ ] Confirm you can reach the API through cURL or a REST client
* [ ] Run `congregate list` at the beginning of the migration blackout period
* [ ] Stage ALL users
  * [ ] **Make sure no groups and projects are staged**
* [ ] Create a directory called "waves" in `/opt/congregate/data` in the container if it doesn't already exist
* [ ] Create a directory called `user_wave` in `/opt/congregate/data/waves` if it doesn't already exist
* [ ] Copy `data/staged_users.json` to `/opt/congregate/data/waves/user_wave`
* [ ] Lookup whether the staged users (emails) already exist on the destination by running `./congregate.sh search-for-staged-users`
  * This will output a list of FOUND, NOT FOUND and DUPLICATE user `email`, along with their `id` and `state`
* [ ] Determine with customer how to configure:
  * `group_sso_provider` and `group_sso_provider_pattern`, if they are using SSO
  * `keep_blocked_users` (`False` by default),
  * `reset_pwd` (`True` by default),
  * `force_rand_pwd` (`False` by default)
* By default blocked users are skipped during user migration. To be sure they are removed from staged users, groups and projects run the following command:
  * [ ] Dry run: `./congregate.sh remove-blocked-users`
  * [ ] Live: `./congregate.sh remove-blocked-users --commit`
* [ ] Notify in the internal Slack channel dedicated to this migration you have completed preparation for the user wave

#### Dry run

* [ ] Run the following command: `nohup ./congregate.sh migrate > data/waves/user_wave/user_wave_dry_run.log 2>&1 &`
  * **NOTE:** The command assumes you have no groups or projects staged
* [ ] Confirm everything looks correct and move on to the next step in the runbook
  * Specifically, review the API requests and make sure the paths look correct.
  * If anything looks wrong in the dry run, make a note of it in the issue and reach out to @pprokic or @leopardm for review. Do not proceed with the migration if the dry run data looks incorrect. If this is incorrect, the data we send will be incorrect.
* [ ] Attach the dry run log (`data/dry_run_user_migration.json`) to this issue
* [ ] Copy the dry run log to `/opt/congregate/data/waves/user_wave/`
* [ ] Notify in the internal Slack channel dedicated to this migration you have completed dry run for the user wave

#### Migration

* [ ] Notify in the internal Slack channel dedicated to this migration you are starting the user migration wave
* [ ] Notify the customer in the customer-facing Slack channel you are starting the user migration wave
* **NOTE:** The command below assumes you have no groups or projects staged
* [ ] Run the following command `nohup ./congregate.sh migrate --commit > data/waves/user_wave/user_wave.log 2>&1 &`
* [ ] Monitor the wave periodically by running `tail -f data/waves/user_wave/user_wave.log`
* [ ] Attach `data/congregate.log`, `data/audit.log`, and `data/waves/user_wave/user_wave.log` to this issue
* [ ] Copy `data/congregate.log`, `data/audit.log`, and `data/waves/user_wave/user_wave.log` to `/opt/congregate/data/waves/user_wave/`

### Group and project migration

#### Preparation

* [ ] Review migration schedule (see customer migration schedule)
* [ ] Check the status of **gitlab.com** (https://status.gitlab.com/)
  * [ ] Confirm you can reach the UI of the instance
  * [ ] Confirm you can reach the API through cURL or a REST client
* [ ] Run `congregate list` at the beginning of the migration blackout period
* [ ] Stage groups or projects based on the wave schedule in the UI
* [ ] Create a directory called "waves" in `/opt/congregate/data` in the container if it doesn't already exist
* [ ] Create a directory called `wave_<insert_wave_number>` in `/opt/congregate/data/waves` if it doesn't already exist
* [ ] Copy all staged data to `/opt/congregate/data/waves/wave_<insert_wave_number>/`
* [ ] Notify in the internal Slack channel dedicated to this migration you have completed preparation for the wave

#### Dry run

* [ ] Run the following command: `nohup ./congregate.sh migrate --skip-users > data/waves/wave_<insert_wave_number>/wave_<insert_wave_number>_dry_run.log 2>&1 &`
* [ ] Confirm everything looks correct and move on to the next step in the runbook
  * Specifically, review the API requests and make sure the paths look correct. For example, make sure any parent IDs or namespaces are matching the parent ID and parent namespaces we have specified in the congregate config.
  * If anything looks wrong in the dry run, make a note of it in the issue and reach out to @pprokic or @leopardm for review. Do not proceed with the migration if the dry run data looks incorrect. If this is incorrect, the data we send will be incorrect.
* [ ] Attach the dry run logs (`data/dry_run_*_migration.json`) to this issue
* [ ] Copy the dry run logs to `/opt/congregate/data/waves/wave_<insert_wave_number>/`
* [ ] Notify in the internal Slack channel dedicated to this migration you have completed dry run for the wave

#### Migration

* [ ] Notify in the internal Slack channel dedicated to this migration you are starting the migration wave
* [ ] Notify the customer in the customer-facing Slack channel you are starting the migration wave
* [ ] Run the following command `nohup ./congregate.sh migrate --skip-users --commit > data/waves/wave_<insert_wave_number>/wave<insert-wave-here>.log 2>&1 &`
* [ ] Monitor the wave periodically by running `tail -f data/waves/wave_<insert_wave_number>/wave<insert-wave-here>.log`
* [ ] Attach `data/congregate.log`, `data/audit.log`, and `data/waves/wave_<insert_wave_number>/wave<insert-wave-here>.log` to this issue
* [ ] Copy `data/congregate.log`, `data/audit.log`, and `data/waves/wave_<insert_wave_number>/wave<insert-wave-here>.log` to `/opt/congregate/data/waves/wave_<insert_wave_number>/`

### Post Migration of Failed Groups and Projects

#### Migration of Failed Groups and Projects

For each migration attempt check if any project or group imports failed or have imported with failed status.

* [ ] Reach out to `Support` to delete the failed/partially imported projects. Provide the full path to the project. provided in the project migration results
* [ ] Once the projects are confirmed deleted, prepare to migrate them again.
* [ ] If projects or groups are missing, confirm the projects and groups have successfully exported and confirm they don't actually exist on the destination instance
  * To confirm the exports have successfully exported, review the contents of `/opt/congregate/downloads` or the S3 bucket defined in the configuration. Make sure no export archive has a size of 42 bytes. That means the export archive is invalid.
  * To confirm the projects or groups don't actually exist on the destination instance, compare the results of the diff report and manually check where the project or group should be located.
  * To confirm the projects or groups don't actually exist on the destination instance, you may also `dry-run` a wave.
    * You can also search for the project with an API request to `/projects?search=<project-name>`
    * You can also search for the groups with an API request to `/groups?search=<group-name>` or `/groups/<url-encoded-full-path>`
* [ ] Stage _only_ those groups and projects and go through this runbook again, this time with the following command for the migration stage: `nohup ./congregate.sh migrate --skip-users --commit > data/waves/wave_<insert_wave_number>/wave<insert-wave-here>_attempt<insert-attempt>.log 2>&1 &`
* [ ] Monitor the wave periodically by running `tail -f data/waves/wave_<insert_wave_number>/wave<insert-wave-here>_attempt<insert-attempt>.log`
* [ ] Notify in the internal Slack channel dedicated to this migration the migration has finished
* [ ] Notify the customer in the customer-facing Slack channel the migration wave has finished
* [ ] Attach `data/congregate.log`, `data/audit.log`, and `data/waves/wave_<insert_wave_number>/wave<insert-wave-here>_attempt<insert-attempt>.log` to this issue
* [ ] Copy `data/congregate.log`, `data/audit.log`, and `data/waves/wave_<insert_wave_number>/wave<insert-wave-here>_attempt<insert-attempt>.log` to `/opt/congregate/data/waves/wave_<insert_wave_number>/`

<!-- TO DO: No diff reports exist for BB server at this time

### Post Migration

* [ ] Once all the projects/groups are migrated, stitch together the various migration attempts by running `./congregate.sh stitch-results --result-type=<user|group|project> --no-of-files=<number-of-results-files-to-stitch>`
* [ ] Once the results have been stitched into a single JSON file, run the diff report on the newly created results file
* [ ] Notify in the internal Slack channel dedicated to this migration you are running the diff report
* [ ] Run `nohup ./congregate.sh generate-diff --staged > data/waves/wave_<insert_wave_number>/diff<insert-wave-here>.log 2>&1 &` to generate the various diff reports
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

* [ ] Review the diff reports (`data/*_results.html`) once they are finished generating
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
* [ ] Attach `data/*_results.*` and `data/*_diff.json` to this issue
* [ ] Copy `data/*_results.*` and `data/*_diff.json` to `/opt/congregate/data/waves/wave_<insert_wave_number>/`
* [ ] Notify in the internal Slack channel dedicated to this migration the diff report is finished generating with a link to the comment you just posted. If you need to run another small subset of this migration, mention that in the Slack message as well.
* [ ] Notify the customer in the customer-facing Slack channel the migration wave has finished

-->

### Rollback

If **any** data was migrated incorrectly (i.e. to the wrong namespace), you **must** rollback the migration wave **completely**

#### Users

* [ ] Notify in the internal Slack channel dedicated to this migration you are running a rollback due to an issue with the migration
* [ ] Dry run `nohup ./congregate.sh rollback --hard-delete --skip-groups --skip-projects > data/waves/user_wave/rollback_dry_run.log 2>&1 &`
  * **NOTE:** `--hard-delete` will also remove user contributions
* [ ] Live run `nohup ./congregate.sh rollback --hard-delete --skip-groups --skip-projects --commit > data/waves/user_wave/rollback.log 2>&1 &`
* [ ] Copy `data/congregate.log` and `data/audit.log` to `/opt/congregate/data/waves/user_wave/`
* [ ] Post a comment describing the reason for the rollback and attach the rollback log and `data/audit.log`
* [ ] Follow these [instructions in the handbook](https://about.gitlab.com/handbook/engineering/security/#engaging-the-security-on-call) and link to this issue.

#### Groups and projects

* [ ] Notify in the internal Slack channel dedicated to this migration you are running a rollback due to an issue with the migration
* [ ] Dry run `nohup ./congregate.sh rollback --skip-users > data/waves/wave_<insert_wave_number>/rollback_dry_run.log 2>&1 &`
* [ ] Live run `nohup ./congregate.sh rollback --skip-users --commit > data/waves/wave_<insert_wave_number>/rollback.log 2>&1 &`
* [ ] Copy `data/congregate.log` and `data/audit.log` to `/opt/congregate/data/waves/wave_<insert_wave_number>/`
* [ ] Post a comment describing the reason for the rollback and attach the rollback log and `data/audit.log`
* [ ] Follow these [instructions in the handbook](https://about.gitlab.com/handbook/engineering/security/#engaging-the-security-on-call) and link to this issue.

/confidential
