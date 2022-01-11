# Migration Metrics

Various migration metrics are generated while running congregate. These are the primary generated files:

## During runtime

- congregate.log
  - The application log for congregate. This is a fairly verbose log containing the status of the migration
- audit.log
  - This log contains any POST, PUT, or DELETE requests made and their subsequent payloads

## After dry run

- dry_run_user_migration.json
  - Contains all POST, PUT, and DELETE requests to be made before a user migration
- dry_run_group_migration.json
  - Contains all POST, PUT, and DELETE requests to be made before a group migration
- dry_run_project_migration.json
  - Contains all POST, PUT, and DELETE requests to be made before a project migration

When a dry run finishes, congregate calls [add_post_migration_stats](../congregate.helpers.html#congregate.helpers.migrate_utils.add_post_migration_stats) to generate a quick summary of all POST/PUT/DELETE requests to be made during a migration and the total number of POST/PUT/DELETE requests.

## After migration

- user_migration_results.json
  - Results generated following the migration in JSON format
- user_migration_results.html
  - Diff report containing user differences found between source and destination instances
- user_diff.json
  - The JSON used to generate `user_migration_results.html`
- group_migration_results.json
  - Results generated following the migration in JSON format
- group_migration_results.html
  - Diff report containing group differences found between source and destination instances
- user_diff.json
  - The JSON used to generate `group_migration_results.html`
- project_migration_results.json
  - Results generated following the migration in JSON format
- project_migration_results.html
  - Diff report containing project differences found between source and destination instances
- user_diff.json
  - The JSON used to generate `project_migration_results.html`
- migration_rollback_results.html
  - Diff report containing an expected accuracy of 0 since all data was rolled back. If this is not showing an accuracy of 0, not all data was successfully removed

When a migration finishes, congregate calls [add_post_migration_stats](../congregate.helpers.html#congregate.helpers.migrate_utils.add_post_migration_stats) to generate a quick summary of all POST/PUT/DELETE requests made during a migration and the total number of POST/PUT/DELETE requests.
