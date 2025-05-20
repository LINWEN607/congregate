![](img/gitlab-logo-100.png)

# Migration Planning and Expectations

Revision 1.2

Revision.date 02.28.2024

Prepared by GitLab Professional Services

## ToC

- [Migration Planning and Expectations](#migration-planning-and-expectations)
  - [ToC](#toc)
- [Migration Process Overview](#migration-process-overview)
  - [Phase 1 - Planning](#phase-1---planning)
    - [Audience](#audience)
  - [Phase 2 - Setup](#phase-2---setup)
    - [Audience](#audience-1)
  - [Phase 3 - Pilot Migrations](#phase-3---pilot-migrations)
    - [Audience](#audience-2)
  - [Phase 4 - Main Migrations](#phase-4---main-migrations)
    - [Audience](#audience-3)
  - [Phase 5 - Wrap Up](#phase-5---wrap-up)
    - [Audience](#audience-4)
- [Pre and Post Migration Considerations](#pre-and-post-migration-considerations)
  - [General](#general)
  - [Pre-Migration - Developers](#pre-migration---developers)
    - [Familiarize Themselves with GitLab](#familiarize-themselves-with-gitlab)
    - [Review Project Repositories](#review-project-repositories)
    - [Backup Important Data](#backup-important-data)
    - [Communicate with Teammates](#communicate-with-teammates)
    - [Resolve Pending Tasks](#resolve-pending-tasks)
    - [Update Local Workflows](#update-local-workflows)
    - [Backup Personal Keys](#backup-personal-keys)
    - [Prepare CI/CD Configurations](#prepare-cicd-configurations)
    - [Test Workflows in GitLab](#test-workflows-in-gitlab)
    - [Provide Feedback](#provide-feedback)
  - [Pre Migration - System](#pre-migration---system)
    - [Identification of resources](#identification-of-resources)
    - [Users](#users)
    - [Hard-coded Dependencies](#hard-coded-dependencies)
    - [Networking](#networking)
    - [Access and Permissions](#access-and-permissions)
    - [Domains (and BYOD)](#domains-and-byod)
      - [Action](#action)
    - [Email Systems](#email-systems)
    - [Integrations and Dependencies](#integrations-and-dependencies)
      - [Action](#action-1)
    - [Repositories](#repositories)
  - [Pre Migration](#pre-migration)
    - [Schedule and Planning](#schedule-and-planning)
    - [Communications](#communications)
    - [Determine Post-Migration Steps](#determine-post-migration-steps)
    - [Customer Coordinator](#customer-coordinator)
    - [Scheduling and constraints](#scheduling-and-constraints)
    - [App Teams {#app-teams}](#app-teams-app-teams)
  - [Post Migration](#post-migration)
    - [Projects - Developers](#projects---developers)
    - [Project Owners and Maintainers](#project-owners-and-maintainers)
    - [Unmigrated Project Features (GitLab to GitLab)](#unmigrated-project-features-gitlab-to-gitlab)
      - [Sensitive information](#sensitive-information)
      - [Generally not supported](#generally-not-supported)
    - [Unmigrated Project Features (GitHub to GitLab)](#unmigrated-project-features-github-to-gitlab)
    - [CI/CD Pipelines](#cicd-pipelines)
    - [Issue Tracking and Boards](#issue-tracking-and-boards)
    - [Merge Requests](#merge-requests)
    - [Wikis and Documentation](#wikis-and-documentation)
    - [Integrations and Tooling](#integrations-and-tooling)
    - [Security and Compliance](#security-and-compliance)
    - [Badges](#badges)
    - [Boards and Board Lists](#boards-and-board-lists)
    - [Epics](#epics)
    - [Group Labels](#group-labels)
    - [Iterations and Iteration Cadences](#iterations-and-iteration-cadences)
    - [Members](#members)
    - [Group Milestones and Release Milestones](#group-milestones-and-release-milestones)
    - [Namespace Settings](#namespace-settings)
    - [Uploads](#uploads)
  - [Common Post Migration Issues](#common-post-migration-issues)
  - [Customer-Specific Section](#customer-specific-section)
    - [Additional Pre Migration Concerns](#additional-pre-migration-concerns)
    - [Additional Post Migration Steps and Checks](#additional-post-migration-steps-and-checks)
    - [Post Migration Support Plan](#post-migration-support-plan)
- [FAQ](#faq)
- [Links](#links)

# Migration Process Overview

The Migration Process Overview is intended to be a high level outline, describing the process to plan, execute, and report on a migration. For the majority of migration cases, [Congregate](https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate) will be used to orchestrate migrations in waves. Some tasks will need to happen infrequently, others every wave, some multiple times per wave. Project migrations should start with a small number in the Phase 1 Pilot Migrations and then start ramping up in the Phase 4 Main Migrations as issues are addressed.

Before actual production migrations, your communication plan for end users should be developed, and shared with users who will be migrated. Stakeholders who can verify functionality for a completed migration should be identified ahead of time. Schedule of said verifications should be decided ahead of time as well. I.e. will they verify immediately after the migration, during a planned outage window? Will they verify the following day when they are available?

This guide is based on years of experience migrating customers' valuable data ensuring a smooth transition with minimal impact to end users. This guide is a good starting point to a successful migration and should help ensure a smooth transition. It is meant to help C7 get started, but by no means is exhaustive.

Below is what a project’s general timeline might look like. Phase 3 and 4 timelines can be adjusted by the number of projects, and any end user feedback that needs to be incorporated into the migration process.

## Phase 1 - Planning

Work with stakeholders to verify requirements and scope, identify concerns, rough draft schedules, and approved communication plans. These communication plans might include items such as feedback loops, error handling, end user onboarding, end user expectations, and risk management.

General steps for this phase include; Generate the Source and Destination admin tokens. Setup the Migration VM with Congregate modifying the congregate.conf file as appropriate. Identify projects to participate in Phase 3 Pilot Migrations, suggesting that there are no more than 20 projects representing a wide range of use cases, such as larger or smaller projects, projects with pipelines, users that are knowledgeable and not knowledgeable about GitLab. Generate the migration schedule and waves thinking through dependencies.

If any existing projects have pipelines, GitLab-Runner requirements should be identified and planned to be dealt with preferably in Phase 2 - Setup or Phase 3 - Pilot Migrations.

### Audience

* Customer Migration Team
* Customer Product Owners
* Customer Security Team
* Customer Infrastructure Team
* GitLab Professional Services Engineer (PSE)
* GitLab Project Manager (PM)

| Common Tasks                                                    | DRI                                                            |
| :-------------------------------------------------------------- | :------------------------------------------------------------- |
| Identify Stakeholders                                           | Customer Product Owners and GitLab PM                          |
| Develop Communication Plans                                     | Customer Product Owners and GitLab PM                          |
| Develop Schedule (Migration Waves)                              | Customer Product Owners and GitLab PM                          |
| Generate Admin Tokens                                           | Customer Infrastructure and Security Team                      |
| Set Up Migration VM                                             | Customer Infrastructure and Migration Team                     |
| Identify Pilot Migration Projects                               | Customer Migration Team and GitLab PSE                         |
| Identify GitLab-Runner Requirements                             | Customer Migration Team and GitLab PSE                         |
| Identity networking/firewall requirements for migration systems | Customer Migration Team, Customer Network Team, and GitLab PSE |

## Phase 2 - Setup

Verify Congregate configuration is correct, and can access Source and Destination instances.  This can be accomplished by creating a Destination group/subgroup, and migrating a small/simple existing project from Source to Destination.

It is recommended to migrate or pre-provision all users via SCIM or SAML JIT as a first step.  This will enable user attribution. It is also recommended to migrate the group structure without projects first. This will reduce time spent for later migrations and enable user attribution. If SCIM is being used on the destination, user migration is not necessary, but can still be helpful. If users are migrated before SCIM is implemented, avatars and user ssh keys will be migrated. Then when SCIM is implemented, migrated users will be associated with the new SCIM user, assuming emails match. User Migration and attribution can be a fairly in depth topic, start reading about preparing users for migration [here](https://docs.gitlab.com/ee/user/group/import/index.html#prepare-user-accounts). Migrating users and groups should not impact any existing work, and can be done during work hours.

If any GitLab-Runner requirements were identified during Phase 1 - Planning, they should be implemented at this time.

### Audience

* Customer Migration Team
* Customer Infrastructure Team
* Customer Security Team
* GitLab Professional Services Engineer (PSE)

| Common Tasks                         | DRI                                                     |
| :----------------------------------- | :------------------------------------------------------ |
| Create Destination Test Group        | GitLab PSE                                              |
| Identify Sample Source Project       | Customer Migration and Security Team                    |
| Migrate Sample Project to Test Group | Customer Migration, Infrastructure Team, and GitLab PSE |
| Migrate Users and Groups             | Customer Migration Team and GitLab PSE                  |

## Phase 3 - Pilot Migrations

Work with identified Pilot Migration teams to migrate their projects during identified migration windows. If there are concerns about the teams being able to still work, consider migrating to a test group/subgroup first, so migrated projects can be tested without affecting day to day operations. Test the migrated projects by running User Acceptance on them. Possible items to check for User Acceptance could include issues, merge requests, merge request approval rules, repository commits, branches, etc. If any problems arise, fix the problem, and roll the fixes into the procedure. Once everything has been approved and demonstrated that work can continue, delete the group/subgroup, and migrate the projects to their normal home.

To help identify Pilot Projects, the Pilot Projects should be selected to identify technical and operational risks to be dealt with in this phase. It's important to select a wide range of users and projects for this phase, while still keeping the total number of projects small.

### Audience

* Customer Migration Team
* Customer Product Owners
* Customer Product SMEs
* GitLab Program Manager (PM)
* GitLab Professional Services Engineer (PSE)

| Common Tasks                         | DRI                                      |
| :----------------------------------- | :--------------------------------------- |
| Communicate Start of Pilot Migration | Customer Product Owners and GitLab PM    |
| Update Congregate Data               | Customer Migration Team and GitLab PSE   |
| Migrate Projects                     | Customer Migration Team and GitLab PSE   |
| Generate Reports                     | Customer Migration Team and GitLab PSE   |
| Archive Source Projects              | Customer Migration Team                  |
| Communicate End of Pilot Migration   | Customer Product Owners and GitLab PM    |
| User Acceptance Testing              | Customer Migration Team and Product SMEs |

## Phase 4 - Main Migrations

At this point, most problems should have been identified and fixed. Due to this feedback, migrations can start ramping up to larger collections of projects. Following the schedule identified in Phase 1, start performing migration waves during identified migration windows, adjusting schedule as necessary. If certain projects fail to migrate during the window, communicate the failure, and move the project to a later wave while troubleshooting is performed.

### Audience

* Customer Migration Team
* Customer Product Owners
* Customer Product SMEs
* Customer Product Developers
* GitLab Project Manager (PM)
* GitLab Professional Services Engineer (PSE)

| Common Tasks                           | DRI                                                                    |
| :------------------------------------- | :--------------------------------------------------------------------- |
| Communicate Start of Migration Wave    | Customer Product Owners and GitLab PM                                  |
| Update Data                            | Customer Migration Team and GitLab PSE                                 |
| Migrate Projects                       | Customer Migration Team and GitLab PSE                                 |
| Generate Reports                       | Customer Migration Team and GitLab PSE                                 |
| Archive Successful Source Projects     | Customer Migration Team                                                |
| Communicate End of Migration Wave      | Customer Product Owners and GitLab PM                                  |
| Migration Wave User Acceptance Testing | Customer Migration Team, Product SMEs, and Customer Product Developers |

## Phase 5 - Wrap Up

All automatic migrations should have happened by this point. Any projects not migrated by now, are considered failed automatic project migrations, and should be handled manually. Usually the number of failed projects in this phase is significantly small. Extra effort should be taken to identify why the projects are failing, and addressed as appropriate.

Decide what should be done with the source instance(s). Will they be retired, left running, archived, etc.?

### Audience

* Customer Migration Team
* Customer Product Owners
* Customer Product SMEs
* Customer Product Developers
* Customer Infrastructure Team
* Customer Security Team
* GitLab Project Manager (PM)
* GitLab Professional Services Engineer (PSE)

| Common Tasks                                     | DRI                                                                                    |
| :----------------------------------------------- | :------------------------------------------------------------------------------------- |
| Assess how to Reduce Project size and Complexity | Customer Product Developers, Product SMEs, and GitLab PSE                              |
| Develop Plan to Migrate Project                  | Customer Migration Team, Infrastructure, Security, Product Developers, and GitLab PSE  |
| Work with Affected Team to Schedule Migration    | Customer Product Developers, Product Owners, Migration Team, GitLab PSE, and GitLab PM |
| Migrate Project                                  | Customer Migration Team and GitLab PSE                                                 |
| Run Post-Migration Tasks Possible                | Customer Migration Team and GitLab PSE                                                 |
| Communicate End of Migration Wave                | Customer Product Owners and GitLab PM                                                  |
| Migration Wave User Acceptance Testing           | Customer Migration Team, Product Developers,  and Product SMEs                         |

# Pre and Post Migration Considerations

## General

This general document will highlight standardized suggestions towards what the users should expect to perform in their target environment. It should help guide them towards the correct decisions after switching to their SaaS version.

Note: These instructions primarily focus on GitLab-\>GitLab or GitHub-\>GitLab migrations using the "API methods"; Direct Transfer for GitLab to GitLab or the GitHub importer. "Migrations" using GEO replication or Backup/Restore methods have different concerns and will be covered in a separate document.

## Pre-Migration - Developers

Before a migration, individual engineers can take several steps to prepare themselves for the transition. Here's a list of actions they should consider:

### Familiarize Themselves with GitLab

Spend some time exploring GitLab's interface, features, and workflows. Take advantage of GitLab's documentation, tutorials, and online resources to become comfortable with the platform. If your engagement includes training, make sure to attend and get your certifications\!

### Review Project Repositories

Take an inventory of the repositories they own or contribute to on the source system. Assess the importance and status of each repository to help prioritize migration efforts.

### Backup Important Data

Make local backups of critical repositories. This ensures that essential information is preserved in case of any issues during the migration process. **Note**: Migrations are a non-destructive process, so the odds of this are exceedingly low

### Communicate with Teammates

Discuss the migration plan with teammates and collaborators to ensure everyone is aware of the upcoming changes. Coordinate efforts and address any concerns or questions they may have about the migration. Layout a communication plan for migration schedules

### Resolve Pending Tasks

Complete any many pending tasks as possible, such as open pull/merge requests or issues, before the migration begins. This helps prevent any disruptions or conflicts during the transition process.

### Update Local Workflows

If engineers use local development workflows that are integrated with the source system, such as Git commands or Git clients, they may need to update configurations or settings to work seamlessly with GitLab.

### Backup Personal Keys

Depending on the source system, SSH keys or GPG keys may not be included in the migration of users. While most users will already have back-ups of these items, we like to call them out for safety's sake

### Prepare CI/CD Configurations

If engineers are responsible for configuring CI/CD pipelines for their projects, they should familiarize themselves with GitLab's CI/CD configuration syntax and adjust their pipelines accordingly. Depending on the scope of your engagement, this may include pairing with GitLab engineers to develop conversion processes for other systems such as Jenkins or GitHub Actions.

### Test Workflows in GitLab

If possible, set up a test project or repository in GitLab to experiment with workflows, integrations, and features before the actual migration. This allows engineers to identify any potential issues or challenges early on.

### Provide Feedback

Throughout the migration process, share feedback with project managers, administrators, or GitLab support regarding any issues, bugs, or usability concerns encountered. This helps improve the migration experience for the entire team.

By proactively taking these steps, individual engineers can better prepare themselves for a smooth and successful migration, minimizing disruptions to their workflows and projects.

## Pre Migration - System

The first piece that should always be considered is the list of items migrated and not migrated.

* For GitLab via Direct Transfer those lists are here : [https://docs.gitlab.com/ee/user/group/import/](https://docs.gitlab.com/ee/user/group/import/)
* For GitLab via GitHub importer those lists are here : [https://docs.gitlab.com/ee/user/project/import/github.html](https://docs.gitlab.com/ee/user/project/import/github.html)

Note: Items not explicitly listed as imported or not imported should be assumed to **not** be imported

### GitLab Version Compatibility

For GitLab <=> GitLab migrations, ensuring that your source and destination GitLab instances meet version compatibility requirements is critical for a smooth migration. 

Refer to [compatibility section of the documentation](./famq.md#compatibility) to learn which version are compartible. 

* Failure to meet these compatibility requirements can lead to import failures or incomplete data transfer. Planning for any necessary upgrades on the source or destination instance should be a key part of the pre-migration system checks.


### Identification of resources

In the initial state of the GitLab migration it is important to identify all the pertaining resources outside the items being migrated. These could include external CI/CD resources and dependencies, container image registries, or even external libraries such as DSL code needing to be part of the common build environment. As part of the migration, integration tooling will also need to be revised and tested. These tools could be Jenkins, Jira or external build software such as CircleCI or Travis CI. It is advisable to also check any dependencies from external cloud providers.

Resources should be identified by Team Lead engineers. The following are the advisable tests and checks needing to be revised post migration.

### Users

* For most migrations to GitLab it is recommended to pre-provision users as this enables a more complete migration of the data.
  * For our multi-tenant SaaS offering, this may mean setting up SAML and SCIM for your namespace and allowing those tools to do the provisioning, either through first login (JIT) for SAML or via the usual SCIM push mechanics.
  * For our single-tenant SaaS offering and for self-managed, this may also mean enabling SCIM, or some other push mechanism for creating accounts from your user management SSoT.
* It is also necessary to set the public email for users on the **source** system
  * Note: For some systems, this is cannot be automated via an admin token and must be configured by individual users
* For GEO based migrations, the users are copied over as part of the synchronization process

### Hard-coded Dependencies

* URLs for source systems have likely changed.
  * Create a list of any hard-coded dependencies in build systems that require updating

### Networking

* Depending on the type of migration, there may be requirements to open up internal source systems to communications to/from GitLab instances (.com, Dedicated, self-managed). The primary culprits are:
  * GitLab to GitLab using Direct Transfer, GitHub to GitLab, or BitBucket to GitLab
    * The destination instance must be able to see the source instance
    * The migration VM (if applicable) must be able to see the source and destination instances
* Ensure your migration destination has access to systems that it will need to reach; integrations, build systems. Some examples include:
  * GitLab Runner
  * Jenkins
  * WebHooks in general
* Ensure your internal systems have external access to reach the destination system where needed
* Create a list of these integrations and verify that they coordinated
* **Create a full network diagram of all communication points**. This can help with planning on requirements as well as help in costing network usage
  * Consider integrations that are not specific to GitLab (eg: anything with .well-known or similar) such as OIDC connections

### Access and Permissions

* Review and update user access levels and permissions for groups and projects to align with organizational roles and responsibilities.
* Ensure that access controls are appropriately configured to maintain data security and compliance standards
* The majority of the security configuration is handled by the SAML/SSO/SCIM configuration
* If there is SAML authentication only, w/o SSO-only authentication enforcement, users with no SAML accounts will still be able to access the Group's resources
  * In that case, SAML is just another way to sign in to GitLab
* SSO-only authentication enforcement ensures that only users with a SAML account will be able to access a Group's resource
  * Users cannot be added as new members manually
  * Only existing users on the instance, who have a linked identity with the correct identity Provider, will be shown
  * GitLab will not look up the user directory on the idP to determine who to show
  * GitLab cannot and does not request information from the SAML provider
  * All the information is sent to GitLab from the SAML provider only when a user signs in successfully
  * **NOTE:** The setting may not be enabled during the migration to ensure the PS engineer has proper access to perform the migration tasks
* SCIM functionality is intended for automatic user provisioning and deprovisioning
  * It is a protocol that the IdP uses to tell GitLab what to do
* Other security options (*Settings > General > Permissions and group features*) are available, including:
  * *Restrict membership by email domain*
  * *Restrict access by IP address*
  * *Two factor authentication* - 2FA can be enforced in the group, but may be redundant if SSO-only authentication is already enforced as that usually requires a multi-factor authentication (MFA) element

### Domains (and BYOD)

Mostly for migrations to single-tenant SaaS (Dedicated):

* Will the customer need Bring Your Own Domain (BYOD) functionality?
* Will the customer utilize allowlists to limit access (create a private system)?
  * Related: Are their integrations that would require ***public access*** to this private system?

#### Action

* List the custom domain

### Email Systems

For migrations to single-tenant SaaS (Dedicated)

* Does the customer have any custom email FROM addresses? This is particularly important when utilizing BYOD

### Integrations and Dependencies

* This is the number one missed piece during migrations. Group/Project/Pipeline level integrations or dependencies missed during pre-migration inventory, including items like webhooks called out, above
* Running pilot migrations can help identify missed dependencies. Prioritize the most complex projects for these pilot runs to flesh out as many of these touch points as possible

#### Action

Create a list of all webhooks, integrations, dependencies

### Repositories

* For GitLab to GitLab scenarios, are you using repositories?
* Congregate can current migrate container registry and Maven, with NPM, PyPi, and Generic coming soon



## Pre Migration

### Schedule and Planning

As pointed out in [Phase 1](https://docs.google.com/document/d/1RkcL54BiSg6t26_2CYihTgG0Wauc9RzYSxYHoL9bTWI/edit#heading=h.ixzbami4hloi), the customer should work with GitLab to plan migration waves. GitLab can generate a wave planning file to assist with planning. Things to consider for this planning:

* Inter-project dependencies
* Project priority; are there project that must move sooner or later
* Organizational dependencies
* External dependencies; pipeline translations, new integrations or systems (container registry, CICD system retirement, etc)
* "Size"

### Communications

The customer teams will need to be notified of migration dates. This can be set as a range, initially (migrations will occur between X and Y) with specific dates being communicated after the migration waves are decided on.

### Determine Post-Migration Steps

Customers should also work with their internal teams and the GitLab delivery team to determine a post-migration "runbook" for the engineering teams. Some potential points in that document:

* Expectations post-migration; where to go, which URLs
* Validation steps to perform
* Git changes (some of which is included in this document)
* Project change; registry and repo paths, runner tagging
* How to test pipelines
* How to convert CI
* Support and contacts for issues (office hours, etc)

### Customer Coordinator

* Customer is to send out communications to their users.
* Users should be aware that all of their Gitlab projects are in the process of being migrated to Gitlab.com
* Specific teams of users should know the tentative dates of when their specific projects are to be migrated

### Scheduling and constraints

* Migration waves are comprised of about 200 projects and the total time for a migration takes about 8 hours to complete based on the size of the projects involved in the particular wave
* A migration wave is scheduled with a customer at least 5 days in advance in order to give the PSE time to ensure that no other customer migrations to GitLab.com will take place during the migration window

### App Teams {#app-teams}

* Check communications sent out by management to determine if any of their projects will be included in the next migration wave
* For projects included in the migration wave, make any last code changes, issues, merge requests, etc.. prior to the beginning of the migration wave
* Do not push any code changes or create any issues, merge requests, etc… until after management sends out a communication that the migration is complete
* Projects are only migrated once. If changes are made to the source self-managed instance during or after the migration, they will not be carried over to Gitlab.com
* Delete unused branches and tags on GitHub to allow the migration process to complete faster.
* Team members have requested access to GitLab and have a user account
* Team members can log into GitLab

## Post Migration

After migration there are things that engineers can do to validate the system. A list of some of these check-points is listed below. Some of these may be specific to GitLab to GitLab migrations and not relevant. Also, specific migration or conversion actions may be addressed in the [Customer-Specific Section](#customer-specific-section) at the end of this document

**Note**: not all features are available during all migrations. Check the links above if there are questions or discrepancies.

### Projects - Developers

As waves of migration are being completed, individual users should be testing their allocated projects as per the notice from their lead.

To test connectivity, Read & Write modes should be in scope. Test these with the following commands below:

* READ:
  * git ls-remote	 \<REPO\_URL\>
* WRITE:
  * cd \<MIGRATED\_CLONED\_REPO\_FOLDER\>
  * git remote -v
  * *Take a screenshot of your current remote url setting.*
  * git set-url origin git://\<REPO\_URL\>
  * git checkout -b migr-write-test
  * echo “foo\_bar” \> testfile.dat
  * git push --set-upstream origin migr-write-test
* GitLab will provide a quick link to create a Merge Request:
  * ...
    remote: To create a merge request for my-new-branch, visit:

    remote:   [https://gitlab.com/my-group/my-project/merge\_requests/new?merge\_request%5Bsource\_branch%5D=migr-write-test](https://gitlab.com/my-group/my-project/merge_requests/new?merge_request%5Bsource_branch%5D=migr-write-test)

* Feel free to copy and paste this link to create a merge request. This will also test your user attributes further.
* Members of user teams should test that they can re-pull their projects from Gitab.com
  * If they receive errors at this stage the most likely issues are:
    * They need to generate a new ssh token
    * They need to reauthenticate
* If a member of the user team is unable to push code the most common issues are:
  * They are still pushing to the old instance where the project is archived
  * They need to generate a new ssh token
  * They need to reauthenticate
* User teams should check on, among other things, the following elements of their projects on Gitlab.com:
  * The number of branches on a given project
  * The total number of merge requests
  * Their role on the given project
* If you use them, verify valid keys (ssh, gpt, etc) are in the new instance. If not, create new ones.

### Project Owners and Maintainers

* Review and adjust project level permissions, including Enable project-level shared runners (default: true) and AutoDevOps (default: true)
* Register any local runners that will be used for CI jobs
* Adjust group and project permissions, if applicable. Note: All groups and projects are set to private upon import (unless the group imports into a parent group and inherits its visibility), regardless of their setting in the source instance.
* If migrating to GitLab.com, update any project, group, and system hooks that point to localhost or a private instance - GitLab.com will see them as invalid and fail to create them
* Update any CI jobs, CI/CD variables, and hooks that point to the source system url; for GL-\>GL migrations, relative paths used in CI jobs to point to other projects should be fine, but any absolute paths/full urls will need to be updated to point to the projects at the destination instance url
* Verify dependency chains (build order) of projects
* Secrets (tokens) that may be present in certain features, e.g. hooks, are not exposed in the API response and therefore not migrated. Those individual features have to be newly created
* For GitLab to GitLab migrations, you will want to validate that projects shared with groups in the source instance are still shared in the destination. If the entire group structure is not migrated first, the shared groups will not be preserved in the destination instance
* Recreate group and project badges
* Recreate any instance and group level custom project templates
* Update and/or create any features that are not migrated (based on the migration features matrix ([Bitbucket](https://gitlab-org.gitlab.io/professional-services-automation/tools/migration/congregate/bitbucket-migration-features-matrix/), [GitHub](https://gitlab-org.gitlab.io/professional-services-automation/tools/migration/congregate/github-migration-features-matrix/), [GitLab](https://gitlab-org.gitlab.io/professional-services-automation/tools/migration/congregate/gitlab-migration-features-matrix/)))

### Unmigrated Project Features (GitLab to GitLab)

As stated, several features are not handled in a migration. While the specifics of how customers should handle these features is specific to their environments and needs, we attempt here to offer some ideas for how to handle these items in post-migration

#### Sensitive information

(List correct Feb 28, 2024)

Some items contain sensitive information and are not migrated by default. There are a few methods to deal with these.

* Some are handled by the [Congregate](https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate) migration tool (if it is being used). Consult the [supported features list](https://gitlab-org.gitlab.io/professional-services-automation/tools/migration/congregate/gitlab-migration-features-matrix/), here.
* Unsupported items from this category **will need to be recreated manually or via API**
* Unfortunately, these cannot be moved until after the project is created on the destination, so any pre-work will consist of preparing and testing any scripting

| Area                        | API if available                                                                                                                    |
| :-------------------------- | :---------------------------------------------------------------------------------------------------------------------------------- |
| CI/CD variables             | [https://docs.gitlab.com/ee/api/project\_level\_variables.html](https://docs.gitlab.com/ee/api/project_level_variables.html)        |
| Deploy keys                 | [https://docs.gitlab.com/ee/api/deploy\_keys.html](https://docs.gitlab.com/ee/api/deploy_keys.html)                                 |
| Deploy tokens               | [https://docs.gitlab.com/ee/api/deploy\_tokens.html](https://docs.gitlab.com/ee/api/deploy_tokens.html)                             |
| Pipeline schedule variables | [https://docs.gitlab.com/ee/api/pipeline\_schedules.html](https://docs.gitlab.com/ee/api/pipeline_schedules.html)                   |
| Pipeline triggers           |                                                                                                                                     |
| Project Webhooks            | [https://docs.gitlab.com/ee/api/projects.html\#list-project-hooks](https://docs.gitlab.com/ee/api/projects.html#list-project-hooks) |

#### Generally not supported

(List correct Feb 28, 2024)

* Some are handled by the [Congregate](https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate) migration tool (if it is being used). Consult the [supported features list](https://gitlab-org.gitlab.io/professional-services-automation/tools/migration/congregate/gitlab-migration-features-matrix/), here.
  * Of note (not exhaustive)
    * Container Registry
    * Maven, Generic, NPM, and PyPi packages
* Unsupported items from this category **will need to be recreated manually or via API**
* Unfortunately, these cannot be moved until after the project is created on the destination, so any pre-work will consist of preparing and testing any scripting

| Area                    | API if available                                                                                                                                                                                                                          |
| :---------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Agents                  | [https://docs.gitlab.com/ee/api/cluster\_agents.html](https://docs.gitlab.com/ee/api/cluster_agents.html)                                                                                                                                 |
| Container Registry      | [https://docs.gitlab.com/ee/api/container\_registry.html](https://docs.gitlab.com/ee/api/container_registry.html)  Note: This allows you to interact with the Container Registry, but not pull and push containers                        |
| Environments            | [https://docs.gitlab.com/ee/api/environments.html](https://docs.gitlab.com/ee/api/environments.html)                                                                                                                                      |
| Feature flags           | [https://docs.gitlab.com/ee/api/feature\_flags.html](https://docs.gitlab.com/ee/api/feature_flags.html) and [https://docs.gitlab.com/ee/api/feature\_flag\_user\_lists.html](https://docs.gitlab.com/ee/api/feature_flag_user_lists.html) |
| Infrastructure Registry |                                                                                                                                                                                                                                           |
| Package registry        | [https://docs.gitlab.com/ee/api/packages.html](https://docs.gitlab.com/ee/api/packages.html)                                                                                                                                              |
| Pages domains           | \*Delete only API exists                                                                                                                                                                                                                  |
| Remote mirrors          | [https://docs.gitlab.com/ee/api/remote\_mirrors.html](https://docs.gitlab.com/ee/api/remote_mirrors.html)                                                                                                                                 |

### Unmigrated Project Features (GitHub to GitLab)

It is more difficult to gauge the effort needed for GitHub to GitLab, as we publish what *is* migrated and not a list of what is not. For GitHub, it's more along the "metadata" of individual repos; commits, branches, PRs, and issues as already covered in other sections.

### CI/CD Pipelines

* Verify the migration of CI/CD pipelines and jobs to GitLab and confirm their functionality. This includes runner/build engine connectivity (GitLab runner, Jenkins integration)
* Optimize pipelines for performance and reliability, considering factors such as parallelism, caching, and resource utilization.
* Generic things that we suggest to test in order to put an approval stamp on the migrated project.
  * Automated builds.
  * Unit Testing
  * Integration Testing
  * Automated Deployment
  * Monitoring and Reporting
  * Deploying to Production
* Post pipeline verification it is advisable to check on all deployed artifacts.

### Issue Tracking and Boards

* Spot check the migration of issues, epics, and boards from the previous system to GitLab. The importers and Congregate will produce a list of "failed relationships" that should cover this, but a spot check that they look good, have the proper attribution, etc should also be performed
* Spot check issue boards and labels as needed to streamline project management and tracking.

### Merge Requests

* Spot check the migration of merge requests The importers and Congregate will produce a list of "failed relationships" that should cover this, but a spot check that they look good, have the proper attribution, are linked to the proper branches, and you can reach those branches from the MR should also be performed

### Wikis and Documentation

* Ensure that wikis and documentation have been migrated successfully and are accessible to relevant team members.
* Encourage the ongoing contribution and maintenance of documentation to facilitate knowledge sharing and collaboration.

### Integrations and Tooling

* **INTEGRATIONS AND WEBHOOKS DO NOT MIGRATE**. Please know that you will need to reconfigure these at the instance/group/project level ***after*** migration

### Security and Compliance

* Review group security settings and configurations in GitLab to ensure adherence to organizational policies and industry regulations. This can include items like SCIM/SAML configuration and IP Allowlist
* Implement necessary security measures, such as vulnerability scanning, access controls, and compliance checks.

### Badges

* Review imported badges to ensure they are correctly applied to repositories, reflecting project status, quality, or other relevant metrics.
* Consider creating new badges or updating existing ones to align with your organization's objectives and key performance indicators.

### Boards and Board Lists

* Validate the migration of boards and board lists to GitLab, ensuring that they accurately represent project workflows and statuses.
* Customize board lists as needed to accommodate your team's specific requirements and processes.

### Epics

* Verify the migration of epics to GitLab and confirm their associations with respective projects and groups.
* Organize epics effectively, grouping related tasks and initiatives to provide clarity and visibility into project priorities.

### Group Labels

* Review imported group labels and ensure they are appropriately categorized and applied to projects within the group.
* Standardize label usage across groups and projects to facilitate consistent tracking and reporting.

### Iterations and Iteration Cadences

* Confirm the migration of iterations and iteration cadences to GitLab, allowing teams to plan and track work within defined timeframes.
* Establish iteration cadences that align with your organization's sprint or release schedules, promoting predictability and accountability in project delivery.

### Members

* Validate the migration of members to GitLab, ensuring that all relevant team members have appropriate access and permissions within groups and projects. If you are using SCIM provisioning, this should happen when a user first logs into the system
* Communicate any changes in membership or roles to affected individuals and provide necessary training or support as needed.

### Group Milestones and Release Milestones

* Verify the migration of group milestones and release milestones to GitLab, enabling teams to track progress and align activities with overarching project goals.
* Utilize milestones effectively to set targets, prioritize tasks, and coordinate cross functional efforts within groups and projects.

### Namespace Settings

* Review namespace settings in GitLab to ensure they align with your organization's governance policies and preferences.
* Customize settings such as visibility, permissions, and repository configurations to meet specific project requirements and security standards.

### Uploads

* Validate the migration of uploads, including files, images, and other attachments, to GitLab to maintain data integrity and accessibility.
* Ensure that uploaded files are correctly linked and accessible within relevant project repositories, wikis, or issues.

## Common Post Migration Issues

Most of the issues are already covered above in the checks. In general, the typical problems are:

| Concern                                                     | Description                                                                                                                                                                                                           | Supported By                                                                                                                                               |
| :---------------------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------- |
| System-level access for individuals                         | Usually pointing to SAML/SCIM issues Could also be a problem with IP allowlists or domain restrictions for the instance/namespace                                                                                     | GitLab for configuration Customer teams for configuration in their source identity system                                                                  |
| Basic permissions at the namespace, group, or project level | Also usually a SAML/SCIM issue, or an issue with a user email name bound to their user account,  but can point to a migration issues if permissions were not added to the specific project                            | GitLab for configuration Customer teams for configuration in their source identity system                                                                  |
| Issues with git origin, called out in the above             | Called out above                                                                                                                                                                                                      |                                                                                                                                                            |
| Runner/jobs not getting picked up                           | This can be from private runners not yet being registered, or tagging of the pipeline. Customer should check with their operations teams Users can also check the runner inheritance settings for groups and projects | GitLab for configuration GitLab for pipeline advisory Customer teams for configuration or specifics                                                        |
| Integrations                                                | Jira, Jenkins, or other systems. Check the tokens on the integrations themselves. Otherwise, it may be a network connection issue outside the scope of this documentation                                             | GitLab for configuration of the integrations from the GitLab side Customer teams for configuration on the destination side of the integration or specifics |
| Missing data                                                | A catch-all for missing data; repos, pipelines, commits, metadata related to a project *not* covered in the missing features above                                                                                    | GitLab                                                                                                                                                     |

## Customer-Specific Section

As we customize this document for individual customers, additional data will be added here. This can include pre/post information, found issues, support links

### Additional Pre Migration Concerns

### Additional Post Migration Steps and Checks

### Post Migration Support Plan

# FAQ

Check out our [migration FAQ document](https://gitlab.com/gitlab-org/professional-services-automation/delivery-kits/migration-template/-/blob/master/customer/famq.md?ref_type=heads) to understand more individual aspects of a GitLab Professional Services Migration engagement.

# Links

* [Migration Delivery Kit](https://gitlab.com/gitlab-org/professional-services-automation/delivery-kits/migration-template)
* [Congregate](https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate)
* [GitLab Imports](https://docs.gitlab.com/ee/user/project/import/)