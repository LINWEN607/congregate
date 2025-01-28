[TOC]


# Migration Wave

This runbook covers the process of migrating a wave of **groups and projects** from a source GitHub.com instance to **GitLab.com**.

## Slack channel for communication

* Customer shared channel
* For GitLab PSE, there is an internal dedicated channel for discussion and alerts

## Points of contact

* Get list of main point of contact from Customer during the Migration window

## Groups to migrate

### Legend

* :x: = not started
* :heavy_minus_sign: = in progress (optional)
* :white_check_mark: = finished

## Professional Services Steps to Complete Migration Wave

### Pre-migration checklist

* PSE conducting the migration:
  * [ ] Acquires an obfuscated (`./congregate.sh obfuscate`) Github Org personal access token with owner privileges. [Reference link](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
    * [ ] Steps:
      * [ ] In the upper-right corner of any page, click your profile photo, then click **Settings**.
      * [ ] In the left sidebar, click **Developer settings**.
      * [ ] In the left sidebar, under **Personal access tokens**, click **Fine-grained tokens**.
      * [ ] Click **Generate new token**.
        * Under **Token name**, enter a name for the token.
        * Under **Expiration**, select an expiration for the token.
        * Optionally, under **Description**, add a note to describe the purpose of the token.
  * [ ] Acquires an obfuscated (`./congregate.sh obfuscate`) GitLab.com Admin token with `api` scope by raising an _Issue_ in [Access request](https://gitlab.com/gitlab-com/team-member-epics/access-requests) and choosing template _Access Change Request_
  * [ ] Configures Congregate to migrate from a GitHub.com to GitLab.com
    * [ ] Inspects and validates configured values in `data/congregate.conf`
      * **Tip:** Run `congregate validate-config` to ensure Congregate is configured properly
  * [ ] (optional) Runs `congregate clean-database --commit` to drop any previous collection(s) of users, groups and projects
    * [ ] If you are migrating from scratch add `--keys` argument to drop collection(s) of deploy keys as well

### User migration

Instructions for user migration collapsed by default.

#### Prepare users

* [ ] Review migration schedule (see customer migration schedule)
* [ ] Review [GitHub pre-requisites](https://docs.gitlab.com/ee/user/project/import/github.html#prerequisites) before performing migration
  * [ ] To import projects from GitHub, you must enable the [GitHub import source](https://docs.gitlab.com/ee/administration/settings/import_and_export_settings.html#configure-allowed-import-sources). **NOTE**: GitHub import source is enabled by default on GitLab.com
  * [ ] **Accounts for user contribution mapping**

    For user contribution mapping between GitHub and GitLab to work:
    * Each GitHub author and assignee in the repository must have a [public-facing email address](https://docs.github.com/en/account-and-profile/setting-up-and-managing-your-personal-account-on-github/managing-email-preferences/setting-your-commit-email-address).
    * The GitHub user’s email address must match their GitLab email address.
    * If a user’s email address in GitHub is set as their secondary email address in GitLab, they must confirm it.
  * [ ] GitHub Enterprise does not require a public email address, so you might have to add it to existing accounts.
* [ ] When provisioning users via SAML (Just-in-Time) or SCIM [domain verification](https://docs.gitlab.com/ee/user/enterprise_user/#1-add-a-custom-domain-for-the-matching-email-domain) is recommended to avoid [user account auto-deletion on gitlab.com after 3 days](https://gitlab.com/gitlab-org/gitlab/-/issues/352514)
  * [ ] **NOTE:** Product is considering to [exclude SCIM provisioned users](https://gitlab.com/gitlab-org/gitlab/-/issues/423322). SAML Just-in-Time provisioned users still need to confirm/verify their email
* [ ] When migrating/creating users via Congregate, using the admin token, they are automatically confirmed/verified. However, they still have to link their GitLab and SAML accounts
  * To link them they have to follow [this troubleshooting scenario](https://docs.gitlab.com/ee/user/group/saml_sso/troubleshooting.html#message-there-is-already-a-gitlab-account-associated-with-this-email-address-sign-in-with-your-existing-credentials-to-connect-your-organizations-account) to reset their pwd and login to gitlab.com for the 1st time
* [ ] Login to the migration VM using `ssh -L 8000:localhost:8000 <vm_alias_ip_or_hostname>` to expose UI port `8000` outside of the docker container
  * Run `congregate ui` from the container to start the Congregate UI
* [ ] Check the status of **gitlab.com** (https://status.gitlab.com/)
  * [ ] Confirm you can reach the UI of the instance
  * [ ] Confirm you can reach the API through cURL or a REST client
  * [ ] Confirm the import (Admin) user has a spoofed SAML link in _Profile -\> Account -\> Service sign-in_
    * It has to be spoofed as we do not want the customer provisioning a gitlab.com Admin account
    * See [GitLab migration prerequisites](https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate/-/blob/master/runbooks/migration-pre-and-post-requisites.md) for more details
* [ ] Create a directory called "waves" in `/opt/congregate/data` in the container if it doesn't already exist
* [ ] Create a directory called `user_wave` in `/opt/congregate/data/waves` if it doesn't already exist
* [ ] Run `nohup congregate list > data/waves/listing.log 2>&1 &` at the beginning of the migration blackout period
* [ ] Stage ALL users
  * **NOTE:** Make sure no groups and projects are staged
  * Determine (with customer) whether user ID 1 is a regular user that should be migrated
* [ ] Copy `data/staged_users.json` to `/opt/congregate/data/waves/user_wave`
* [ ] Lookup whether the staged users (emails) already exist on the destination by running `congregate search-for-staged-users` **NOTE**: The public profile email on source (GH) should match any (primary or secondary) verified/confirmed user email on destination
  * This will output a list of user metadata, based on `email`, along with other stats
  * Add argument `--table` to command to save this output to `data/user_stats.csv`
  * `public_email` field is not retrieved from GitHub source and therefore the `Source 'public_email' NOT set or NOT matching primary` column is either empty or might return wrong results in `user_stats.csv`
* [ ] Determine with customer how to configure:
  * [ ] `group_sso_provider` and `group_sso_provider_pattern`, if they are using SSO
  * [ ] `keep_inactive_users` (`False` by default),
    * `reset_pwd` (`True` by default),
    * `force_rand_pwd` (`False` by default)
* [ ] By default inactive users are skipped during user migration. To be sure they are removed from staged users, groups and projects run the following command:
  * [ ] Dry run: `congregate remove-inactive-users`
  * [ ] Live: `congregate remove-inactive-users --commit`
* [ ] Notify in the internal Slack channel dedicated to this migration you have completed preparation for the user wave

<details>
<summary>

#### Dry run users

</summary>

* [ ] Run the following command: `nohup congregate migrate > data/waves/user_wave/user_wave_dry_run.log 2>&1 &`
  * **NOTE:** The command assumes you have no groups or projects staged
* [ ] Confirm everything looks correct and move on to the next step in the runbook
  * Specifically, review the API requests and make sure the paths look correct.
  * If anything looks wrong in the dry run, make a note of it in the issue and reach out to `@gitlab-org/professional-services-automation/tools/migration` for review. Do not proceed with the migration if the dry run data looks incorrect. If this is incorrect, the data we send will be incorrect.
* [ ] Copy `data/results/dry_run_user_migration.json` to `/opt/congregate/data/waves/user_wave/` and attach to this issue
* [ ] Notify in the internal Slack channel dedicated to this migration you have completed dry run for the user wave

####

#### Migrate users

* [ ] Notify in the internal Slack channel dedicated to this migration you are starting the user migration wave
* [ ] Notify the customer in the customer-facing Slack channel you are starting the user migration wave
* [ ] Run the following command `nohup congregate migrate --commit > data/waves/user_wave/user_wave.log 2>&1 &`
* [ ] Monitor the wave periodically by running `tail -f data/waves/user_wave/user_wave.log`
* [ ] Copy the following files to `/opt/congregate/data/waves/user_wave/` and attach to this issue:
  * `data/logs/congregate.log`
  * `data/logs/audit.log`
  * `data/results/user_migration_results.json`
  * `data/waves/user_wave/user_wave.log`

</details>

### Group and project migration

#### Prepare groups and projects

For GitHub.com to GitLab.com, there are two ways to migrate

1. Only Projects(Repositories in GitHub)
2. Groups(Organisations/Teams in GitHub) and Projects(Repositories in GitHub)

### Option 1: Only Projects(Repositories in GitHub)

We perform wave migration for projects migration.

* [ ] **Migration Wave File:** Customer provides this migration wave.csv file defining what project goes to what group on the destination
  * This file lists out every github project on the customer’s instance and includes an unpopulated wave# and wave date column for each project. This also includes to what group will the project need to be migrated on GitLab.com
  * The customer is responsible for choosing which projects are apart of each wave
  * Once a wave is set, the PSE will import this information into the migration tool
  * Example of wave.csv: Wave name, Wave date, Source Url, Parent Path, Override

    <table>
    <tr>
    <td>

    **Wave name**
    </td>
    <td>

    **Wave date**
    </td>
    <td>

    **Source Url**
    </td>
    <td>

    **Parent Path**
    </td>
    <td>

    **Override**
    </td>
    </tr>
    <tr>
    <td>

    _Wave_1_
    </td>
    <td>

    _2049-01-01_
    </td>
    <td>

    _GitHub project url_
    </td>
    <td>

    _GitLab group url_
    </td>
    <td>

    _x_
    </td>
    </tr>
    <tr>
    <td>wave_1</td>
    <td>

    _2049-01-01_
    </td>
    <td>

    https://github.example.net/parent_1/project_1
    </td>
    <td>parent_group/nested</td>
    <td>x</td>
    </tr>
    </table>

* [ ] Review migration schedule (see customer migration schedule)
* [ ] Confirm all users have logged in and linked their SAML accounts (if applicable)
  * [ ] Disable top-level group SSO enforcement to allow membership and contribution mapping for users that do not have their SAML account linked
  * [ ] See Customer migration prerequisites for details
* [ ] Check the status of **gitlab.com** (https://status.gitlab.com/)
  * [ ] Confirm you can reach the UI of the instance
  * [ ] Confirm you can reach the API through cURL or a REST client
* [ ] Create a directory called "waves" in `/opt/congregate/data` in the container if it doesn't already exist
* [ ] Create a directory called `wave_<insert_wave_number>` in `/opt/congregate/data/waves` if it doesn't already exist
* [ ] Run `nohup congregate list > data/waves/listing.log 2>&1 &` at the beginning of the migration blackout period
* [ ] Stage projects based on the wave schedule using either UI or Command line:
  * [ ] UI
  * [ ] Command line:
    * [ ] `congregate stage-wave <wave name>` For example as per above table: `congregate stage-wave wave_1`
    * [ ] `nohup congregate stage-wave <wave name> --commit > data/waves/wave_<insert_wave_number>/wave_<insert_wave_number>_stage.log 2>&1 &`
    * [ ] tail above log file to know more
* [ ] Copy all staged data to `/opt/congregate/data/waves/wave_<insert_wave_number>/`
* [ ] Make sure the group(s) you are migrating to have shared runners enabled
  * This is to avoid a group import bug : GitLab issue 276930 (Not linked to avoid mention)
  * Originally avoided by fixing another bug : GitLab issue 290291 (Not linked to avoid mention)
* [ ] If `Restrict membership by email domain` is configured for the top-level group (_Settings -\> General -\> Permissions, LFS, 2FA_) make sure to add the Admin user's `gitlab.com` email domain
  * This is to avoid group and project import failures
* [ ] Notify in the internal Slack channel dedicated to this migration you have completed preparation for the wave

#### Dry run projects

* [ ] Run the following command: `nohup congregate migrate --skip-users --skip-groups > data/waves/wave_<insert_wave_number>/wave_<insert_wave_number>_dry_run.log 2>&1 &`
* [ ] Confirm everything looks correct and move on to the next step in the runbook
  * Specifically, review the API requests and make sure the paths look correct. For example, make sure any parent IDs, target namespace or other namespaces are matching the parent ID and parent namespaces we have specified in the congregate config.
  * If anything looks wrong in the dry run, make a note of it in the issue and reach out to `@gitlab-org/professional-services-automation/tools/migration` for review. Do not proceed with the migration if the dry run data looks incorrect. If this is incorrect, the data we send will be incorrect.
* [ ] Copy `data/results/dry_run_*_migration.json` to `/opt/congregate/data/waves/wave_<insert_wave_number>/` and attach to this issue
* [ ] Notify in the internal Slack channel dedicated to this migration you have completed dry run for the wave

#### Migrate projects

* [ ] Notify in the internal Slack channel dedicated to this migration you are starting the migration wave
* [ ] Notify the customer in the customer-facing Slack channel you are starting the migration wave
* [ ] Run the following command `nohup congregate migrate --skip-users --skip-groups --commit > data/waves/wave_<insert_wave_number>/wave<insert-wave-here>.log 2>&1 &`
* [ ] Monitor the wave periodically by running `tail -f data/waves/wave_<insert_wave_number>/wave<insert-wave-here>.log`
* [ ] Copy the following files to `/opt/congregate/data/waves/wave_<insert_wave_number>/` and attach to this issue:
  * `data/logs/congregate.log`
  * `data/logs/audit.log`
  * `data/results/group_migration_results.json`
  * `data/results/project_migration_results.json`
  * `data/logs/import_failed_relations.json`
  * `data/waves/wave_<insert_wave_number>/wave<insert-wave-here>.log`congregate/data/waves/wave\_/\`
* [ ] Inspect `data/logs/import_failed_relations.json` for any project import failed relations (missing feature info)
  * In case of missing MRs, Pipelines, etc. that are critical to the customer and business:
    * [ ] Stage and rollback projects with critical failed relations
      * **NOTE:** `--skip-users` and `--skip-groups`
    * [ ] Repeat [migration](#migrate-group-and-projects)
    * [ ] Once complete, and in case of consistently missing info, discuss and request verbal or written sign-off from customer
      * [ ] Otherwise [rollback](#rollback) the entire wave and reschedule
* [ ] Inspect [Kibana](https://log.gprd.gitlab.net/app/discover) logs for failed group and project membership
  * Adjust the time frame to the migration period
  * Query `pubsub-sidekiq-inf-gprd*` for `json.message: "[Project/Group Import] Member addition failed" AND json.root_namespace_id: "<parent-group-id>"`
  * (optional) Add additional fields to the query .e.g:
    * `json.message`
    * `json.importable_type`
    * `json.user_id`
    * `json.access_level`
* [ ] Inspect [Kibana](https://log.gprd.gitlab.net/app/discover) logs for failed group and project imports
  * Adjust the time frame to the migration period
  * Query `pubsub-sidekiq-inf-gprd*` for `json.class: "RepositoryImportWorker" AND json.meta.remote_ip: "<migration-vm-ip>"`
    * (optional) Add fields `json.meta.project` and `json.job_status`
  * Query `pubsub-sidekiq-inf-gprd*` for `json.class: "GroupImportWorker" AND json.meta.remote_ip: "<migration-vm-ip>"`
    * (optional) Add field `json.job_status`
  * For more options checkout the [Support workflow for import errors](https://about.gitlab.com/handbook/support/workflows/kibana.html#import-errors)
* [ ] Inspect [Kibana](https://log.gprd.gitlab.net/app/discover) logs for other import errors
  * Adjust the time frame to the migration period
  * Add `json.severity: ERROR`
  * Query `pubsub-sidekiq-inf-gprd*` for `json.extra.sidekiq.meta.remote_ip : "<migration-vm-ip>"`
    * (optional) Add additional fields to the query .e.g:
      * `json.extra.sidekiq.class`
      * `json.exception.message`
      * `json.exception.class`
      * `json.extra.relation_name`

### Option 2: Groups(Organizations/Teams in GitHub) and Projects(Repositories in GitHub)

We perform wave migration for Groups & Projects migration. In this option, Congregate creates the group(mentioned under _Parent Path_ column in wave.csv) if it is missing in the destination.

* [ ] **Migration Wave File:** Customer provides this migration wave.csv file defining what project goes to what group on the destination
  * This file lists out every github project on the customer’s instance and includes an unpopulated wave# and wave date column for each project. This also includes to what group will the project need to be migrated on GitLab.com
  * The customer is responsible for choosing which projects are apart of each wave
  * Once a wave is set, the PSE will import this information into the migration tool
  * Example of wave.csv: Wave name, Wave date, Source Url, Parent Path, Override

    <table>
    <tr>
    <td>

    **Wave name**
    </td>
    <td>

    **Wave date**
    </td>
    <td>

    **Source Url**
    </td>
    <td>

    **Parent Path**
    </td>
    <td>

    **Override**
    </td>
    </tr>
    <tr>
    <td>

    _Wave_1_
    </td>
    <td>

    _2049-01-01_
    </td>
    <td>

    _GitHub project url_
    </td>
    <td>

    _GitLab group url_
    </td>
    <td>

    _yes_
    </td>
    </tr>
    <tr>
    <td>wave_1</td>
    <td>

    _2049-01-01_
    </td>
    <td>

    https://github.example.net/parent_1/project_1
    </td>
    <td>parent_group/nested</td>
    <td>yes</td>
    </tr>
    </table>

* [ ] Review migration schedule (see customer migration schedule)
* [ ] Confirm all users have logged in and linked their SAML accounts (if applicable)
  * [ ] Disable top-level group SSO enforcement to allow membership and contribution mapping for users that do not have their SAML account linked
  * [ ] See Customer migration prerequisites for details
* [ ] Check the status of **gitlab.com** (https://status.gitlab.com/)
  * [ ] Confirm you can reach the UI of the instance
  * [ ] Confirm you can reach the API through cURL or a REST client
* [ ] Create a directory called "waves" in `/opt/congregate/data` in the container if it doesn't already exist
* [ ] Create a directory called `wave_<insert_wave_number>` in `/opt/congregate/data/waves` if it doesn't already exist
* [ ] Run `nohup congregate list > data/waves/listing.log 2>&1 &` at the beginning of the migration blackout period
* [ ] Stage groups and projects based on the wave schedule in either UI or Command line
  * [ ] UI
  * [ ] Command line:
    * [ ] `congregate stage-wave <wave name>` For example as per above table: `congregate stage-wave wave_1`
    * [ ] `nohup congregate stage-wave <wave name> --commit > data/waves/wave_<insert_wave_number>/wave_<insert_wave_number>_stage.log 2>&1 &`
    * [ ] tail above log file to know more
* [ ] Copy all staged data to `/opt/congregate/data/waves/wave_<insert_wave_number>/`
* [ ] Make sure the group(s) you are migrating to have shared runners enabled
  * This is to avoid a group import bug : GitLab issue 276930 (Not linked to avoid mention)
  * Originally avoided by fixing another bug : GitLab issue 290291 (Not linked to avoid mention)
* [ ] If `Restrict membership by email domain` is configured for the top-level group (_Settings -\> General -\> Permissions, LFS, 2FA_) make sure to add the Admin user's `gitlab.com` email domain
  * This is to avoid group and project import failures
* [ ] Notify in the internal Slack channel dedicated to this migration you have completed preparation for the wave

#### Dry run Groups & Projects

* [ ] Run the following command: `nohup congregate migrate --skip-users --group-structure > data/waves/wave_<insert_wave_number>/wave_<insert_wave_number>_dry_run.log 2>&1 &`
* [ ] Confirm everything looks correct and move on to the next step in the runbook
  * Specifically, review the API requests and make sure the paths look correct. For example, make sure any parent IDs, target namespace or other namespaces are matching the parent ID and parent namespaces we have specified in the congregate config.
  * If anything looks wrong in the dry run, make a note of it in the issue and reach out to `@gitlab-org/professional-services-automation/tools/migration` for review. Do not proceed with the migration if the dry run data looks incorrect. If this is incorrect, the data we send will be incorrect.
* [ ] Copy `data/results/dry_run_*_migration.json` to `/opt/congregate/data/waves/wave_<insert_wave_number>/` and attach to this issue
* [ ] Notify in the internal Slack channel dedicated to this migration you have completed dry run for the wave

#### Migrate Groups and Projects

* [ ] Notify in the internal Slack channel dedicated to this migration you are starting the migration wave
* [ ] Notify the customer in the customer-facing Slack channel you are starting the migration wave
* [ ] Run the following command `nohup congregate migrate --skip-users --group-structure --commit > data/waves/wave_<insert_wave_number>/wave<insert-wave-here>.log 2>&1 &`
* [ ] Monitor the wave periodically by running `tail -f data/waves/wave_<insert_wave_number>/wave<insert-wave-here>.log`
* [ ] Copy the following files to `/opt/congregate/data/waves/wave_<insert_wave_number>/` and attach to this issue:
  * `data/logs/congregate.log`
  * `data/logs/audit.log`
  * `data/results/group_migration_results.json`
  * `data/results/project_migration_results.json`
  * `data/logs/import_failed_relations.json`
  * `data/waves/wave_<insert_wave_number>/wave<insert-wave-here>.log` congregate/data/waves/wave\_/\`
* [ ] Inspect `data/logs/import_failed_relations.json` for any project import failed relations (missing feature info)
  * In case of missing MRs, Pipelines, etc. that are critical to the customer and business:
    * [ ] Stage and rollback projects with critical failed relations
      * **NOTE:** `--skip-users` and `--skip-groups`
    * [ ] Repeat [migration](#migrate-group-and-projects)
    * [ ] Once complete, and in case of consistently missing info, discuss and request verbal or written sign-off from customer
      * [ ] Otherwise [rollback](#rollback) the entire wave and reschedule

### Post Migration of Failed Groups and Projects

<details>
<summary>Instructions for post migration of failed groups and projects collapsed by default.</summary>

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
  * `data/logs/import_failed_relations.json`
  * `data/waves/wave_<insert_wave_number>/wave<insert-wave-here>.log`

####

### Post Migration of Failed User, Group and Project Info

* [ ] Inspect logs (and/or Slack) for failed migrations of single user, group and project features - everything Congregate additionally migrates after a user is created i.e. group and/or project imported
* [ ] In case of unexpected errors with the migration of post-import data (SSH keys, variables, reigistries, etc.):
  * [ ] Confirm those users/groups/projects are staged
  * [ ] Run `nohup ./congregate.sh migrate --only-post-migration-info --commit > data/waves/wave_<insert_wave_number>/wave<insert-wave-here>_attempt<insert-attempt>_post_migration.log 2>&1 &` to migrate any post-migration data
    * **NOTE:** `--only-post-migration-info` will implicitly skip group and project exports, but not imports and user creation

</details>

### Post Migration

* [ ] If you had to run multiple `congregate migrate` attempts to bring over failed users, groups, or projects, you can run `congregate migrate --only-post-migration-info` to create a unified results file without the need to run `stitch-results`
* [ ] Once you have a complete results file, run the diff report `congregate generate-diff --staged`
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
* [ ] Notify in the internal Slack channel dedicated to this migration the diff report is finished generating with a link to the comment you just posted.
* [ ] Notify the customer in the customer-facing Slack channel the migration wave has finished

### Archive Staged Projects

* [ ] Upon successfull migration and diff report discuss with customer when to archive staged projects on source
* [ ] Notify the customer in the customer-facing Slack channel you are archiving projects on source
* [ ] Run `nohup ./congregate.sh archive-staged-projects --commit > data/waves/user_wave/archive.log 2>&1 &`
  * **NOTE:** Make sure to have the correct `data/staged_projects` file present

### Rollback

<details>
<summary>

If **any** data was migrated incorrectly (i.e. to the wrong namespace), you **must** rollback the migration wave **completely**. Section collapsed by default.

</summary>

#### Users

* [ ] Notify in the internal Slack channel dedicated to this migration you are running a rollback due to an issue with the migration
* [ ] Dry run `nohup ./congregate.sh rollback --hard-delete --skip-groups --skip-projects > data/waves/user_wave/rollback_dry_run.log 2>&1 &`
  * **NOTE:** `--hard-delete` will also remove user contributions
* [ ] Live run `nohup ./congregate.sh rollback --hard-delete --skip-groups --skip-projects --commit > data/waves/user_wave/rollback.log 2>&1 &`
* [ ] Copy `data/logs/congregate.log` and `data/logs/audit.log` to `/opt/congregate/data/waves/user_wave/`
* [ ] Post a comment describing the reason for the rollback and attach the rollback log and `data/logs/audit.log`
* [ ] Follow these [instructions in the handbook](https://about.gitlab.com/handbook/engineering/security/#engaging-the-security-on-call) and link to this issue.

#### Groups and projects

* [ ] Make sure groups and projects can be immediately deleted
  * **Group Settings:** _Group -\> Settings -\> General -\> Permissions_
  * **Instance Settings:** _Admin Area -\> Settings -\> General -\> Visibility and access controls_
* [ ] If not, inform the Support Engineer with Rails Console access in order to delete them before proceeding. If there is no existing Support Engineer assigned to the issue, reach out in `#support_gitlab-com` Slack channel with the request details and link to a comment that lists the subgroups that require deletion.
* [ ] Notify in the internal Slack channel dedicated to this migration you are running a rollback due to an issue with the migration
* [ ] Dry run `nohup ./congregate.sh rollback --skip-users > data/waves/wave_<insert_wave_number>/rollback_dry_run.log 2>&1 &`
* [ ] Live run `nohup ./congregate.sh rollback --skip-users --commit > data/waves/wave_<insert_wave_number>/rollback.log 2>&1 &`
* [ ] Copy `data/logs/congregate.log` and `data/logs/audit.log` to `/opt/congregate/data/waves/wave_<insert_wave_number>/`
* [ ] Post a comment describing the reason for the rollback and attach the rollback log and `data/logs/audit.log`
* [ ] Follow these [instructions in the handbook](https://about.gitlab.com/handbook/engineering/security/#engaging-the-security-on-call) and link to this issue.

</details>

/confidential