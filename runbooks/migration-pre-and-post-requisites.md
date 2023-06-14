<!--
    Copy the contents of this runbook into an issue when running through migration prerequisites.
    Post the link to the issue on the Slack channel dedicated to this migration.
-->

# [customer name] Migration Pre and Post-requisites

This runbook covers the process of preparing and cleaning up after a migration from a source GitLab instance to a destination GitLab instance.

* (gitlab.com) [GitLab Commercial Customer Success Documentation](https://gitlab-com.gitlab.io/account-management/commercial/documentation/) on migrating to gitlab.com.

## Migration pre-requisites

<details><summary>GitLab and Customer steps collapsed by default.</summary>

<!--
    Specify the migration period

    3:00PM 2020-09-07 - 3:00AM 2020-09-15
-->

### GitLab

* [ ] For to-SaaS migrations, verify with the Account/Sales team that all licensing is setup for the `namespace` on `gitlab.com`, make sure the customer's `namespace` is set as `private`.
* [ ] Setup the migration VM that will host the Professional Services (PS) migration tool’s (Congregate) Docker container.
  * It should have minimal port and IP access. See [VM Requirements](#vm) for more detail.
  * **NOTE:** If required the VM might be created, by the customer, within their environment. Make sure this approach is covered in the SoW.
* [ ] (gitlab.com) Follow the [PS Provisioning Process](https://gitlab.com/gitlab-com/business-technology/team-member-enablement/runbooks/-/blob/master/it_operations/GitLab_com_environment_(PRD,DEV,STG)access_requests.md#provisioning-process) for GitLab.com environments Access Request (AR) i.e. Admin account.
  * Create [new AR issue](https://gitlab.com/gitlab-com/team-member-epics/access-requests/-/issues) from the `Access_Change_Request` issue template
  * Follow the description to add labels
    * `AR-Approval::Needs Manager Approval`
    * `AR::In Queue`
    * `admin-access`
    * `IT::to do`
    * `NewAccessRequest`

    **NOTE:** Labels may change over time
  * Assign to Manager for review/approval. 
    * Managers: 
      * Follow the instructions in the AR template for review and approval
      * Additionally mention SIRT for review i.e. `@gitlab-com/gl-security/security-operations/sirt`

    **NOTE:** Mentions may change over time
  * (Optional) Post issue in Slack's [**#it_help**](https://gitlab.slack.com/archives/CK4EQH50E) channel
* (gitlab.com) To avoid provisioning the (Admin) export/import user in an external identity provider, spoof the SAML identity. `PUT` the following json body to `https://<hostname>/api/v4/users/<id>` to modify the Admin user:

    ```json
    {
      "provider": "group_saml",
      "extern_uid": "<random_uid>",
      "group_id_for_saml": <parent_group_id>
    }
    ```

    **NOTE:** The group needs to have SAML configured.

* [ ] Create one-off Personal Access Tokens (PATs) for the Admin user account on the source and destination instance.
  * The PATs should have an expiry date of the estimated last day (wave) of the migration.
  * [ ] (gitlab.com) Inform SIRT about every Admin token creation and/or user impersonation.
* [ ] (gitlab.com) Generate awareness in Support/SRE/Infra teams and identify specific individuals (e.g. with Rails console access) to take tickets from customers during migration. Highlight these people/groups in the migration wave issues.
  * **NOTE**: These issues **must** be created [5 days in advance](https://about.gitlab.com/handbook/support/workflows/importing_projects.html#import-scheduled) of executing the migration wave.

### Customer

* [ ] Upgrade and align the source and destination instances to the latest version of GitLab-EE
  * [Project export/import compatibility](https://docs.gitlab.com/ee/user/project/settings/import_export.html#compatibility)
  * [Group export/import compatibility](https://docs.gitlab.com/ee/user/group/import/index.html#compatibility)
* [ ] Clean registries and repositories as much as possible:
  * [ ] Repositories:
    * [ ] Get under 5Gb of project export for an optimal chance at success
    * [ ] Clean as many branches, merge requests, etc as possible from the history
  * [ ] Registries:
    * [ ] Clear as many tags as possible. Number * size of images can impact migration performance and duration
* [ ] Consolidate users (and their number) that need to be migrated.
  * Determine whether inactive ones should be removed on source, skipped during migration or migrated and inactive on destination.
  * (gitlab.com) Configure valid primary emails for service accounts to avoid issues with [Confirmation Emails](https://about.gitlab.com/handbook/support/workflows/confirmation_emails.html).
* [ ] (from GitHub) Make sure that all relevant GitHub users have their `public email` field set and matching `email`
* [ ] Check whether legacy projects, with 1k+ issues/MRs and/or 10k+ pipelines, could be slimmed down for a more seamless export/import
  * [ ] If done via Rails console, schedule a meeting between lead PSE and source instance Admin to walk through the process
    * For exact steps see [**Trim or remove project CI pipelines**](/runbooks/migrations-to-dot-com.md#trim-or-remove-project-ci-pipelines)
* [ ] Create a user-group-project migration schedule (waves)
  * [ ] All users (excluding [internal and bot](https://docs.gitlab.com/ee/development/internal_users.html#internal-users)) are migrated first
  * [ ] Entire group structure next
    * (gitlab.com) [Notes](https://docs.gitlab.com/ee/user/group/import/index.html#migrate-groups-by-uploading-an-export-file-deprecated) around GitLab Group Export/Import
    * Consult with your engineer around restrictions for group movement and renaming, as it is dependent on your source system and migration requirements
  * Projects are migrated in waves (with their parent groups if the previous was not done)
  * (gitlab.com) GitLab support requires a 5-day lead on migrations to gitlab.com. Consider this when determining wave schedule
* [ ] If needed create dedicated (Admin) export/import user accounts on the source and destination instance.
  * Otherwise use any existing Admin user accounts
* [ ] Make sure the (Admin) export/import user(s) (may be different) are provisioned in your source and destination LDAP/SAML [identity provider](https://docs.gitlab.com/ee/administration/auth/), as other users
  * This is to avoid any permission issues on export/import
* [ ] (gitlab.com) If using a SAML+SSO identity provider (Okta, Azure, etc.) on the destination instance make sure:
  * All `active` users are provisioned in the identity provider using the same primary email as on the source instance
  * All users are logged in to gitlab.com
  * All users have linked their GitLab and SAML accounts by logging in via the identity provider's GitLab SAML app

  **NOTE:** Properly mapped contributions depend on group/project membership. If a user is added as a group/project member it gets mapped and is taken into consideration when doing the contribution (GitLab features) mapping.
* [ ] Configure source and destination instance (if applicable) rate limits ([configurable as of 13.2](https://docs.gitlab.com/ee/api/README.html#rate-limits))
  * This may also be done temporarily, for the duration of the migration wave
* [ ] Configure destination instance (if applicable) [immediate group and project deletion permissions](https://about.gitlab.com/handbook/support/workflows/hard_delete_project.html). They are required in case of a rollback scenario, where all staged groups and projects need to be removed on the destination instance.
  * This may also be done temporarily, for the duration of the migration wave
* [ ] Make sure the GitLab source instance application users are aware of the migration (code freeze)
  * As an Admin, broadcast a message to all users from the instance level, at least a week prior to the migration
  * To discourage application activity during migration you may [restrict users from logging into GitLab](https://docs.gitlab.com/omnibus/maintenance/#restrict-users-from-logging-into-gitlab)
  * As of GitLab 13.9 it's also possible to [enable maintenance mode](https://docs.gitlab.com/ee/administration/maintenance_mode/index.html#enable-maintenance-mode) during the migration, which allows most external actions that do not change internal state
* [ ] (gitlab.com) In case you **Restrict membership by email domain** (on *Settings -> General -> Permissions, LFS, 2FA*) on the parent group, make sure to add `gitlab.com`. This will allow the migration/import user to unpack imported group and project exports.
* [ ] (Optional) To improve the performance of background jobs (Sidekiq), handling multiple group and project exports, add the following to the GitLab `/etc/gitlab/gitlab.rb` configuration

    ```ruby
    gitlab_rails['env'] = {
      'SIDEKIQ_MEMORY_KILLER_MAX_RSS' => "0"
    }
    sidekiq['queue_groups'] = [
      "*"
    ]
    ```

</details>

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

`Congregate` is run from a migration host jumpbox. Where that box is hosted depends on a few factors:

* As migrations currently require an admin API token, the VM cannot be hosted inside of a customer space if the migration involves SaaS. The VM has to be hosted:
  * In GitLab GCP infrastructure provisioned using the below process -OR- in another GitLab-controlled web space
    * This may require work on the customer side to setup access (VPN, firewall, WireGuard, etc) if their source system is not internet-facing
* If the migration does *not* involve SaaS, it can be hosted in any space that has access to the source and destination system.
  * Generally, inside the more "walled" system
* Special Case: Multi-Hop to/from SaaS
  * If the customer will not/can not open ports or provide a VPN connection, we can do the following:
    * Migrate (using Congregate) to an internet-exposed interim instance in a cloud space using an admin token from the source system (say SaaS) and an admin token for the interim instance
    * Remove the admin token from the source system (say SaaS)
    * Customer can now migrate from the interim to their internal instance by pulling the Congregate container to a machine inside their wall, using an admin token for their target system, and an admin token from the interim instance

### Requisitioning a Migration VM (GitLab GCP Hosted)

* [ ] (gitlab.com) Create an MR in [Transient Imports project](https://gitlab.com/gitlab-com/gl-infra/transient-imports) by following the [_README.md_](https://gitlab.com/gitlab-com/gl-infra/transient-imports#transient-imports)
  * Add customer [PS epic](https://gitlab.com/groups/gitlab-com/customer-success/professional-services-group/-/epics) link in the MR description
  * The lead PSE should add their gitlab.com `.pub` SSH key as `owner_key`
  * Make sure all PSEs running the migration have added their public IP to the `source_ranges_allowed` list (comma separated)
    * Comment on the IPs listing order eg: `# pse1, pse2, pse3`
  * Please comment in the module listing the customer name or SOW link. This helps with tracking for de-provisioning, later. Eg: `# This VM is for customer: ABC Inc`
  * Set the following variables in the `modules` section:
    * `gl_customer_name = "name of customer"` Eg: `gl_customer_name = "acme"`
    * `gl_owner_email_handle = "email name of lead PSE"` Eg: `gl_owner_email_handle = "gmiller"`
    * **Note:** these items have the following restrictions: `The value can only contain lowercase letters, numeric characters, underscores and dashes. The value can be at most 63 characters long. International characters are allowed.`
  * Assign yourself and comment `/assign_reviewer @<see-in-project-readme>`
* [ ] Once the MR is approved and merged retrieve the IP from the `apply` stage and job

  ```text
  Apply complete! Resources: 1 added, 0 changed, 0 destroyed.
  Outputs:
  import-<issue_id>-ip = <public_ip>
  ```

  * Test the access: `ssh -i ~/.ssh/<ssh_private_key> root@<public_ip>`
  * Update package manager: `apt update && apt upgrade -y && apt autoremove -y`
  * Install docker: `apt install docker.io`
  * Follow `./congregate/docs/full_setup.md#Installing and configuring Congregate (end-user)` for further steps

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
Due to time constraints, ASA costs and scaling limitations it may be necessary to provision only SSH key authentication.

## Migration post-requisites

<details><summary>GitLab and Customer steps collapsed by default.</summary>

* [ ] If required archive all projects on source that have been migrated
* [ ] If applicable [disable maintenance mode](https://docs.gitlab.com/ee/administration/maintenance_mode/index.html#disable-maintenance-mode) on source

### De-provisioning

#### Migration VM

* [ ] (Optional) Backup group and project export archive files
* [ ] (gitlab.com) Deprovision migration VM by informing Infra in the issue ([VM Requirements](#vm)) commenting that the migration is complete
  * Create an MR, linking to the issue and comment, and delete the `import-<issue_no>.tf` file
  * Assign an SRE to review, approve and merge the MR

#### Admin account

* [ ] (gitlab.com) Once the migration is complete follow the [PS De-provisioning Process](https://gitlab.com/gitlab-com/business-technology/team-member-enablement/runbooks/-/blob/master/it_operations/GitLab_com_environment_(PRD,DEV,STG)access_requests.md#deprovisioning-process) for GitLab.com environments Access Request
  * Remove 2FA and spoofed SAML
  * If the user account is soft-deleted (w/o user contributions history) their GitLab features mapping will remain intact
  * If the user account is hard-deleted (w/ user contributions history) their GitLab features will fallback to the `Ghost` user
  * If the user account is blocked it will completely prevent access to the GitLab instance and [more](https://docs.gitlab.com/ee/user/admin_area/moderate_users.html#block-a-user)

  **NOTE:** Only Support/IT can perform any of the 3 mentioned actions once Admin privileges are stripped from the user account
* [ ] Revoke/remove PATs used for the migration
* [ ] Revoke Admin rights

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
* [ ] Update project and group shared groups (unless the entire group structure is migrated first)
  * [ ] (gitlab.com) Update direct group and project membership to allow specific user and group MR approval rules in projects
* [ ] Update instance and group level (custom) project templates
* [ ] Update and/or create any features that are not migrated (based on migration features matrix)

</details>

/confidential
