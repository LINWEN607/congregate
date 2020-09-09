<!-- 
    Copy the contents of this runbook into an issue when running through migrtion prerequisites.
    Post the link to the issue on the Slack channel dedicated to this migration. 
-->

# <customer name> Migration Pre and Post-requisites

This runbook covers the process of preparing and cleaninig up after a migration from a source GitLab instance to a destination GitLab instance.

## Migration pre-requisites

### GitLab

* [ ] Setup the migration VM that will host the Professional Services (PS) migration tool’s (Congregate) Docker container.
  * It should have minimal port and IP access. See [VM Requirements](#VM) for more detail.
* [ ] (gitlab.com) Follow the [PS Provisioning Process](https://gitlab.com/gitlab-com/business-ops/team-member-enablement/runbooks/-/blob/master/it_operations/GitLab_com_environment_(PRD,DEV,STG)access_requests.md#provisioning-process) for GitLab.com environments Access Request.
* [ ] Configure LDAP/SAML identity for the Admin user account on the destination instance.
  * This is required for the user-group-project mapping to succeed.
* [ ] Create a one-off PAT for the Admin user account on the source instance.
  * The PAT should have an expiry date of the estimated last day (wave) of the migration.
* [ ] (gitlab.com) Generate awareness in Support/SRE team and identify specific individuals (with Rails console access) to take tickets from customers during migration.

### Customer

* [ ] Upgrade source and destination instance to the latest version of GitLab-EE.
* [ ] Consolidate users (and their number) that need to be migrated.
  * Determine whether blocked ones should be removed on source or migrated (as blocked).
* [ ] Create a user-group-project migration schedule (waves).
  * All users are migrated first.
  * Consider the option of migrating all groups (w/ sub-groups, w/o projects) next.
  * Projects are migrated in waves (with their parent groups if the previous was not done).
* [ ] Create one-off Admin user accounts on the source and destination instance (if applicable).
* [ ] Configure LDAP/SAML identity for the Admin user account on the destination instance.
  * This is required for the user-group-project mapping to succeed.

## VM

<!--
    Provide the VM details

    OS: Ubuntu 18.04 or similar

    N1 Instance (for gitlab.com)

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

* The host will require Docker to be installed and be able to pull the Congregate container from the GitLab.com container registery.
* The container/VM will collect data from the source and push it to the destiantion instance via the API.
* The VM/container must not be able to access other resources.

### Authentication (for gitlab.com)

The VM should be setup with Okta ASA. In case of time constraints setup SSH key authentication.

## Migration post-requisites

(gitlab.com) Once the migration is complete follow the [PS Deprovisioning Process](https://gitlab.com/gitlab-com/business-ops/team-member-enablement/runbooks/-/blob/master/it_operations/GitLab_com_environment_(PRD,DEV,STG)access_requests.md#deprovisioning-process) for GitLab.com environments Access Request.
