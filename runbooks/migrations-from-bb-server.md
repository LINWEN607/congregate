<!--
    Copy the contents of this runbook into an issue when running through a migration wave.
    Post the link to the issue on the Slack channel dedicated to this migration.
-->

# <customer name> Migration Wave <insert-number-here>

This runbook covers the process of migrating a wave of **groups and projects** from a source BitBucket Server instance to a GitLab instance (gitlab.com or self-managed).

## Migration Blackout Period

<!--
    Specify the date and time of this migration wave. For example

    3:00PM 2020-09-07 - 3:00AM 2020-09-07
-->
📅

## Slack channel for communication

<!--
    Provide the name and link of the Slack channel dedicated to communicating the status and events of the migration
-->

## Points of contact

<!-- PLEASE REMOVE BLOCK AFTER POPULATING TO AVOID TAGGING PEOPLE THAT SHOULD NOT BE INVOLVED
    Provide the gitlab handles for the various people involved in this migration wave and their specific role in the migration.

    You must provide the following roles:
    - PSE conducting the migration
    - SIRT group assigning an on-call Security engineer during the migration period
    - Infra managers group assigning an SRE during the migration period
    - Support managers group assigning a Support engineer during the migration period

    Optional roles to provide:
    - Backup PSE if the migration period spans several hours
    - .com Support Engineer with rails console access for their awareness
    - PS manager for their awareness

    For example:

    ### GitLab

    * @<username>: PSE conducting the migration
    * (gitlab.com) @gitlab-com/gl-security/security-operations/sirt: SIRT engineers responding to gitlab.com alerts e.g. Admin user impersonations
    * (gitlab.com) @gitlab-com/gl-infra/managers: Infra managers that are aware of the migration and assigning an SRE during the migration period
    * (gitlab.com) @gitlab-com/support/managers: Support managers that are aware of the migration and assigning a Support engineer during the migration period

    ### <Customer>

    * @<username>: Customer point of contact
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

| Completed | Project Name   | Total Repos     | Project Size    |
| --------- | -------------- | --------------- | --------------- |
| :x:       | [name]         | [total-Repos]   | [project-size]  |
| **Total** | [total-number] | [sum-of-column] | [sum-of-column] |

Copy the following data and add subsequent columns for single project migration

| Completed | Repo Path | Repo Size     |
| --------- | --------- | ------------- |
| :x:       | [name]    | [total-Repos] |

-->

## Professional Services Steps to Complete Migration Wave

### Pre-migration checklist

