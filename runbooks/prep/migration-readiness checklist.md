# Migration Readiness Checklist
Welcome to a GitLab Professional Services Migration Engagement. This document is meant to help customers prepare for the migration project ahead.

## Terminology
- Project = source code repository + additional data like merge requests, agile planning issues, container/packages
- Group = a collection of 1 or more Projects. A Group has its own membership scheme that is inherited by subordinate projects. 
- User = an account on the gitlab system
- Member = a user assigned to a group or a project
- Wave = A List of projects and/or groups, represented in a spreadsheet or CSV file format, that will be migrated to the destination gitlab system, at a scheduled date/time.
- PS = Shorthand for Professional Services, i.e GitLab PS.

## Migration Planning Team - Access
- GitLab PS will need system admin access to the source system with admin access tokens. 
- Gitlab PS will need system admin access (self managed) or group admin access (SaaS) on the destination GitLab system.[^1]
[^1]: Migrations to gitlab.com will require GL provisioned VM and User Account. The customer might need to add this user to their group. 

## Migration Planning Team - Communication 
- Wave execution status and status updates will be communicated by the GitLab PS team to the Migration Planning Team as required. The actual migration can be a bit mundane, so using async communication via Slack is the preferred method.
- End user communication is the responsibility of the customer. This includes notification of intent to migrate, and answering questions that the end users might have (more below)

##  Migration Planning Team - User migration planning
Best practice is to create user accounts on the destination GitLab system first. The GitLab PS team will use automation to query the source system(s) to get a list of all users that need to be migrated. User details should be accurate on the source systems, especially email. There should be no personal or fake emails entered for a given user. This is a hard requirement for GitHub.[^github-1]  If you have a list of username, full name, and email address in a file, this can be used as an audit check to the list automatically retrieved from the source system.

[^github-1]: If your source system is GitHub **make sure your users have their official email address in the [public email address](https://docs.github.com/en/github/setting-up-and-managing-your-github-user-account/managing-email-preferences/setting-your-commit-email-address#setting-your-commit-email-address-on-github) on their github user account**. 

## End User Application Teams - Migration Preparation
If the source system is GitLab and teams are using GitLab CI, application teams should audit their gitlab-ci.yml files to ensure that no absolute urls used in CI/CD scripting. If unmitigated, the project's ci/cd automation will be broken post-migration. Prior to migration, absolute paths should be remediated with relative paths and [predefined variables](https://docs.gitlab.com/ee/ci/variables/predefined_variables.html).

## Migration Planning Team - Wave Planning
To prove out the data migration integrity, network connectivity, access tokens, etc., GitLab PS suggests a "Pilot Migration" wave with a customer identified "Early Adopter" team. The Early Adopter team will identify sample projects for migration that will represent the widest possible customer use cases. The Early Adopter team will be quality control; validating data integrity, post-migration experience, and desired results of the Pilot Migration. Once GitLab PS gets customer approval of this Pilot Migration, the remaining migration waves can move forward. 

Migration of projects is complicated and resource intensive, so we break it up into manageable waves. Customers should start to think about how to group projects into migration waves. Often this can be by;
- Portfolios, so applications that might have dependencies on each other migrate together.
- Technology stack, so common development practices can be emphasized upon arriving at the new gitlab system.
- Or some combination of the previous.

Depending on the source/destination system combination, the number of projects per wave can vary between 200 up to many thousands. Make sure to ask the PS team approximately how many projects can be migrated per wave. 

During execution of a migration wave, changes to the source system should be limited as best as possible.  Some examples could include `git push` or UI editing of a project.  These restrictions are meant to maintain a single source of truth for the project while data is being imported to the destination GitLab system. It is best practice for the customer to communicate [code freeze](https://en.wikipedia.org/wiki/Freeze_(software_engineering)) windows to their application teams prior to the teams migration wave, indicating when the wave is scheduled, followed by a reminder message when the migration wave is about to begin. Its a good idea to setup a support or Q&A chat channel for end users to ask questions and to coordinate any exceptions if necessary. 

## End User Application Team - Post Migration Checks
- [ ] Customer Application teams should check their source code for total number of commits, branches, tags, and disk space as noted at the top of a project. Sometimes the number of tags is slightly off as certain source systems (GitHub) treat releases and tags slightly differenlty than GitLab Does. 
- [ ] The total number of merge requests should be spot checked. Inside a few merge requests, teams should ensure merge request comments, merge user, and merge approver are appropriately attributed to user accounts. If the import process could not find the user accoust to attribute these to, it will default to the user whose token was used to perform the migration. 
- [ ] Total number of issues. Comments within issues are appropriately attributed to users. 
- [ ] Total number of Containers and packages if applicable. 
- [ ] User Membership per project and/or group. 
- [ ] Re-register project or group-specific CI/CD runners (if applicable)
- [ ] Run one or more jobs from the application's CI/CD pipeline. 

## Migration Planning Team - Post Migration Considerations

After the migration wave is complete, the source system project(s) will usually be archived or marked as read-only by the GitLab PS team. This is to prevent any accidental writes to the source project, as this would cause a divergence with the destination GitLab system.  

## Specific Considerations

- From a central governance perspective, Customers should think about CI/CD, project, and issue templates that can be reused across application teams. They should consider the practice of accepting contributions to the standardized templates to promote a good developer experience.
- Group and specific runners will need to be registered to the project on the destination instance after migration.

## Getting the most out of your investment

If the customer is coming to GitLab from a different SCM system, consider [GitLab education services](https://about.gitlab.com/services/education/) to best enable your end users to get the most out of gitlab. Specifically, you can consider [GitLab with Git basics](https://about.gitlab.com/services/education/gitlab-basics) and [GitLab CI/CD Training](https://about.gitlab.com/services/education/gitlab-ci) - both of which are offered as Instructor Led Training or via our GitLab Learn platform.

