<!-- 
    Copy the contents of this runbook into an issue when running through migrtion prerequisites.
    Post the link to the issue on the Slack channel dedicated to this migration. 
-->

# <customer name> Migration prerequisites

This list covers the process of preparing for migration from a source GitLab instance to a destination GitLab instance.

## Migration prerequisites

### GitLab

* [ ] Setup the migration VM that will host the PS migration tool’s (Congregate) Docker container.
  * It should have minimal port and IP access. See [VM Requirements](#VM) for more detail.
* [ ] (gitlab.com) Create a one-off Admin account and personal access token (PAT) on the destination instance for importing.
  * Once the migration is complete revoke the Admin account for the migrating customer to retain.
* [ ] Create on source and destination the (Admin) user PAT with an expiry date.

### Customer

* [ ] Upgrade source and destination instance to the latest version of GitLab-EE.
* [ ] Consolidate users (and their number) that need to be migrated.
  * [ ] Determine whether blocked ones should be removed on source or migrated (as blocked).
* [ ] Make sure that the migration user admin account has LDAP/SAML identity configured on the destination instance.
  * This is required for the user-group-project mapping to succeed.
* [ ] Create a user-group-project migration schedule (waves) per migration.
  * All users are migrated first.
  * Consider the option of migrating all groups (w/ sub-groups, w/o projects) next.
  * Projects are migrated in waves (with their parent groups if the previous was not done).
* Create temporary group level (Owner) accounts on the source and destination instance.

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
