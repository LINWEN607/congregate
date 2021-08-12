# Migration Wave Considerations

## What is a wave?

A wave consists of users, groups, and projects slated to be migrated within a day. A wave can consist of multiple users, groups, and projects.
Users i.e. their entire accounts (with additional GitLab features, e.g. SSH and GPG keys) mentioned in the migration features matrix ([Bitbucket](customer/bitbucket-migration-features-matrix.md), [GitHub](customer/github-migration-features-matrix.md), [GitLab](customer/gitlab-migration-features-matrix.md)) are migrated first. Users need to be migrated before we migrate groups and projects so that the user contribution mappings and permissions persist when we import groups and projects.  The number users in a user migration wave or projects in a group/project wave depends on the source and destination system.  When scheduling migrations, we typically plan to migrate 1 wave per day.

## GitLab to GitLab Migration

Users are typically migrated in waves of 500 per day.  User accounts might not need to be migrated if LDAP or SSO has been implemented on the destination system.  In that case, however, additional GitLab attributes associated with the user account, such as SSH and GPG keys, will not be migrated and must be manually recreated.

When migrating a group, it should be at the top level whenever possible.  With GitLab export/import functionality, a group and its subgroups and projects are migrated together and the group hierarchy and project alignment to those groups is retained. Breaking it apart over multiple waves complicates the process and is a time sink. GL->GL migrations are typically capped at 200 projects per wave.  So it is important to find a group with 200 or fewer projects to migrate.

From an organization perspective, if you have groups set up in GitLab to consist of specific teams, then you are in good shape. Pick the teams you want to migrate in the order that best suits your schedule, and we can accommodate it. If your groups are scattered and the structure is all over the place, find what groups fit best within a wave by use case.

If choosing multiple groups per wave, you should consider these attributes:

- groups containing projects that depend on each other for build/CI success
- groups containing projects that similar sets of users interact with, e.g groups representing project sets in a single product portfolio or business unit

<!--### Other Git Source to GitLab Migration-->
