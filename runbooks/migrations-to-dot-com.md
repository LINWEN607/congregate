<!-- 
    Copy the contents of this runbook into an issue when running through a migration wave.
    Post the link to the issue on the Slack channel dedicated to this migration. 
-->

# <customer name> Migration Wave <insert-number-here>

This runbook covers the process of migrating a wave of **groups and projects** from a source GitLab instance to **gitlab.com**.

**NOTE**: This issue **must** be created [5 days in advance](https://about.gitlab.com/handbook/support/workflows/importing_projects.html#import-scheduled) of executing the migration wave.

## Migration Blackout Period

<!--
    Specify the date and time of this migration wave. For example

    3:00PM 2020-09-07 - 3:00AM 2020-09-08
-->

## Slack channel for communication

<!--
    Provide the name and link of the Slack channel dedicated to communicating the status and events of the migration
-->

## Points of contact

<!--
    Provide the gitlab handles for the various people involved in this migration wave and their specific role in the migration. 

    You must provide the following roles:
    - PSE conducting the migration
    - On-call security engineer working during the migration period
    - Infra managers group assigning the SRE working during the migration period

    Optional roles to provide:
    - Backup PSE if the migration period spans several hours
    - .com Support Engineer with rails console access for their awareness
    - PS manager for their awareness
    
    For example:

    @leopardm: PSE conducting the migration
    @pharrison: Security Manager in the loop in case anything goes wrong
    @gitlab-com/gl-infra/managers: Infra managers that are aware of the migration and assigning the SRE during the migration period
    @lyle: Support Manager with Rails Console access
-->

## Groups to migrate

### Legend

* :x: = not started
* :heavy_minus_sign: = in progress (optional)
* :white_check_mark: = finished

<!--
Copy the following data and add subsequent columns for wave migration or nested group migration

| Completed | Group Name | Total Projects   | Group Size   |
| --------- | ---------- | ---------------- | ------------ |
| :x:       | [name]     | [total-projects] | [group-size] |

Copy the following data and add subsequent columns for single group migration

| Completed | Project Path | Repo Size        |
| --------- | ------------ | ---------------- |
| :x:       | [name]       | [total-projects] |
-->

## Professional Services Steps to Complete Migration Wave

### User migration

#### Preparation

* [ ] Review migration schedule (see customer migration schedule)
* [ ] Check the status of **gitlab.com** (https://status.gitlab.com/)
  * [ ] Confirm you can reach the UI of the instance
  * [ ] Confirm you can reach the API through cURL or a REST client
  * [ ] Confirm the import (Admin) user is a member of the SAML+SSO enforced group
  * [ ] If not and late notice, as a workaround:
    * [ ] Discuss with customer whether it's possible to disable SSO enforced during user migration OR
    * [ ] Reach out to #support_gitlab-com to spoof adding the user to the SAML+SSO enforced group
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
* [ ] Stage _only_ those groups and projects and go through this runbook again, this time with the following command for the migration stage: `nohup ./congregate.sh migrate --skip-users --skip-group-export --skip-project-export --commit > data/waves/wave_<insert_wave_number>/wave<insert-wave-here>_attempt<insert-attempt>.log 2>&1 &`
* [ ] Monitor the wave periodically by running `tail -f data/waves/wave_<insert_wave_number>/wave<insert-wave-here>_attempt<insert-attempt>.log`
* [ ] Notify in the internal Slack channel dedicated to this migration the migration has finished
* [ ] Notify the customer in the customer-facing Slack channel the migration wave has finished
* [ ] Attach `data/congregate.log`, `data/audit.log`, and `data/waves/wave_<insert_wave_number>/wave<insert-wave-here>_attempt<insert-attempt>.log` to this issue
* [ ] Copy `data/congregate.log`, `data/audit.log`, and `data/waves/wave_<insert_wave_number>/wave<insert-wave-here>_attempt<insert-attempt>.log` to `/opt/congregate/data/waves/wave_<insert_wave_number>/`

#### SRE Support Import of Failed Groups and Projects

If a project or group import continues to fail (2 retries max), you'll need to create an infrastructure issue to get the project imported.

* Preparation
  * [ ] Before coming to the conclusion that an infra issue is needed to import the project, examine the contents of the project on the source.
  * [ ] Take note of any environments, CI/CD variables, merge request approvers, and container registries and see if any of those are present. If they are, you will need to run another command to get that data to the destination.
  * [ ] Upload the project export file to google drive and get a shareable link.
* Create an import issue **per project**
  * [ ] Create a new issue in the [infrastructure](https://gitlab.com/gitlab-com/gl-infra/infrastructure/-/issues) project using the [Project import](https://gitlab.com/gitlab-com/gl-infra/infrastructure/-/blob/master/.gitlab/issue_templates/Project%20Import.md) template.
  * [ ] Walk through the steps on the template to provide all necessary information
  * [ ] When providing a list of user emails, you can extract the project export tar.gz and run the following command to get a list of emails (make sure you have `jq` installed):
    * [ ] JSON: `cat project.json | jq -r '.project_members' | jq -r '.[] | .user | .email'`
    * [ ] NDJON: `cat tree/project/project_members.ndjson | jq -r '.user | .email'`
  * [ ] All predefined issue settings are at the bottom (e.g. labels, assignees, etc.) so go ahead and submit the issue.
  * (**optional**) Reach out to the Infra managers on Slack in #infrastructure-lounge by mentioning the issue.
  * [ ] Make sure to check off all checkboxes listed under Support in the import issue. We are Support in this instance.
  * [ ] Once the assignee confirms the import has started, promptly delete the project from google drive.
* Post Import. **The assignee will let you know when the import is complete.**
* If any projects imported by the assignee require any post-migration data to be migrated:
  * [ ] Confirm those projects are staged
  * [ ] Run `nohup ./congregate.sh migrate --only-post-migration-info --commit > data/waves/wave_<insert_wave_number>/wave<insert-wave-here>_attempt<insert-attempt>_post_migration.log 2>&1 &` to migrate any post-migration data
    * [ ] Skip users, groups (exports) and projects (exports) if needed

#### Fallback if no container registry migrate

In the event container registries fail to migrate, there is a bash script built in to the container you can use as a backup.

The script is located at `<path_to_congregate>/dev/bin/manually_move_images.sh` (in the case of the container `/opt/congregate/dev/bin/manually_move_images.sh`)

The script usage is in the script, but here is a quick example of using the script:

```bash
sudo -E /opt/congregate/dev/bin/manually_move_images.sh registry.gitlab.com/gitlab-com/customer-success/tools/congregate registry.dest-gitlab.io/path/to/dest/registry/repo
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

* [ ] Inspect logs (and/or Slack) for failed migrations of single user, group and project info - everything Congregate additionally migrates after a user is created i.e. group and/or project imported
* [ ] In case of unexpected errors with the migration of post-import data (SSH keys, variables, reigistries, etc.):
  * [ ] Confirm those users/groups/projects are staged
  * [ ] Run `nohup ./congregate.sh migrate --only-post-migration-info --commit > data/waves/wave_<insert_wave_number>/wave<insert-wave-here>_attempt<insert-attempt>_post_migration.log 2>&1 &` to migrate any post-migration data
    * Skip users, groups (exports) and projects (exports) if needed

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

* [ ] Make sure groups and projects can be immediately deleted
  * **Group Settings:** *Group -> Settings -> General -> Permissions*
  * **Instance Settings:** *Admin Area -> Settings -> General -> Visibility and access controls*
* [ ] If not, inform the Support Manager with Rails Console access in order to delete them before proceeding
* [ ] Notify in the internal Slack channel dedicated to this migration you are running a rollback due to an issue with the migration
* [ ] Dry run `nohup ./congregate.sh rollback --skip-users > data/waves/wave_<insert_wave_number>/rollback_dry_run.log 2>&1 &`
* [ ] Live run `nohup ./congregate.sh rollback --skip-users --commit > data/waves/wave_<insert_wave_number>/rollback.log 2>&1 &`
* [ ] Copy `data/congregate.log` and `data/audit.log` to `/opt/congregate/data/waves/wave_<insert_wave_number>/`
* [ ] Post a comment describing the reason for the rollback and attach the rollback log and `data/audit.log`
* [ ] Follow these [instructions in the handbook](https://about.gitlab.com/handbook/engineering/security/#engaging-the-security-on-call) and link to this issue.

/confidential
