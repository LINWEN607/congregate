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

### Pre-migration checklist

PSE conducting the migration:

* [ ] Acquires an obfuscated (`./congregate.sh obfuscate`) GitLab source instance personal access token with admin privileges and `api` scope (top right icon _Your user Avatar -\> Edit Profile -\> Access Tokens_)
* [ ] Acquires an obfuscated (`./congregate.sh obfuscate`) GitLab.com Admin token with `api` scope by raising an _Issue_ in [Access request](https://gitlab.com/gitlab-com/team-member-epics/access-requests) and choosing template _Access Change Request_
* [ ] Configures Congregate to migrate from a GitLab instance to gitlab.com
  * [ ] Inspects and validates configured values in `data/congregate.conf`
    * **Tip:** Run `./congregate.sh validate-config`  to ensure Congregate is configured properly
* [ ] (optional) Runs `./congregate.sh clean-database --commit` to drop any previous collection(s) of users, groups and projects
  * [ ] If you are migrating from scratch add `--keys` argument to drop collection(s) of deploy keys as well

### User migration

<details>
<summary>Instructions for user migration collapsed by default.</summary>

#### Prepare users

* [ ] Review migration schedule (see customer migration schedule)
* [ ] When provisioning users via SAML (Just-in-Time) or SCIM [domain verification](https://docs.gitlab.com/ee/user/enterprise_user/#1-add-a-custom-domain-for-the-matching-email-domain) is recommended to avoid [user account auto-deletion on gitlab.com after 3 days](https://gitlab.com/gitlab-org/gitlab/-/issues/352514)
  * [ ] **NOTE:** Product is considering to [exclude SCIM provisioned users](https://gitlab.com/gitlab-org/gitlab/-/issues/423322). SAML Just-in-Time provisioned users still need to confirm/verify their email
* [ ] When migrating/creating users via Congregate, using the admin token, they are automatically confirmed/verified. However, they still have to link their GitLab and SAML accounts
  * To link them they have to follow [this troubleshooting scenario](https://docs.gitlab.com/ee/user/group/saml_sso/troubleshooting.html#message-there-is-already-a-gitlab-account-associated-with-this-email-address-sign-in-with-your-existing-credentials-to-connect-your-organizations-account) to reset their pwd and login to gitlab.com for the 1st time
* [ ] Login to the migration VM using `ssh -L 8000:localhost:8000 <vm_alias_ip_or_hostname>` to expose UI port `8000` outside of the docker container
  * Run `./congregate.sh ui` from the container to start the Congregate UI
* [ ] Check the status of **gitlab.com** (https://status.gitlab.com/)
  * [ ] Confirm you can reach the UI of the instance
  * [ ] Confirm you can reach the API through cURL or a REST client
  * [ ] Confirm the import (Admin) user has a spoofed SAML link in _Profile -\> Account -\> Service sign-in_
    * It has to be spoofed as we do not want the customer provisioning a gitlab.com Admin account
    * See GitLab migration prerequisites for details
* [ ] Create a directory called "waves" in `/opt/congregate/data` in the container if it doesn't already exist
* [ ] Create a directory called `user_wave` in `/opt/congregate/data/waves` if it doesn't already exist
* [ ] Ensure the permissions for the directories _/opt/congregate/data_ and _/opt/congregate/downloads_ are set to `ps-user`. Run the command (within the Congregate container) `sudo chown ps-user:ps-user -R data downloads` from the _/opt/congregate_ directory
* [ ] Run `nohup ./congregate.sh list > data/waves/listing.log 2>&1 &` at the beginning of the migration blackout period
* [ ] Stage ALL users
  * **NOTE:** Make sure no groups and projects are staged
  * Determine (with customer) whether user ID 1 is a regular user that should be migrated
* [ ] Copy `data/staged_users.json` to `/opt/congregate/data/waves/user_wave`
* [ ] Lookup whether the staged users (emails) already exist on the destination by running `./congregate.sh search-for-staged-users`
  * This will output a list of user metadata, based on `email`, along with other stats
  * Add argument `--table` to command to save this output to `data/user_stats.csv`
* [ ] Determine with customer how to configure:
  * `group_sso_provider` and `group_sso_provider_pattern`, if they are using SSO
  * `keep_inactive_users` (`False` by default),
  * `reset_pwd` (`True` by default),
  * `force_rand_pwd` (`False` by default)
* [ ] By default inactive users are skipped during user migration. To be sure they are removed from staged users, groups and projects run the following command:
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
* [ ] Run the following command `nohup ./congregate.sh migrate --commit > data/waves/user_wave/user_wave.log 2>&1 &`
* [ ] Monitor the wave periodically by running `tail -f data/waves/user_wave/user_wave.log`
* [ ] Copy the following files to `/opt/congregate/data/waves/user_wave/` and attach to this issue:
  * `data/logs/congregate.log`
  * `data/logs/audit.log`
  * `data/results/user_migration_results.json`
  * `data/waves/user_wave/user_wave.log`

</details>

### Group and project migration

#### Prepare groups and projects

* [ ] Confirm [group](https://docs.gitlab.com/ee/user/project/settings/import_export.html#enable-export-for-a-group) and [project](https://docs.gitlab.com/ee/administration/settings/import_and_export_settings.html#enable-project-export) exports are enabled on the source GitLab instance
* [ ] Confirm file exports are [enabled as an import source](https://docs.gitlab.com/ee/user/project/settings/import_export.html#configure-file-exports-as-an-import-source) on the destination GitLab instance
  * **NOTE:** Enabled by default on gitlab.com
* [ ] If container registries are migrated make sure to set `/var/run/docker.sock` permissions for the `ps-user` in the Congregate Docker container by running `sudo chmod 666 /var/run/docker.sock`.
* [ ] Confirm number and list of source projects with at least 1 job artifact > 1Gb ([gitlab.com instance level limit](https://docs.gitlab.com/ee/user/gitlab_com/#gitlab-cicd)) by running (PSQL) DB query:
  * `select distinct p.id, p.name from ci_job_artifacts a inner join projects p on p.id=a.project_id where a.size > 1000000000;`
  * These projects will either need to decrease their artifact size (to < 1Gb) or publish/share the generated files as (generic) [packages](https://docs.gitlab.com/ee/user/packages/package_registry/index.html) instead
* [ ] Review migration schedule (see customer migration schedule)
* [ ] Confirm all users have logged in and linked their SAML accounts (if applicable)
  * [ ] Disable top-level group SSO enforcement to allow membership and contribution mapping for users that do not have their SAML account linked
  * [ ] See Customer migration prerequisites for details
* [ ] Check the status of **gitlab.com** (https://status.gitlab.com/)
  * [ ] Confirm you can reach the UI of the instance
  * [ ] Confirm you can reach the API through cURL or a REST client
* [ ] Create a directory called "waves" in `/opt/congregate/data` in the container if it doesn't already exist
* [ ] Create a directory called `wave_<insert_wave_number>` in `/opt/congregate/data/waves` if it doesn't already exist
* [ ] Run `nohup ./congregate.sh list > data/waves/listing.log 2>&1 &` at the beginning of the migration blackout period
* [ ] Stage groups or projects based on the wave schedule in the UI
  * [ ] If staging by group make sure to stage all sub-groups as well
* [ ] Copy all staged data to `/opt/congregate/data/waves/wave_<insert_wave_number>/`
* [ ] Make sure the group(s) you are migrating to have shared runners enabled
  * This is to avoid a group import bug : GitLab issue 276930 (Not linked to avoid mention)
  * Originally avoided by fixing another bug : GitLab issue 290291 (Not linked to avoid mention)
* [ ] If `Restrict membership by email domain` is configured for the top-level group (_Settings -\> General -\> Permissions, LFS, 2FA_) make sure to add the Admin user's `gitlab.com` email domain
  * This is to avoid group and project import failures
* [ ] (as of **14.0**) Set `public_email` field for all staged users on source by running `./congregate.sh set-staged-users-public-email`
  * Skip running command if source version is **\< 14.0** and destination version is **\>= 14.0**
* [ ] Notify in the internal Slack channel dedicated to this migration you have completed preparation for the wave

**NOTE:** Projects and groups (except top-level group) are by (instance) default deleted after 7 days. In the meantime their name and path changes and the projects are archived. To immediately delete them one (Owner) has to delete them again. Adding `permanently_remove` immediately removes them via API.

#### Dry run groups and projects

* [ ] Run the following command: `nohup ./congregate.sh migrate --skip-users > data/waves/wave_<insert_wave_number>/wave_<insert_wave_number>_dry_run.log 2>&1 &`
  * [ ] If only sub-groups are staged make sure to add `--subgroups-only`
* [ ] Confirm everything looks correct and move on to the next step in the runbook
  * Specifically, review the API requests and make sure the paths look correct. For example, make sure any parent IDs or namespaces are matching the parent ID and parent namespaces we have specified in the congregate config.
  * If anything looks wrong in the dry run, make a note of it in the issue and reach out to `@gitlab-org/professional-services-automation/tools/migration` for review. Do not proceed with the migration if the dry run data looks incorrect. If this is incorrect, the data we send will be incorrect.
* [ ] Copy `data/results/dry_run_*_migration.json` to `/opt/congregate/data/waves/wave_<insert_wave_number>/` and attach to this issue
* [ ] Notify in the internal Slack channel dedicated to this migration you have completed dry run for the wave

#### Migrate groups and projects

* [ ] If container registries are migrated make sure to set `/var/run/docker.sock` permissions for `ps-user` by running `sudo chmod 666 /var/run/docker.sock`.
* [ ] Notify in the internal Slack channel dedicated to this migration you are starting the migration wave
* [ ] Notify the customer in the customer-facing Slack channel you are starting the migration wave
* [ ] Run the following command `nohup ./congregate.sh migrate --skip-users --commit > data/waves/wave_<insert_wave_number>/wave<insert-wave-here>.log 2>&1 &`
  * [ ] If only sub-groups are staged make sure to add `--subgroups-only`
  * [ ] Add `--retain-contributors` to map the users who contributed to a project in the past but are no longer members of the project
* [ ] Monitor the wave periodically by running `tail -f data/waves/wave_<insert_wave_number>/wave<insert-wave-here>.log`
* [ ] Copy the following files to `/opt/congregate/data/waves/wave_<insert_wave_number>/` and attach to this issue:
  * `data/logs/congregate.log`
  * `data/logs/audit.log`
  * `data/results/group_migration_results.json`
  * `data/results/project_migration_results.json`
  * `data/logs/import_failed_relations.json`
  * `data/waves/wave_<insert_wave_number>/wave<insert-wave-here>.log`congregate/data/waves/wave\_/\`
* [ ] Inspect `data/logs/import_failed_relations.json` for any project import failed relations (missing feature info)
  * In case of missing MRs, Piplines, etc. that are critical to the customer and business:
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

### Migrate project export larger than 5Gb

Project exports include, among others:

* Repository
* Wiki
* LFS objects
* Snippets
* Uploads

<details>
<summary>Instructions for migrating project exports >5Gb</summary>

#### Import project from AWS S3

**NOTE**: If the project size is bigger than 5 GB, less than 10 GB. We can import the project from AWS S3 through API.

1. Steps to install AWS CLI and connect to AWS S3
   1. [Install the AWS CLI](https://docs.aws.amazon.com/cli/v1/userguide/cli-chap-install.html)
   2. `aws configure` to [configure the AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html)
   3. `aws s3 ls s3://<bucket_name>` to verify if you can list your bucket
   4. `aws s3 cp <the project.tar.gz> s3://<bucket_name>` to upload the project package to S3 bucket
2. Follow [Import the Project from AWS S3](https://docs.gitlab.com/ee/api/project_import_export.html#import-a-file-from-aws-s3) to import the project from S3 to GitLab.com. Example:

    ```bash
    curl -v POST \
      --header "PRIVATE-TOKEN: <token>" \
      --header "Content-Type: application/json" \
      --url "https://gitlab.com/api/v4/projects/remote-import-s3" \
      --data '{
        "path": "<project-path>",
        "name": "<defaults-to-path-if-empty>",
        "namespace": “<full-target-group-path>",
        "region": "<s3-bucket-region>",
        "bucket_name": "<s3-bucket-name>",
        "file_key": "<export-file-name>.tar.gz",
        "access_key_id": “<aws-access-key>",
        "secret_access_key": “<aws-secret-key>"
      }'
    ```
    1. If you encounter errors, consult our PS troubleshooting guide [here](https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate/-/blob/master/docs/troubleshooting_s3_import.md)

#### Workarounds

Maximum import size limitations can prevent an import from being successful. If changing the import limits is not possible, you can try one of the workarounds listed here.

[Workaround Option 1](https://docs.gitlab.com/ee/user/project/settings/import_export_troubleshooting.html#workaround-option-1)

[Workaround Option 2](https://docs.gitlab.com/ee/user/project/settings/import_export_troubleshooting.html#workaround-option-2)

#### Manually Execute Project Export

You can [manually execute the project export](https://docs.gitlab.com/ee/user/project/settings/import_export_troubleshooting.html#manually-execute-export-steps) excluding unneeded exporters, for example LFS objects, to reduce the project size, and import LFS objects separately during the post migration step. Excluding uploads can also help, e.g. in the case of MRs exceeding the [Evaluate threshold](https://gitlab.com/gitlab-org/professional-services-automation/tools/utilities/evaluate#project-data), having many file uploads, and/or non-optimal object storage configuration on source.

</details>

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
  * [ ] (**optional**) Reach out to the Infra managers on Slack in #infrastructure-lounge by mentioning the issue.
  * [ ] Make sure to check off all checkboxes listed under Support in the import issue. We are Support in this instance.
  * [ ] Once the assignee confirms the import has started, promptly delete the project from google drive.
* Post Import. **The assignee will let you know when the import is complete.**
* If any projects imported by the assignee require any post-migration data to be migrated:
  * [ ] Confirm those projects are staged
  * [ ] Run `nohup ./congregate.sh migrate --skip-users --only-post-migration-info --commit > data/waves/wave_<insert_wave_number>/wave<insert-wave-here>_attempt<insert-attempt>_post_migration.log 2>&1 &` to migrate any post-migration data
    * [ ] If only sub-groups are staged make sure to add `--subgroups-only`
    * [ ] **NOTE:** `--only-post-migration-info` will implicitly skip group and project exports, but not imports and user creation

#### Alternative project export/import methods

* Export
  * [Via Rake task](https://docs.gitlab.com/ee/administration/raketasks/project_import_export.html#export-using-a-rake-task)
  * [Via Rails console](https://docs.gitlab.com/ee/user/project/settings/import_export_troubleshooting.html#manually-execute-export-steps)
* [Project import options](https://docs.gitlab.com/ee/development/import_project.html#importing-the-project)
  * [Via Rake task](https://docs.gitlab.com/ee/development/import_project.html#importing-via-a-rake-task)
  * [Via Rails console](https://docs.gitlab.com/ee/development/import_project.html#importing-via-the-rails-console)
* [Import/export Rake tasks](https://docs.gitlab.com/ee/administration/raketasks/project_import_export.html#importexport-rake-tasks)

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
p=Project.find_by_full_path('<full_path>')
=> #<Project id:<PID> <full_path>
u=User.find_by(username: '<admin_or_owner_username>')
=> #<User id:UID @<admin_or_owner_username>>

# (Optional) Find out delete error
p.delete_error
=> "PG::QueryCanceled: ERROR:  canceling statement due to statement timeout\n"

# (Optional) Count current pipelines
p.ci_pipelines.count
=> <no_of_pipelines_left>

# Option 1: Trim CI pipelines
p.ci_pipelines.find_each(start: <oldest_pipeline_id>, finish: <latest_pipeline_id>, batch_size: <no_of_pipelines_to_remove_per_batch>, &:destroy)
=> nil

# Option 2: Leave only pipelines triggered by tags
p.ci_pipelines.where(tag: false).find_each(batch_size: <no_of_pipelines_to_remove_per_batch>, &:destroy)

# Option 3: Remove all pipelines
p.ci_pipelines.find_each(batch_size: <no_of_pipelines_to_remove_per_batch>, &:destroy)
=> nil
p.ci_pipelines.count
=> 0

# (Optional) Count remaining pipelines
p.ci_pipelines.count
=> <no_of_pipelines_left>

# (WARNING) Completely remove the project
ProjectDestroyWorker.new.perform(p.id, u.id, {})
=> true
```

#### Fallback if container registries fail to migrate

In the event container registries fail to migrate, e.g. due to size and/or network restrictions, there is a bash script built into the container you can use as a backup.

The script is located at `<path_to_congregate>/dev/bin/manually_move_images.sh` (in the case of the container `/opt/congregate/dev/bin/manually_move_images.sh`)

The script usage is in the script, but here is a quick example of using the script:

```bash
sudo -E /opt/congregate/dev/bin/manually_move_images.sh registry.gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate registry.dest-gitlab.io/path/to/dest/registry/repo
```

This will migrate all containers from a single registry repository to another registry repository.

If you need to move several registry repositories, you can follow the usage of another script in `/dev/bin` called `docker_brute_force.py`. In that script, you pre-populate all source and destination registry repositories in a list of tuples. It's hacky, but still faster than manually pulling and pushing all docker containers.

* Optional checklist
  * [ ] Confirm container registries failed to migrate and make a comment in this issue describing the failure
  * [ ] (Optional) Prep `docker_brute_force.py` to migrate several registry repositories
  * [ ] Execute the docker migration through one of the following commands:
    * `nohup sudo ./dev/bin/manually_move_images.sh <source-repo> <destination-repo> > data/waves/wave_<insert_wave_number>/wave<insert-wave-here>_attempt<insert-attempt>_manual_docker_migration.log 2>&1 &`
    * `nohup sudo ./dev/bin/docker_brute_force.py > data/waves/wave_<insert_wave_number>/wave<insert-wave-here>_attempt<insert-attempt>_manual_docker_migration.log 2>&1 &`
  * [ ] Monitor the logs as it runs
  * [ ] Once it finishes, attach the logs to this issue

##### Migrate container registries per project

If registry migration is configured, instead of doing the actual migration, write the tags to the logs for use in the previously mentioned brute force migration. Can also be useful when renaming targets. To migrate all container registries per project:

1. Add the `--reg-dry-run` argument to the `migrate` command and run it
1. Confirm tuple files are newly generated in `<path_to_congregate>/data/reg_tuples` for each project with container registries
1. Update the `./<src-project-id>_repos.tpls` line in file `<path_to_congregate>/dev/bin/docker_brute_force_for_tpls.py` to match the source project ID for which you want to migrate container registries
1. Run `sudo -E python <path_to_congregate>/dev/bin/docker_brute_force_for_tpls.py`
1. Repeat steps 3-4 for each project that has a newly generated file in `<path_to_congregate>/data/reg_tuples`

### Post Migration of Failed User, Group and Project Info

* [ ] Inspect logs (and/or Slack) for failed migrations of single user, group and project features - everything Congregate additionally migrates after a user is created i.e. group and/or project imported
* [ ] In case of unexpected errors with the migration of post-import data (SSH keys, variables, reigistries, etc.):
  * [ ] Confirm those users/groups/projects are staged
  * [ ] Run `nohup ./congregate.sh migrate --only-post-migration-info --commit > data/waves/wave_<insert_wave_number>/wave<insert-wave-here>_attempt<insert-attempt>_post_migration.log 2>&1 &` to migrate any post-migration data
    * **NOTE:** `--only-post-migration-info` will implicitly skip group and project exports, but not imports and user creation

</details>

### Post Migration

* [ ] Revert back on source the exposed users' `public_email` field by running `./congregate.sh set-staged-users-public-email --hide`
  * Make sure all the affected users are staged first
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
