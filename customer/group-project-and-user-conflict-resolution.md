## Group, Project, and User Conflict Resolution

Occasionally, during the migration process, project and user conflicts will arise.

GitLab requires a unique Name, Username and Email (primary email matching the one on source)
A user conflict occurs when a user with the same Username, but different Name and Email already exists on destination.   The Professional Services Engineer (PSE) will ask you to provide a suffix that can be added to conflicting usernames so that they can be successfully migrated to the destination, as `<username>_<suffix>`

A group conflict means that a group already exists at the same path (full hierarchy from top level group) in the destination instance as the source instance.  In these cases, we will want to rename the group in the source instance to resolve the conflict.

A project conflict means that a project already exists at the same path (full hierarchy from top level group) in the destination instance as the source instance.  In these cases, we will want to rename the project in the source instance to resolve the conflict.
