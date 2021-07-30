## Customer Migration Change Management

As you prepare for the migration, it will be important to set appropriate expectations with end users.  Here are some guidelines for appropriate change management and communication.

### Communication Mechanisms and Timing
- If migrating from a self-managed GitLab source instance, consider using a [broadcast message](https://docs.gitlab.com/ee/user/admin_area/broadcast_messages.html) to broadcast the overall dates of the migration
- Send an email message to end users several weeks before the migration starts to set expectations at a high level  
- Follow up with specific teams a week before their migration, and again 1-2 days before their projects will be migrated
   - some customers choose to have live Q&A sessions with teams prior to their projects being migrated
   - others primarily use async communications and answer questions received via wiki, issue, or other asynchronous collaboration mechanism
- Consider sharing the [FAMQ](customer/famq.md) in a shared location - you can add your own specific details to the draft provided to make it your own

### Information to Share with End Users
- Date and time of the migration window that their project is scheduled in
- General expectations:
   - Source system will be unavailable during the migration window; users should plan to pull latest code and work via git local clone during the migration window
   - Post migration, it is expected that projects will be accessed directly in the new instance; the old instance project will be archived once migration validation is complete
   - After the migration, users can access their GitLab projects at `<specify new url>`; _Note: if the login mechanism has changed, provide details to the end users about how to authenticate to GitLab (e.g. SSO via okta)_
   - End users should update their git remote url for their local clone as soon as the migration is complete
   - If users are migrated from GitLab to GitLab, their SSH keys will be migrated; if migrating from a different source system, a new SSH key will need to be created post-migration
   - Some additional post-migration clean up might need to happen before the project is back to a completely clean state
   - Personal access tokens (PAT) will need to be recreated post-migration and anything that uses a PAT will need to be updated to use the new PAT
- Activities for project owners and maintainers to do in preparation for the migration:
   - Familiarize yourself with the migration features (([Bitbucket](customer/bitbucket-migration-features-matrix.md), [GitHub](customer/github-migration-features-matrix.md), [GitLab](customer/gitlab-migration-features-matrix.md))) - it will be important to have a plan to manually recreate/resolve any features that are not migrated from the source to the destination instance
   - Review the post-migration checklist below and do any analysis of what will need to be updated for each specific project post-migration

### Post-migration checklist for project owners and maintainers
- [ ] Review and adjust project level permissions, including `Enable project-level shared runners` (default: true) and `AutoDevOps` (default: true)
- [ ] Register any local runners that will be used for CI jobs
- [ ] Adjust group and project permissions, if applicable.  _Note: All groups and projects are set to private upon import (unless the group imports into a parent group and inherits its visibility), regardless of their setting in the source instance._
- [ ] If migrating to SaaS, update any project, group, and system hooks that point to localhost or a private instance - GitLab.com will see them as invalid and fail to create them
- [ ] Update any CI jobs, CI/CD variables, and hooks that point to the source system url; for GL->GL migrations, relative paths used in CI jobs to point to other projects should be fine, but any absolute paths/full urls will need to be updated to point to the projects at the destination instance url
- [ ] Secrets (tokens) that may be present in certain features, e.g. hooks, are not exposed in the API response and therefore not migrated. Those individual features have to be newly created
- [ ] For GitLab to GitLab migrations, you will want to validate that [projects shared with groups](https://docs.gitlab.com/ee/user/project/members/share_project_with_groups.html#sharing-a-project-with-a-group-of-users) in the source instance are still shared in the destination.  If the entire group structure is not migrated first, the shared groups will not be preserved in the destination instance 
- [ ] Recreate group and project [badges](https://docs.gitlab.com/ee/user/project/badges.html)
- [ ] Recreate any instance and group level custom project templates  
- [ ] Update and/or create any features that are not migrated (based on the migration features matrix ([Bitbucket](customer/bitbucket-migration-features-matrix.md), [GitHub](customer/github-migration-features-matrix.md), [GitLab](customer/gitlab-migration-features-matrix.md)))
 
