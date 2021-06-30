<!-- 
    Copy the contents of this runbook into an issue when running through migration prerequisites.
    Post the link to the issue on the Slack channel dedicated to this migration.
-->

# [customer name] Migration Pre and Post-requisites

This runbook covers the process of preparing and cleaning up after a migration from a source GitLab instance to a destination GitLab instance.

* (gitlab.com) [GitLab Commercial Customer Success Documentation](https://gitlab-com.gitlab.io/account-management/commercial/documentation/) on migrating to gitlab.com.

## Migration pre-requisites

<!--
    Specify the migration period

    3:00PM 2020-09-07 - 3:00AM 2020-09-15
-->

### GitLab

* [ ] Setup the migration VM that will host the Professional Services (PS) migration tool’s (Congregate) Docker container.
  * [ ] It should have minimal port and IP access. See [VM Requirements](#VM) for more detail.
  * **NOTE:** If required the VM might be created, by the customer, within their environment. Make sure this approach is covered in the SoW.
* [ ] (gitlab.com) Follow the [PS Provisioning Process](https://gitlab.com/gitlab-com/business-technology/team-member-enablement/runbooks/-/blob/master/it_operations/GitLab_com_environment_(PRD,DEV,STG)access_requests.md#provisioning-process) for GitLab.com environments Access Request.
* [ ] Configure LDAP/SAML (in [identity provider](https://docs.gitlab.com/ee/administration/auth/)) for the Admin user account on the destination instance (as for other users).
  * This is required for the user-group-project mapping to succeed.
  * (gitlab.com) Add user to SAML+SSO identity provider destination parent group.
    * Another way to add SAML to the migration user profile, that also avoids provisioning a GitLab admin account in an external identity provider, is to spoof the SAML identity. `PUT` the following json body to `https://<hostname>/api/v4/users/<id>` to modify the Admin user:

      ```json
      {
        "provider": "group_saml",
        "extern_uid": "<uid>",
        "group_id_for_saml": <group_id>
      }
      ```

* [ ] Create a one-off PAT for the Admin user account on the source instance.
  * The PAT should have an expiry date of the estimated last day (wave) of the migration.
* [ ] (gitlab.com) Generate awareness in Support/SRE/Infra teams and identify specific individuals (e.g. with Rails console access) to take tickets from customers during migration. Highlight these people/groups in the migration wave issues.
  * **NOTE**: These issues **must** be created [5 days in advance](https://about.gitlab.com/handbook/support/workflows/importing_projects.html#import-scheduled) of executing the migration wave.

### Customer

* [ ] Upgrade and align the source and destination instances to the latest version of GitLab-EE ([notes](https://docs.gitlab.com/ee/user/project/settings/import_export.html#version-history)).
* [ ] Clean registries and repositories as much as possible:
  * [ ] Repositories:
    * [ ] Get under 5Gb of project export for an optimal chance at success
    * [ ] Clean as many branches, merge requests, etc as possible from the history
  * [ ] Registries:
    * [ ] Clear as many tags as possible. Number * size of images can impact migration performance and duration
* [ ] Consolidate users (and their number) that need to be migrated.
  * Determine whether inactive ones should be removed on source, skipped during migration or migrated and inactive on destination.
  * (gitlab.com) Configure valid primary emails for service accounts to avoid issues with [Confirmation Emails](https://about.gitlab.com/handbook/support/workflows/confirmation_emails.html).
* [ ] Check whether legacy projects, with 1k+ issues/MRs and/or 10k+ pipelines, could be slimmed down for a more seamless export/import
  * [ ] If done via Rails console, schedule a meeting between lead PSE and source instance Admin to walk through the process
    * For exact steps see **Trim or remove project CI pipelines** in `migrations-to-*.md` runbook
* [ ] Create a user-group-project migration schedule (waves).
  * All users are migrated first.
  * Consider the option of migrating all groups (w/ sub-groups, w/o projects) next.
    * (gitlab.com) [Notes](https://docs.gitlab.com/ee/api/group_import_export.html#important-notes) around Group import/export when using the GitLab Group Export/Import
    * Consult with your engineer around restrictions for group movement and renaming, as it is dependent on your source system and migration requirements
  * Projects are migrated in waves (with their parent groups if the previous was not done).
  * (gitlab.com) GitLab support requires a 5-day lead on migrations to gitlab.com. Consider this when determining wave schedule.
* [ ] Create dedicated migration (Admin) user accounts on the source and destination instance.
* [ ] Configure LDAP/SAML (in [identity provider](https://docs.gitlab.com/ee/administration/auth/)) for the Admin user account on the destination instance (as for other users).
  * This is required for the user-group-project mapping to succeed.
  * (gitlab.com) Add user to SAML+SSO identity provider on destination parent group.
* [ ] Configure source and destination instance (if applicable) rate limits ([configurable as of 13.2](https://docs.gitlab.com/ee/api/README.html#rate-limits))
  * This may also be done temporarily, for the duration of the migration wave
* [ ] Configure destination instance (if applicable) [immediate group and project deletion permissions](https://about.gitlab.com/handbook/support/workflows/hard_delete_project.html). They are required in case of a rollback scenario, where all staged groups and projects need to be removed on the destination instance.
  * This may also be done temporarily, for the duration of the migration wave
* [ ] Make sure the GitLab source instance application users are aware of the migration (code freeze)
  * As an Admin, broadcast a message to all users from the instance level, at least a week prior to the migration
  * To discourage application activity during migration you may [restrict users from logging into GitLab](https://docs.gitlab.com/omnibus/maintenance/#restrict-users-from-logging-into-gitlab)
  * As of GitLab 13.9 it's also possible to [enable maintenance mode](https://docs.gitlab.com/ee/administration/maintenance_mode/index.html#enable-maintenance-mode) during the migration, which allows most external actions that do not change internal state
* (gitlab.com) In case you **Restrict membership by email domain** (on *Settings -> General -> Permissions, LFS, 2FA*) on the parent group, make sure to add `gitlab.com`. This will allow the migration/import user to unpack imported group and project exports.

## VM

<!--
    Provide the VM details

    (to gitlab.com) GCP Instance

    OS: Ubuntu 18.04

    N1 Instance

    * 8 vCPU
    * 16GB memory (2GB/vCPU)
    * 200GB storage - SSD
-->

* (gitlab.com) Create a [GitLab Infra team issue](https://gitlab.com/groups/gitlab-com/gl-infra/-/issues) with labels `~"team::Core-Infra"` and `~"AssistType::CloudInfra"` and `/assign @gitlab-com/gl-infra/managers` ([example](https://gitlab.com/gitlab-com/gl-infra/infrastructure/-/issues/12813))
* (gitlab.com) Create an MR in [Transient Imports project](https://gitlab.com/gitlab-com/gl-infra/transient-imports) by following the `README`
  * The lead PSE should add their gitlab.com `.pub` SSH key as `owner_key`
  * Make sure all PSEs running the migration have added their public IP to the `source_ranges_allowed` list (comma separated)
  * Assign yourself and comment `/assign_reviewer @gitlab-com/gl-infra/managers`
* Once the MR is approved and merged retrieve the IP from the `apply` stage and job

  ```text
  Apply complete! Resources: 1 added, 0 changed, 0 destroyed.
  Outputs:
  import-<issue_id>-ip = <public_ip>
  ```

  * Test the access: `ssh -i ~/.ssh/<ssh_private_key> root@<public_ip>`
  * Update package manager: `apt update && apt upgrade -y && apt autoremove -y`
  * Install docker: `apt install docker.io`
  * Follow `README.md#Installing and configuring Congregate (end-user)` for further steps

### Network; VM interaction

<!--
    Copy the following table to determine port and IP access

    | Host                    | Protocol | Port(s)                     |
    | ----------------------- | -------- | --------------------------- |
    | [source-hostname]       | TCP      | 443                         |
    | [destination-hostname]  | TCP      | 443                         |
    | [source-registry]       | TCP      | [port]                      |
    | [destination-registry>  | TCP      | [port] (443 for gitlab.com) |
    | [local-ip] (gitlab.com) | TCP      | 22                          |
-->

* The host will require `sudo` rights in order to:
  * Install and login to `docker` for access to source and destination instance container registry
  * Pull the Congregate container from the GitLab.com container registry
* The container/VM will collect data from the source instance and push it to the destination instance via the API.

### Authentication (for gitlab.com)

If possible, the VM should be setup with Okta Advanced Server Access (ASA).
Due to time constraints, ASA costs and scaling limitations it may be necessary to provision only SSH key authenticaton.

## Migration post-requisites

* [ ] If required archive all projects on source that have been migrated
* [ ] If applicable [disable maintenance mode](https://docs.gitlab.com/ee/administration/maintenance_mode/index.html#disable-maintenance-mode) on source

### VM Deprovisioning

* [ ] (gitlab.com) Once the migration is complete follow the [PS Deprovisioning Process](https://gitlab.com/gitlab-com/business-technology/team-member-enablement/runbooks/-/blob/master/it_operations/GitLab_com_environment_(PRD,DEV,STG)access_requests.md#deprovisioning-process) for GitLab.com environments Access Request
* [ ] (gitlab.com) Deprovision migration VM by informing Infra in the issue ([VM Requirements](#VM)) commenting that the migration is complete
  * [ ] Create an MR, linking to the issue and comment, and delete the `import-<issue_no>.tf` file
  * [ ] Assign an SRE to review, approve and merge the MR
* [ ] Strip dedicated migration user on destination of Admin rights, PATs and update sign-in credentials
* [ ] (Optional) Backup group and project export archive files

### Instance checks

Certain GitLab features are migrated but not adapted to the destination instance. These should be manually updated.

* [ ] Instance, group, sub-group and project level Runner registration
  * Group level runners can be manually (via UI - *Settings -> CI/CD -> Runners*) enabled/disabled as of 13.5
  * Enable project-level shared runners (default: true)
  * Disable AutoDevOps (default: true)
* [ ] Update group and project permissions
* [ ] Update paths (hostnames) for:
  * project, group and system hooks
    * **NOTE:** if they are pointing to a private instance or `localhost` gitlab.com will see them as invalid and fail creating them
  * badges
  * project and group CI/CD variables are migrated, but values that are source specific, e.g. project url or hostname, should be updated to the new values
  * secrets (tokens) that may be present in certain features, e.g. hooks, are not exposed in the API response and therefore not migrated. Those individual features have to be newly created
* [ ] Update project shared groups (unless the entire group structure is migrated first)
* [ ] Update instance and group level (custom) project templates
* [ ] Update and/or create any features that are not migrated (based on migration features matrix)

/confidential
