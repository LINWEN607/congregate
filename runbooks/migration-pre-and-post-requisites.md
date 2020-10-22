<!-- 
    Copy the contents of this runbook into an issue when running through migration prerequisites.
    Post the link to the issue on the Slack channel dedicated to this migration. 
-->

# <customer name> Migration Pre and Post-requisites

This runbook covers the process of preparing and cleaning up after a migration from a source GitLab instance to a destination GitLab instance.

* (gitlab.com) requesting to have a VM created in the transient-imports GCP project.
* (gitlab.com) [GitLab Commercial Customer Success Documentation](https://gitlab-com.gitlab.io/account-management/commercial/documentation/) on migrating to gitlab.com.

## Migration pre-requisites

<!--
    Specify the migration period

    3:00PM 2020-09-07 - 3:00AM 2020-09-15
-->

### GitLab

* [ ] Setup the migration VM that will host the Professional Services (PS) migration tool’s (Congregate) Docker container.
  * [ ] It should have minimal port and IP access. See [VM Requirements](#VM) for more detail.
  * [ ] For proper DNS mapping make sure to add the source IP/hostname to the VM and docker container `/etc/hosts` file, e.g.:

  ```bash
  127.0.0.1 localhost
  192.168.1.1 source.instance.org
  ```

* [ ] (gitlab.com) Follow the [PS Provisioning Process](https://gitlab.com/gitlab-com/business-ops/team-member-enablement/runbooks/-/blob/master/it_operations/GitLab_com_environment_(PRD,DEV,STG)access_requests.md#provisioning-process) for GitLab.com environments Access Request.
* [ ] Configure LDAP/SAML (in [identity provider](https://docs.gitlab.com/ee/administration/auth/)) for the Admin user account on the destination instance (as for other users).
  * This is required for the user-group-project mapping to succeed.
  * (gitlab.com) Add user to SAML+SSO identity provider destination parent group.
* [ ] Create a one-off PAT for the Admin user account on the source instance.
  * The PAT should have an expiry date of the estimated last day (wave) of the migration.
* [ ] (gitlab.com) Generate awareness in Support/SRE/Infra teams and identify specific individuals (e.g. with Rails console access) to take tickets from customers during migration. Highlight these people/groups in the migration wave issues.
  * **NOTE**: These issues **must** be created [5 days in advance](https://about.gitlab.com/handbook/support/workflows/importing_projects.html#import-scheduled) of executing the migration wave.

### Customer

* [ ] Upgrade and align the source and destination instances to the latest version of GitLab-EE ([notes](https://docs.gitlab.com/ee/user/project/settings/import_export.html#important-notes)).
* [ ] Consolidate users (and their number) that need to be migrated.
  * Determine whether blocked ones should be removed on source, skipped during migration or migrated and blocked on destination.
  * (gitlab.com) Configure valid primary emails for service accounts to avoid issues with [Confirmation Emails](https://about.gitlab.com/handbook/support/workflows/confirmation_emails.html).
* [ ] Create a user-group-project migration schedule (waves).
  * All users are migrated first.
  * Consider the option of migrating all groups (w/ sub-groups, w/o projects) next.
  * Projects are migrated in waves (with their parent groups if the previous was not done).
* [ ] Create dedicated migration (Admin) user accounts on the source and destination instance.
* [ ] Configure LDAP/SAML (in [identity provider](https://docs.gitlab.com/ee/administration/auth/)) for the Admin user account on the destination instance (as for other users).
  * This is required for the user-group-project mapping to succeed.
  * (gitlab.com) Add user to SAML+SSO identity provider on destination parent group.
* [ ] Configure source and destination instance (if applicable) rate limits ([configurable as of 13.2](https://docs.gitlab.com/ee/api/README.html#rate-limits))
  * This may also be done temporarily, for the duration of the migration wave
* [ ] Configure destination instance (if applicable) [immediate group and project deletion permissions](https://about.gitlab.com/handbook/support/workflows/hard_delete_project.html). They are required in case of a rollback scenario, where all staged groups and projects need to be removed on the destination instance.
  * This may also be done temporarily, for the duration of the migration wave

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

* The host will require Docker to be installed and be able to pull the Congregate container from the GitLab.com container registry.
* The container/VM will collect data from the source instance and push it to the destination instance via the API.

### Authentication (for gitlab.com)

The VM should be setup with Okta ASA, but based on time constraints it may be necessary to provision only SSH key authenticaton.

## Migration post-requisites

### VM Deprovisioning

* [ ] (gitlab.com) Once the migration is complete follow the [PS Deprovisioning Process](https://gitlab.com/gitlab-com/business-ops/team-member-enablement/runbooks/-/blob/master/it_operations/GitLab_com_environment_(PRD,DEV,STG)access_requests.md#deprovisioning-process) for GitLab.com environments Access Request.
* [ ] Strip dedicated migration user on destination of Admin rights, PATs and update sign-in credentials.
* [ ] (Optional) backup group and project export archive files.

### Instance checks

Certain GitLab features are migrated but not adapted to the destination instance. These should be manually updated.

* [ ] Group, sub-group and project level Runner registration
  * Enable project-level shared runners (default: true)
  * Disable AutoDevOps (default: true)
* [ ] Update group and project permissions
* [ ] Update paths (hostnames) for:
  * project, group and system hooks
  * badges
  * project and group CI/CD variables (if their values are source instance specific)
* [ ] Update project shared groups (unless the entire group structure is migrated first)
* [ ] Update instance and group level (custom) project templates
* [ ] Update any features that are not migrating over (based on migration features matrix)

/confidential