* PSE conducting the migration:
  * [ ] Acquires a BitBucket Server account with `SYS_ADMIN` or `ADMIN` privileges
    * **NOTE:** Unverified alternatives are [app passwords](https://bitbucket.org/blog/deprecating-atlassian-account-password-for-bitbucket-api-and-git-activity) and [HTTP access tokens](https://confluence.atlassian.com/bitbucketserver/personal-access-tokens-939515499.html) (as of version 8)
  * [ ] Acquires the obfuscated (`congregate obfuscate`) BitBucket Server account password as `src_access_token`
  * [ ] Acquires a GitLab Admin token (top right icon in *GitLab -> Settings -> Access Tokens*) with `api` scope
  * [ ] [Configures Congregate](/docs/full_setup.md) to migrate from BitBucket Server to GitLab
    * [ ] Inspects and validates configured values in `data/congregate.conf`
      * **Tip:** Run `./congregate.sh validate-config`

### User migration

<details><summary>Instructions for user migration collapsed by default.</summary>

#### Prepare users

* [ ] Review migration schedule (see customer migration schedule)
* [ ] **(gitlab.com)** Check the [status of **gitlab.com**](https://status.gitlab.com)
  * [ ] Confirm you can reach the UI of the instance
  * [ ] Confirm you can reach the API through cURL or a REST client
* [ ] Run `congregate list` at the beginning of the migration blackout period
  * **NOTE:** Discuss the [permission mapping](/customer/famq.md#how-do-bitbucket-user-permissions-and-roles-map-to-gitlab) with customer to see if it requires adjustment
* [ ] Stage ALL users
  * **NOTE:** Make sure no groups and projects are staged
  * Determine (with customer) whether user ID 1 is a regular user that should be migrated
* [ ] Create a directory called "waves" in `/opt/congregate/data` in the container if it doesn't already exist
* [ ] Create a directory called `user_wave` in `/opt/congregate/data/waves` if it doesn't already exist
* [ ] Copy `data/staged_users.json` to `/opt/congregate/data/waves/user_wave`
* [ ] Lookup whether the staged users (emails) already exist on the destination by running `./congregate.sh search-for-staged-users`
  * This will output a list of user metadata, based on `email`, along with other stats
  * Add argument `--table` to command to save this output to `data/user_stats.csv`
* [ ] Determine with customer how to configure:
  * `group_sso_provider` and `group_sso_provider_pattern`, if they are using SSO
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
  * If anything looks wrong in the dry run, make a note of it in the issue and reach out to `@gitlab-org/professional-services-automation/tools/migration` for review. Do not proceed with the migration if the dry run data looks incorrect. If this is incorrect, the data we send will be incorrect.
* [ ] Copy `data/results/dry_run_user_migration.json` to `/opt/congregate/data/waves/user_wave/` and attach to this issue
* [ ] Notify in the internal Slack channel dedicated to this migration you have completed dry run for the user wave

#### Migrate users

* [ ] Notify in the internal Slack channel dedicated to this migration you are starting the user migration wave
* [ ] Notify the customer in the customer-facing Slack channel you are starting the user migration wave
* **NOTE:** The command below assumes you have no groups or projects staged
* [ ] Run the following command `nohup ./congregate.sh migrate --commit > data/waves/user_wave/user_wave.log 2>&1 &`
* [ ] Monitor the wave periodically by running `tail -f data/waves/user_wave/user_wave.log`
* [ ] Copy the following files to `/opt/congregate/data/waves/user_wave/` and attach to this issue:
  * `data/logs/congregate.log`
  * `data/logs/audit.log`
  * `data/waves/user_wave/user_wave.log`

</details>

### Group and project migration

#### Prepare groups and projects

* [ ] Review migration schedule (see customer migration schedule)
* [ ] **(gitlab.com)** Check the [status of **gitlab.com**](https://status.gitlab.com)
  * [ ] Confirm you can reach the UI of the instance
  * [ ] Confirm you can reach the API through cURL or a REST client
* [ ] Run `congregate list` at the beginning of the migration blackout period
* [ ] Stage groups or projects based on the wave schedule in the UI
* [ ] Create a directory called "waves" in `/opt/congregate/data` in the container if it doesn't already exist
* [ ] Create a directory called `wave_<insert_wave_number>` in `/opt/congregate/data/waves` if it doesn't already exist
* [ ] Copy all staged data to `/opt/congregate/data/waves/wave_<insert_wave_number>/`
* [ ] Notify in the internal Slack channel dedicated to this migration you have completed preparation for the wave

#### Dry run groups and projects

* [ ] Run the following command: `nohup ./congregate.sh migrate --skip-users > data/waves/wave_<insert_wave_number>/wave_<insert_wave_number>_dry_run.log 2>&1 &`
* [ ] Confirm everything looks correct and move on to the next step in the runbook
  * Specifically, review the API requests and make sure the paths look correct. For example, make sure any parent IDs or namespaces are matching the parent ID and parent namespaces we have specified in the congregate config.
  * If anything looks wrong in the dry run, make a note of it in the issue and reach out to `@gitlab-org/professional-services-automation/tools/migration` for review. Do not proceed with the migration if the dry run data looks incorrect. If this is incorrect, the data we send will be incorrect.
* [ ] Copy `data/results/dry_run_*_migration.json` to `/opt/congregate/data/waves/wave_<insert_wave_number>/` and attach to this issue
* [ ] Notify in the internal Slack channel dedicated to this migration you have completed dry run for the wave

#### Migrate group and projects

* [ ] Notify in the internal Slack channel dedicated to this migration you are starting the migration wave
* [ ] Notify the customer in the customer-facing Slack channel you are starting the migration wave
* [ ] Run the following command `nohup ./congregate.sh migrate --skip-users --commit > data/waves/wave_<insert_wave_number>/wave<insert-wave-here>.log 2>&1 &`
* [ ] Monitor the wave periodically by running `tail -f data/waves/wave_<insert_wave_number>/wave<insert-wave-here>.log`
* [ ] Copy the following files to `/opt/congregate/data/waves/wave_<insert_wave_number>/` and attach to this issue:
  * `data/logs/congregate.log`
  * `data/logs/audit.log`
  * `data/waves/wave_<insert_wave_number>/wave<insert-wave-here>.log`

### Post Migration of Failed Groups and Projects

<details><summary>Instructions for post migration of failed groups and projects collapsed by default.</summary>

#### Migration of Failed Groups and Projects

For each migration attempt check if any project or group imports failed or have imported with failed status.

* [ ] Reach out to `Support` to delete the failed/partially imported projects. Provide the full path to the project. provided in the project migration results
* [ ] Once the projects are confirmed deleted, prepare to migrate them again.
* [ ] If projects or groups are missing, confirm the projects and groups have successfully exported and confirm they don't actually exist on the destination instance
  * To confirm the exports have successfully exported, review the contents of `/opt/congregate/downloads` or the S3 bucket defined in the configuration. Make sure no export archive has a size of 42 bytes. That means the export archive is invalid.
  * To confirm the projects or groups don't actually exist on the destination instance, you may also `dry-run` a wave.
    * You can also search for the project with an API request to `/projects?search=<project-name>`
    * You can also search for the groups with an API request to `/groups?search=<group-name>` or `/groups/<url-encoded-full-path>`
* [ ] Stage _only_ those groups and projects and go through this runbook again, this time with the following command for the migration stage: `nohup ./congregate.sh migrate --skip-users --commit > data/waves/wave_<insert_wave_number>/wave<insert-wave-here>_attempt<insert-attempt>.log 2>&1 &`
* [ ] Monitor the wave periodically by running `tail -f data/waves/wave_<insert_wave_number>/wave<insert-wave-here>_attempt<insert-attempt>.log`
* [ ] Notify in the internal Slack channel dedicated to this migration the migration has finished
* [ ] Notify the customer in the customer-facing Slack channel the migration wave has finished
* [ ] Copy the following files to `/opt/congregate/data/waves/wave_<insert_wave_number>/` and attach to this issue:
  * `data/logs/congregate.log`
  * `data/logs/audit.log`
  * `data/waves/wave_<insert_wave_number>/wave<insert-wave-here>.log`

#### Alternative Import methods

* [Export/Import project via Rails console](https://docs.gitlab.com/ee/administration/troubleshooting/gitlab_rails_cheat_sheet.html#imports--exports)
  * [Import project via Rails console](https://docs.gitlab.com/ee/development/import_project.html#importing-via-the-rails-console)
* [Import project via Rake task](https://docs.gitlab.com/ee/development/import_project.html#importing-via-a-rake-task)

</details>

### Post Migration

* [ ] Once all the projects/groups are migrated, stitch together the various migration attempts by running `./congregate.sh stitch-results --result-type=<user|group|project> --no-of-files=<number-of-results-files-to-stitch>`
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

### Archive Staged Projects

* [ ] Upon successfull migration and diff report discuss with customer when to archive staged projects on source
* [ ] Notify the customer in the customer-facing Slack channel you are archiving projects on source
* [ ] Run `nohup ./congregate.sh set-bb-read-only-branch-permissions --bb-projects --commit > data/waves/wave_<insert_wave_number>/archive.log 2>&1 &`
  * **NOTE:** Make sure to have the correct `data/staged_projects` file present

### Rollback

<details><summary>If <b>any</b> data was migrated incorrectly (i.e. to the wrong namespace), you <b>must</b> rollback the migration wave <b>completely</b>. Section collapsed by default.</summary>

#### Users

* [ ] Notify in the internal Slack channel dedicated to this migration you are running a rollback due to an issue with the migration
* [ ] Dry run `nohup ./congregate.sh rollback --hard-delete --skip-groups --skip-projects > data/waves/user_wave/rollback_dry_run.log 2>&1 &`
  * **NOTE:** `--hard-delete` will also remove user contributions
* [ ] Live run `nohup ./congregate.sh rollback --hard-delete --skip-groups --skip-projects --commit > data/waves/user_wave/rollback.log 2>&1 &`
* [ ] Copy `data/logs/congregate.log` and `data/logs/audit.log` to `/opt/congregate/data/waves/user_wave/`
* [ ] Post a comment describing the reason for the rollback and attach the rollback log and `data/logs/audit.log`
* [ ] Follow these [instructions in the handbook](https://about.gitlab.com/handbook/engineering/security/#engaging-the-security-on-call) and link to this issue.

#### Groups and projects

* [ ] Notify in the internal Slack channel dedicated to this migration you are running a rollback due to an issue with the migration
* [ ] Dry run `nohup ./congregate.sh rollback --skip-users > data/waves/wave_<insert_wave_number>/rollback_dry_run.log 2>&1 &`
* [ ] Live run `nohup ./congregate.sh rollback --skip-users --commit > data/waves/wave_<insert_wave_number>/rollback.log 2>&1 &`
* [ ] Copy `data/logs/congregate.log` and `data/logs/audit.log` to `/opt/congregate/data/waves/wave_<insert_wave_number>/`
* [ ] Post a comment describing the reason for the rollback and attach the rollback log and `data/logs/audit.log`
* [ ] Follow these [instructions in the handbook](https://about.gitlab.com/handbook/engineering/security/#engaging-the-security-on-call) and link to this issue.

</details>

/confidential
