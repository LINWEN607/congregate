# Pre and Post Migration Work

## Related Links

- [Customer Migration Change Management](https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate/-/blob/master/customer/customer-migration-change-management.md#post-migration-checklist-for-project-owners-and-maintainers)
- [Migration Readiness](./migration-readiness-checklist.md)
- [Frequently Asked Migration Questions](https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate/-/blob/master/customer/famq.md#what-are-a-customers-obligations-and-responsibilities-prior-during-and-after-a-migration)

## Pre-Migration

### General

#### Users and SSO Configuration

- The first active step in a migration is making sure that all of a customers active users exist on Gitlab.com, this is typically done via a mass import from an SSO application that the customer manages
- Users need to exist on Gitlab.com prior to migration so issues, merge requests, comments, etc.. are attributed to the correct user based on the email address associated with their account
  - Note: Users on the *source* system must have a public email visible for attribution to work
    - GitLab source can do this via API
    - GitHub souce requires each user to do this step, manually

#### Security Configuration

- The majority of the security configuration is handled by the SSO configuration as only SAML authenticated users can access the customers top-level group on gitlab.com
- Other security options are available including:
  - Ip allowlisting: Settings > General > Restrict access by IP address
  - Restricted access based on email domain: Settings > General > Restrict membership by email domain

#### Migration Wave File

- Once the PSE has access to the customer’s gitlab instance they will generate a file called wave-file.csv
- This file lists out every gitlab project on the customer’s instance and includes an unpopulated wave# and wave date column for each project
- The customer is responsible for choosing which projects are apart of each wave
- Once a wave is set, the PSE will import this information into the migration tool

### Customer Coordinator

- Customer is to send out communications to their users.
- Users should be aware that all of their Gitlab projects are in the process of being migrated to Gitlab.com
- Specific teams of users should know the tentative dates of when their specific projects are to be migrated

#### Scheduling and Constraints

- Migration waves are comprised of about 300-500 projects and the total time for a migration takes about 8 hours to complete based on the size of the projects involved in the particular wave
- The PSE should be given enough time to ensure that no other customer migrations to GitLab.com will take place during the migration window.

### App Teams

- Check communications sent out by management to determine if any of their projects will be included in the next migration wave
- For projects included in the migration wave, make any last code changes, issues, merge requests, etc.. prior to the beginning of the migration wave
- Do not push any code changes or create any issues, merge requests, etc… until after management sends out a communication that the migration is complete
- Projects are only migrated once. If changes are made to the source self-managed instance during or after the migration, they will not be carried over to Gitlab.com
- Delete unused branches and tags on GitHub to allow the migration process to complete faster.
- Team members have requested access to GitLab and have a user account
- Team members can log into GitLab

## Post-Migration

### Customer Coordinator

- Announce migration status; complete, re-migrating, delayed
- Act as SPoC for teams as they validate the migration

### App Teams

### Users

- Members of users teams should [update their git upstream origin](https://git-scm.com/docs/git-remote) on all of their local repositories
- Members of user teams should test that they can re-pull their projects from Gitab.com
  - If they receive errors at this stage the most likely issues are:
    - They need to generate a new ssh token
    - They need to reauthenticate
- If a member of the user team is unable to push code the most common issues are:
  - They are still pushing to the old instance where the project is archived
  - They need to generate a new ssh token
  - They need to reauthenticate
- User teams should check on, among other things, the following elements of their projects on Gitlab.com:
  - The number of branches on a given project
  - The total number of merge requests
  - Their role on the given project
- If you use them, verify valid keys (ssh, gpt, etc) are in the new instance.  If not, create new ones.

### Project Owners and Maintainers

- Review and adjust project level permissions, including Enable project-level shared runners (default: true) and AutoDevOps (default: true)
- Register any local runners that will be used for CI jobs
- Adjust group and project permissions, if applicable. Note: All groups and projects are set to private upon import (unless the group imports into a parent group and inherits its visibility), regardless of their setting in the source instance.
- If migrating to GitLab.com, update any project, group, and system hooks that point to localhost or a private instance - GitLab.com will see them as invalid and fail to create them
- Update any CI jobs, CI/CD variables, and hooks that point to the source system url; for GL->GL migrations, relative paths used in CI jobs to point to other projects should be fine, but any absolute paths/full urls will need to be updated to point to the projects at the destination instance url
- Verify dependency chains (build order) of projects
- Secrets (tokens) that may be present in certain features, e.g. hooks, are not exposed in the API response and therefore not migrated. Those individual features have to be newly created
- For GitLab to GitLab migrations, you will want to validate that projects shared with groups in the source instance are still shared in the destination. If the entire group structure is not migrated first, the shared groups will not be preserved in the destination instance
- Recreate group and project badges
- Recreate any instance and group level custom project templates
- Update and/or create any features that are not migrated (based on the migration features matrix ([Bitbucket](https://gitlab-org.gitlab.io/professional-services-automation/tools/migration/congregate/bitbucket-migration-features-matrix/), [GitHub](https://gitlab-org.gitlab.io/professional-services-automation/tools/migration/congregate/github-migration-features-matrix/), [GitLab](https://gitlab-org.gitlab.io/professional-services-automation/tools/migration/congregate/gitlab-migration-features-matrix/)))

#### Updating and Running Pipelines

- In many cases pipelines contain specific hooks that point to various resources or other locations with the project structure
- If any hooks are pointing to a private instance or localhost for example, which is not accessible from the destination instance (eg: gitlab.com) the instance will see them as invalid and fail when creating them.
  - Members of the user teams should update these hooks project and group CI/CD variables are migrated, but values that are source specific, e.g. project url or hostname, should be updated to the new values
- Secrets (tokens) that may be present in certain features, e.g. hooks, are not exposed in the API response and therefore not migrated. Those individual features have to be newly created
- There may be other elements of your pipelines that need to be updated depending on your pipeline and underlying tech-stack but the previous examples are at least what you can expect to need to update
- If you are using an external system for CI/CD, such as Jenkins or Circle CI, make sure that system is functioning properly and picking up changes.
  - How is the external system made aware of changes to SCM?  Push/Pull rules? Web Hooks? Integration?  Make sure those connections are present and working.
  - Change any hard coded URL’s that might point at an old SCM instance.
- If needed, modify Jenkinsfile(s) to point to libraries that are backed by GitLab

#### Establish integrations for other dependencies

- Terraform Cloud
- Jira
- Teams - https://docs.gitlab.com/ee/user/project/integrations/microsoft_teams.html

## What typically needs to be "fixed" in a migrated project?

Certain GitLab features are migrated but not adapted to the destination instance. These should be manually updated:

### Instance, group, sub-group and project level Runner registration

- Group level runners can be manually (via UI - Settings -> CI/CD -> Runners) enabled/disabled as of 13.5
- Enable project-level shared runners (default: true)
- Disable AutoDevOps (default: true)

### Project, group and system hooks

- **NOTE:** If they are pointing to a private instance or localhost gitlab.com will see them as invalid and fail creating them
- Badges
