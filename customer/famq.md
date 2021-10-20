# Frequently Asked Migration Questions

This document should help customers, GitLab Sales and PS Management better understand individual aspects of a PS migration engagement.

[[_TOC_]]

## Do we migrate everything from the source SCM to GitLab overnight?

In short, we do not. We break up our migrations over a series of waves.

This is primarily due to the limits we have with how we migrate the data. Congregate is designed to handle migrating data primarily through consuming various GitLab APIs and other third party APIs (BitBucket, GitHub, etc.) so it has some limits with regards to how much data can be transmitted between instances through the instance's APIs. GitLab.com has rate limits so we can only import so many projects at a time before we hit a rate limit.

Please see [here](#q5) for more details on the topic.

## <a name="q2"></a>What does a migration wave consist of?

A wave consists of users, groups, and projects slated to be migrated within a day. A wave can consist of multiple users, groups, and projects.

Users i.e. their entire accounts with additional GitLab features (e.g. SSH and GPG keys) mentioned in the migration features matrix are migrated first. This, along with details mentioned [here](#q4) need to be in place before we migrate groups and projects. Only then can the user contribution mappings and permissions persist when we import groups and projects.

Please see [project](https://docs.gitlab.com/ee/user/project/settings/import_export.html#important-notes) and [group](https://docs.gitlab.com/ee/api/group_import_export.html#important-notes) import API notes for more details.

We require if you are migrating a group, it has to be at the top level due to how our group export/import works. We migrate a group and its subgroups and projects together. Breaking it apart over multiple waves complicates the process and is a time sink.

From an organization perspective, if you have groups set up in GitLab to consist of specific teams, then you are in good shape. Pick the teams you want to migrate in the order that best suits your schedule, and we can accommodate it. If your groups are scattered and the structure is all over the place, find what groups fit best within a wave by use case. We can provide guidance, but you know your organization and structure better than we do.

## What needs to be done in order to prepare for the migration engagement?

The [Migration Readiness Checklist](customer/migration-readiness-checklist.md) provides details about activities that need to be completed before the migration engagement.

## How do different terms relate across SCM/VCS i.e. development tools?

We have a [blog post](https://about.gitlab.com/blog/2017/09/11/comparing-confusing-terms-in-github-bitbucket-and-gitlab/) from a few years ago describing the different terms between GitHub, BitBucket Cloud, and GitLab, but there is a slight term discrepancy there where BB Cloud uses **Teams** and BB Server uses **Projects**.

The basic mapping of terms looks like the following:

| Development Tool | Collection of repositories | Individual development repo | Snippet of code | Requesting to bring code into the main baseline |
| ---------------- | -------------------------- | --------------------------- | --------------- | ----------------------------------------------- |
| GitLab           | Group                      | Project                     | Snippet         | Merge Request                                   |
| GitHub           | Organization               | Repository                  | Gist            | Pull Request                                    |
| BitBucket Cloud  | Team                       | Repository                  | Snippet         | Pull Request                                    |
| BitBucket Server | Project                    | Repository                  | Snippet         | Pull Request                                    |

We should have a more comprehensive table describing the differences between the greater development tools and the SCM/VCS they utilize. For example, *SVN* uses **trunk** while *Git* uses **master/main** and *AccuRev* and *ClearCase* use **streams** while *SVN*, *Git*, and *Mercurial* use **branches**.

## Is migrating to gitlab.com (SaaS) different than to GitLab Self-Managed (On-Prem)?

Please see [Migrating from Self-Managed GitLab to SaaS](https://about.gitlab.com/handbook/customer-success/professional-services-engineering/engagement-mgmt/scoping-information/migrations/SM-to-SaaS/) for more details.

## <a name="q3"></a>How long should a user expect the blackout/code-freeze period for their project as it is migrated?

That depends on the migration wave size and start time.

In short, it might be 0 (zero) hours, if the migration is handled outside of working hours or up to 8h.

The (PS) engineer orchestrating the migration might be in a favorable timezone to start and complete the work outside of customer working hours. When migrating to gitlab.com it is recommended (by GitLab Infra) to run the production migration during the weekend, when traffic is minimal. Mon-Fri early morning EMEA hours are the next best period. Please align with the designated engineer for timing and availability.

Please see [here](#q2) for a more elaborate explanation.

## <a name="q1"></a>What typically needs to be "fixed" in a migrated project?

Certain GitLab features are migrated but not adapted to the destination instance. These should be manually updated:

* Instance, group, sub-group and project level Runner registration
  * Group level runners can be manually (via UI - *Settings -> CI/CD -> Runners*) enabled/disabled as of 13.5
  * Enable project-level shared runners (default: `true`)
  * Disable AutoDevOps (default: `true`)
* Update group and project permissions (default: `private`). See [project](https://docs.gitlab.com/ee/user/project/settings/import_export.html#important-notes) and [group](https://docs.gitlab.com/ee/api/group_import_export.html#important-notes) import API notes for more details.
* Update paths (hostnames) for:
  * project, group and system hooks
    * **NOTE:** if they are pointing to a private instance or `localhost` gitlab.com will see them as invalid and fail creating them
  * badges
  * project and group CI/CD variables are migrated, but values that are source specific, e.g. project url or hostname, should be updated to the new values
  * secrets (tokens) that may be present in certain features, e.g. hooks, are not exposed in the API response and therefore not migrated. Those individual features have to be newly created
* Update project shared groups (unless the entire group structure is migrated first)
* Update instance and group level (custom) project templates
* Update and/or create any features that are not migrated (based on migration features matrix)

## What activities should a user do once a project is migrated?

Please see [here](#q1) for a more elaborate explanation.

## What are considerations for choosing projects in a "wave"?

Please see [here](#q2) for a more elaborate explanation.

## Are there limitations to migrating from GitLab Starter to GitLab Premium?

Since all of the [Features available to Starter and Bronze subscribers](https://docs.gitlab.com/ee/subscriptions/bronze_starter.html) have either went to *Free* or *Premium* there are no limitations.

Please see [Feature Comparison](https://about.gitlab.com/pricing/self-managed/feature-comparison/) for all available features.

Please see [Release Feature & Deprecation Overview](https://gitlab-com.gitlab.io/cs-tools/gitlab-cs-tools/what-is-new-since/) for more details on individual features.

## What happens to contributions of users that are not migrated?

They are inherited by the importer (import user).

Please see [project import API notes](https://docs.gitlab.com/ee/user/project/settings/import_export.html#important-notes) for more details.

## <a name="q4"></a>Do user contributions and permissions propagate during migration?

Yes, if an Admin user does the import, and on both source and destination the user:

* is a member of the imported group/project
* account exists and (primary) email is confirmed
* primary email is publicly exposed (via API)
* primary email is matching
* (SSO enforced only) has their SAML account linked

Otherwise the (Admin) import user will permanently inherit group/project mentions and contributions of those users.

The inherited group/project mentions and contributions will show a supplementary comment of the original author (see [project import notes](https://docs.gitlab.com/ee/user/project/settings/import_export.html#important-notes) for more details). If you hard-delete the import user, they are inherited by the GitLab instance default (and public) *Ghost* user.

Please see [project import API notes](https://docs.gitlab.com/ee/user/project/settings/import_export.html#important-notes) for more details.

Users might be deliberately missing because on the source instance they are:

* `blocked`
* `ldap_blocked`
* `deactivated`
* `banned`
* removed (e.g. ex employee)
* service accounts (gitlab.com requires user email validation)
* etc.

This doesn't mean we shouldn't migrate them, since `blocked`, `deactivated` and `banned` users do NOT consume a license seat. As long as the mapping prerequisites are met upon group/project import we can still preserve their mentions and contributions. It's then a matter of administration whether the accounts are:

* manually removed from the list of group/project members
* removed by enforcing SSO
* (Admin only) soft deleted from the instance

## Are GitLab Runners migrated and configured as part of the migration?

No, they are not part of the migration.

Please see [here](#q1) for more details on the topic.

## Are all project level features and configurations migrated?

No and/or not entirely.

Please consult the relevant [Congregate](https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate) migration features matrix (GitLab PS internal only) for more details.

## Whether and how should the migration affected instances be used during migration?

Make sure the GitLab source instance application users are aware of the migration (code freeze):

* As an Admin, broadcast a message to all users from the instance level, at least a week prior to the migration
* To discourage application activity during migration you may [restrict users from logging into GitLab](https://docs.gitlab.com/omnibus/maintenance/#restrict-users-from-logging-into-gitlab)
* As of GitLab 13.9 it's also possible to [enable maintenance mode](https://docs.gitlab.com/ee/administration/maintenance_mode/index.html#enable-maintenance-mode) during the migration, which allows most external actions that do not change internal state

Please see [here](#q3) for more details on the topic.

## What level of instance access and permission are needed for migrating?

A dedicated migration VM is used to orchestrate the user, group and project data transfers via source and destination API. For that reason at least this VM, and for certain (streaming/clone import) sources gitlab.com itself, need access to the source system's API via port `443`.

Additionally, on both the source and destination instance, an Admin user account and personal access token (PAT), with full `api` or equivalent scope, is needed to export/import or stream/clone the data over.

When migrating to gitlab.com (SaaS) GitLab IT provisions the Admin account while GitLab Infra/PS provision the migration VM.

Please see [here](#q4) and [here](#q5) for more details on this topic.

## <a name="q5"></a>What are a customer's obligations and responsibilities prior, during and after a migration?

Most of these are mentioned in the `migration-pre-and-post-requisites.md` file.

Additionally:

* delegate source instance (Admin) engineer(s) to attend daily migration calls with (PS) engineer(s)
* if applicable, delegate a destination instance Admin user and Personal Access Token (PAT) that will be used to create users i.e. import groups and projects
  * Please see [here](#q4) for more details on the topic
* determine suffix for duplicate usernames (e.g. `<username>_<suffix>`)
  * during user migration/creation GitLab requires a unique *Name*, *Username* and *Email* (primary email matching the one on source)
  * it can happen that a user with the same *Username*, but different *Name* and *Email* already exists on destination
  * in these (corner) cases we may add a suffix during user creation to avoid conflicts
* determine whether migrated data (projects) should be archived (read-only) on source upon completion
* adjust source/destination instance level settings to enable and improve migration performance, mainly:
  * [Project/group import/export rate limits](https://docs.gitlab.com/ee/user/admin_area/settings/import_export_rate_limits.html)
  * [GitLab self-managed User and IP rate limits](https://docs.gitlab.com/ee/user/admin_area/settings/user_and_ip_rate_limits.html)
  * email and IP domain access for GitLab migration user
  * publicly expose user primary emails (see [here](#q4) for more details)
* other GitLab limits that may require adjusting
  * [Rate limits](https://docs.gitlab.com/ee/security/rate_limits.html)
  * [GitLab self-managed application limits](https://docs.gitlab.com/ee/administration/instance_limits.html)
  * [GitLab.com-specific rate limits](https://docs.gitlab.com/ee/user/gitlab_com/#gitlabcom-specific-rate-limits)
* share GitLab instance and container registry SSL certificate key chain to `ssl_verify` the API connections
* (optional) provide UI (Admin) access to source/destination instance
  * this is manly for the (PS) engineer to run the migration async, e.g. outside of customer working hours and without assistance

## Does the source instance need to be updated to latest in order to migrate?

Not necessarily. Having the source instance align as close as possible with the destination version, while not surpassing, is preferable, as stated [here](https://docs.gitlab.com/ee/user/project/settings/import_export.html#important-notes).

>Imports from a newer version of GitLab are not supported. The Importing GitLab version must be greater than or equal to the Exporting GitLab version.

### Version Requirements

* The GitLab Project export / import API versions need to match between instances and follow the [version history](https://docs.gitlab.com/ee/user/project/settings/import_export.html#version-history) requirements.
* The GitLab Group export / import API versions need to match between instances and follow the [version history](https://docs.gitlab.com/ee/user/group/settings/import_export.html#version-history) requirements.
* The source version should not be more than 2 minor versions behind
  * [Project Import/Export Version History](https://docs.gitlab.com/ee/user/project/settings/import_export.html#130)
  * [Security Releases](https://docs.gitlab.com/ee/policy/maintenance.html#security-releases)

When it comes to how old can the GitLab source instance be we come to the following milestones to take into account:

* **12.8** - MVC version of GitLab group export/import API which is mandatory for PS migrations
* **12.9** - Fixed order of exported group and project relations (e.g. pipelines)
* **12.10** - Added issue/MR state to project export
* **13.0**
  * UI version of GitLab group export/import
  * `NDJSON` introduced on group and project export/import to improve GitLab memory usage
* **13.3** - Most export and major project import bugs resolved
* **13.7** - Several project and group export/import bugs resolved
* **14.0**
  * `JSON` format no longer supported for project and group exports, but still supported on import
  * Group epics labels associations preserved during export/import
* **14.2.2**
  * The `public_email` field is used, instead of `email`, for group and project export/import
  * On import it is backwards compatible i.e. accepting the `email` field if exported
  * The deprecation version for import is not yet known

### Importer bugs

* [Group Export/Import bugs](https://gitlab.com/groups/gitlab-org/-/epics/4614)
* [Project Export/Import bugs](https://gitlab.com/groups/gitlab-org/-/epics/3054)
* [Bitbucket Importer bugs](https://gitlab.com/groups/gitlab-org/-/epics/5514)
* [GitHub Importer bugs](https://gitlab.com/groups/gitlab-org/-/epics/3050)
