# Consolidated Discovery Notes

The Ultimate Goal of this document is to have its contents converted into a roadmap markdown file with an index of questions unique to each source and destination. For example when performing a migration from Bitbucket to Gitlab.com you would review the questions/notes for Source -> Bitbucket and Destination -> Gitlab.com/SaaS. All notes and contributions are welcome (it is the GitLab way). Any miscellaneous or unsorted notes can be placed in the section Unsorted Notes. Please indicate any source/destination that contributions apply to.

## Sources

## Destinations

### Gitlab.com / SaaS

#### Migration Host:

* Our migration host lives in GCP. Do we have firewall access to their instances?
* Specific outbound IPs of the machine can be retrieved from the GCP console, so that they don't have to allow the entire GCP range through the wall
* If you need to allow the entire GCP range (eg: for streaming imports) the range can be found [here](https://docs.gitlab.com/ee/user/gitlab_com/#ip-range)
    * Streaming imports (BitBucket, GitHub, soon to be GitLab) currently require `http` *or* `trusted https`. Self-signed certificates will fail. Options:
        * Disable `https` on the source instance
        * Add an external signed certificate to the instance
        * Use a `N (multi)-hop` migration
        * Use a `reverse proxy` that trusts the internal certificate and forwards requests
    * Note: The above options may require adjustments to the project scope and timeline
* VPN usage is supported, but can limit migrations speeds
    * Make sure to remove any IP throttling that may be configured

#### General Users

* Do users on the source system have their public email set?
  * Reason: It is required for attribution
* Explain/reiterate that the highest permissions for SaaS is group owner. They will not be "administrators"
  * We are moving towards [Enterprise Users](https://gitlab.com/groups/gitlab-org/-/epics/4786)
* Number of users and projects involved in each wave
  * Usually no constraints on number of users. A few thousand users can be migrated at once. Congregate checks if active users from the source instance exist in the destination instance. If the user does not exist on the destination, then the new users will be created.

#### Projects

* Review Owner, Maintainer and Developer roles and what each is allowed to do. 

[https://docs.gitlab.com/ee/user/permissions.html]( https://docs.gitlab.com/ee/user/permissions.html#project-members-permissions)

* Review [Branch protection rules](https://docs.gitlab.com/ee/user/project/protected_branches.html#who-can-modify-a-protected-branch) (disallow push to master by anyone)
* Review [Merge Request Approval rules](https://docs.gitlab.com/ee/user/project/merge_requests/approvals/) (enable project maintainers to approve)
* Review [CODEOWNERS](https://docs.gitlab.com/ee/user/project/code_owners.html) concept for large repos
* Review how to create and maintain [Issue and merge request templates](https://docs.gitlab.com/ee/user/project/description_templates.html)

#### Runners

* Will you be using SaaS shared runners?
    * Port requirements for connection to on-premise systems: [https://docs.gitlab.com/ee/user/gitlab_com/#ip-range](https://docs.gitlab.com/ee/user/gitlab_com/#ip-range)
* Will you be bringing your own runners?
    * You will need to re-register them on your own
    * Runners communicate outbound over HTTPS (443)
* Runners need to be re-registered at the Instance, group, sub-group and project level
* Group level runners can be manually (via UI - _Settings -> CI/CD -> Runners_) enabled/disabled as of 13.5
* Runners will need to be on the same version level as the gitlab instance.

#### Registries

##### Container Registry

* Are you using the container registry on the source?
* Do you intend to use container registry on SaaS?
* We support container registry migration, but registry size can severely impact migration times. Please clean out the container registry as much as possible before migration

##### Package Registry

* We support GitLab to GitLab Maven Package Registry migration at this time. Other package types are pending.

#### SSO/SCIM/SAML

* Are emails changing across systems?
* Is SSO configured on the destination system?
    * (SaaS) If you want to Enforce SSO-only authentication after the migration we can migrate users, groups, and projects per usual. Contribution mapping will not be deleted, but the users have to login before enforcing it or they will get kicked out automatically and lose their membership mapping. If this happens, these users will have to be manually added back and be remapped. This is not as bad as losing contribution mapping, but should still be avoided. 
* Will you be using Group SAML ?
    * [https://docs.gitlab.com/ee/user/group/saml_sso/](https://docs.gitlab.com/ee/user/group/saml_sso/)
* Will you be using SCIM? [https://docs.gitlab.com/ee/user/group/saml_sso/scim_setup.html](https://docs.gitlab.com/ee/user/group/saml_sso/scim_setup.html)
* Will you be using SCIM provisioning, SAML JIT provisioning, or linking SAML to existing users?
    * With SCIM provisioning, their SCIM provider will sync with GitLab creating/deleting users as needed
    * With SAML JIT, if SAML SSO is setup, it will attempt to create users on first login attempt using the same process
    * SAML link is just what it sounds like. They have an existing user on the GitLab, they login to that account, login to their SSO provider, and link the two
* Will SSO be enforced with web and/or git activity?
    * Recommend not setting until after all contribution and membership mapping is complete
* Will you be using SAML group sync? - [https://docs.gitlab.com/ee/user/group/saml_sso/#group-sync](https://docs.gitlab.com/ee/user/group/saml_sso/#group-sync)
    * Can affect synchronization and permissions
    * Recommend not setting until after all contribution and membership mapping is complete
* Will users be expected to login one time before migration?
    * If currently not, can this be enforced?
    * This ensures that user accounts are confirmed properly
* What SAML/SSO/SCIM providers are you using?
    * Each is configured slightly differently. We have better integrations with some than others, particularly on the SCIM side
    * Consult GitLab documentation and watch YouTube videos for examples

#### Security Settings

##### Group Security Settings

* Will you need the IP allow list configured? - [https://docs.gitlab.com/ee/user/group/#restrict-group-access-by-ip-address](https://docs.gitlab.com/ee/user/group/#restrict-group-access-by-ip-address)
* Will you be restricting access by domain? - [https://docs.gitlab.com/ee/user/group/#restrict-group-access-by-domain](https://docs.gitlab.com/ee/user/group/#restrict-group-access-by-domain)
* Are you Enabling Two Factor authentication? -
    * [https://docs.gitlab.com/ee/user/profile/account/two_factor_authentication.html](https://docs.gitlab.com/ee/user/profile/account/two_factor_authentication.html)
* When moving to SaaS users are no longer admins
* Discuss the permission inheritance 
    * Project Security settings
    * Review Owner, Maintainer and Developer roles and what each is allowed to do. 
    * Review Branch protection rules (disallow push to master by anyone)
    * Review Merge Request Approval rules (enable project maintainers to approve)
    * Review CODEOWNERS concept for large repos

#### Miscellaneous

##### Integrations and webhooks in use

* In some instances (source code) URL/Location updates will need to be made. Integrations are not migrated as of yet and you will need to manually update those links.
* We have a way to clean up hard coded pipeline URLs to update them to the destination. Webhook migration is a post-migration step.

##### Communications with internal and external systems

* Suggest mapping out all expected communications. [Template available](https://drive.google.com/drive/u/0/folders/16Sbs1KCTm9DRrAgg5eEvtfWPOB9dFbQZ)

Other areas with large amounts of data - MR's, pipelines, etc:

* Number of historic pipelines that have run on the repo. Over 1500 runs can clog up the system. So if a project has over a couple thousand pipelines, that will cause a closed issue. 

Use of secrets/deploy tokens/deploy keys:

* CI/CD variables are migrated automatically

Cross-project dependencies:

* If you have a group of common libraries that are used, make sure to point them out. If you have a place for common utilities, that would need to be migrated first to avoid problems. 

## Common Deliverables 

### GitLab CI/CD Architecture Diagram: 

* Delivered by GitLab Solutions Architect (SA). Broad deliverable. Doesn’t fit into SaaS other than runner information

### Single Sign-On Configuration Plan

* The single sign-on configuration plan should ideally be ripped out of SOW templates and reworded into a support-based deliverable i.e “Support the customer in configuring their SSO configuration”. 
* Helpful Background Information: [SSO and SCIM Primer for PSE’s](https://docs.google.com/document/d/1Wuw2kKD9pbNwsYbIy81AJzMZjOD6M94WkveqkOElpmE/edit#heading=h.8lmjx4887lrh)

### Security Configuration Plan

* The security configuration plan should ideally be ripped out of SOW templates and reworded into a support-based deliverable i.e “Support the customer in configuring their security configuration”. 

## General Migration Constraints

* Migrations are typically capped at 200 projects per wave
* When migrating to SaaS, projects with git repo sizes greater than 5GB will be excluded from the automated Migration. This is due to API limitations on Gitlab.com
* GitLab instances must be up to date or lagging the current version by no more than 1 month
* Manual verification before and after migration grow with scale

## FAQ

## Unsorted Notes

## Resources

[Customer Collaboration Project - Template](https://gitlab.com/gitlab-com/account-management/templates/customer-collaboration-project-template)

[Migration Project - Template](https://gitlab.com/gitlab-org/professional-services-automation/delivery-kits/migration-template)

[pre/post-setup issue - template](https://gitlab.com/gitlab-org/professional-services-automation/delivery-kits/migration-template/-/issues/new?issuable_template=migration-pre-and-post-requisites)

[Migration Wave Considerations](https://gitlab.com/gitlab-org/professional-services-automation/delivery-kits/migration-template/-/blob/master/customer/migration-wave-considerations.md)

[Frequently Asked Migration Questions](https://gitlab.com/gitlab-org/professional-services-automation/delivery-kits/migration-template/-/blob/master/customer/famq.md)

[Migration Feature Matrix - GitLab](https://gitlab.com/gitlab-org/professional-services-automation/delivery-kits/migration-template/-/blob/master/customer/gitlab-migration-features-matrix.md)

[Migration Feature Matrix - BitBucket](https://gitlab.com/gitlab-org/professional-services-automation/delivery-kits/migration-template/-/blob/master/customer/bitbucket-migration-features-matrix.md)

[Migration Feature Matrix - GitHub](https://gitlab.com/gitlab-org/professional-services-automation/delivery-kits/migration-template/-/blob/master/customer/github-migration-features-matrix.md)

[Migration Kickoff Deck(google Slides) - Template](https://docs.google.com/presentation/d/1AzM_qYKKOYhgvNTrEBXRmFT2m0caBuKZ6VAH6sCbiKQ/edit#slide=id.g59bfc474c5_2_145)

[Project Kickoff Deck(Google Slides) - Template](https://docs.google.com/presentation/d/1HtVIE64N94Rcc774ujllClGmYZ5y1_ApE4-O3pazR6k/edit#slide=id.g911d82cfdc_1_5)

[Congregate Codebase](https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate)

## Gitlab Docs

[Project Import/Export](https://docs.gitlab.com/ee/user/project/settings/import_export.html)

[Migrating Projects](https://docs.gitlab.com/ee/user/project/import/)
