<!-- 
    Copy the contents of this runbook into an issue when running through a migration wave.
    Post the link to the issue on the slack channel dedicated to this migration. 
-->

# <customer name> Migration Wave <insert-number-here>

This runbook covers the process of migrating a wave of **groups and projects** from a source GitLab instance to a destination GitLab instance. This is assuming all users have already been migrated.

## Migration Blackout Period

<!--
    Specify the date and time of this migration wave. For example

    3:00PM 4/13/20 - 3:00AM 4/14/20
-->

## Slack channel for communication

<!--
    Provide the name and link of the slack channel dedicated to communicating the status and events of the migration
-->

## Points of contact

<!--
    Provide the gitlab handles for the various people involved in this migration wave and their specific role in the migration. 
    
    For example:

    @leopardm: PSE conducting the migration
    @lyle: Support Manager with Rails Console access
    @pharrison: Security Manager in the loop in case anything goes wrong
-->

## Groups to migrate

<!-- 

Copy the following data and add subsequent columns for wave migration or nested group migration

| Completed | Group Name | Total Projects   | Group Size   |
| --------- | ---------- | ---------------- | ------------ |
| :x:       | [name]     | [total-projects] | [group-size] |

Copy the following data and add subsequent columns for single group migration

| Completed | Project Path | Repo Size        |
| --------- | ------------ | ---------------- |
| :x:       | [name]       | [total-projects] |

-->

<sub>

**Key**

* :x: = not started 
* :heavy_minus_sign: = in progress
* :white_check_mark: = finished

</sub>

## Professional Services Steps to Complete Migration Wave

### Preparation

* [ ] Review migration schedule (see customer migration schedule)
* [ ] Check the status of the destination instance
    * In the case of gitlab.com, check https://status.gitlab.com/
    * A manual spot check of the instance
        * [ ] Confirm you can reach the UI of the instance
        * [ ] Confirm you can reach the API through cURL or a REST client
* [ ] Run `congregate list` at the beginning of the migration blackout period
* [ ] Stage projects based on the wave schedule in the UI
* [ ] Stage groups based on the wave schedule in the UI
* [ ] Create a directory called "waves" in `/opt/congregate/data` in the container if it doesn't already exist
* [ ] Create a directory called `wave_<insert_wave_number>` in `/opt/congregate/data/waves` if it doesn't already exist
* [ ] Copy all staged data to `/opt/congregate/data/waves/wave_<insert_wave_number>/`
* [ ] Notify in the internal slack channel dedicated to this migration you have completed preparation for the wave

### Dry run

* [ ] Run the following command: `nohup ./congregate.sh migrate --skip-users > data/waves/wave_<insert_wave_number>/wave_<insert_wave_number>_dry_run.log 2>&1 &`
* [ ] Confirm everything looks correct and move on to the next step in the runbook
    * Specifically, review the API requests and make sure the paths look correct. For example, make sure any parent IDs or namespaces are matching the parent ID and parent namespaces we have specified in the congregate config.
    * If anything looks wrong in the dry run, make a note of it in the issue and reach out to @pprokic or @leopardm for review. Do not proceed with the migration if the dry run data looks incorrect. If this is incorrect, the data we send will be incorrect.
* [ ] Attach the dry run logs (`data/dry_run_*_migration.json`) to this issue
* [ ] Copy the dry run logs to `/opt/congregate/data/waves/wave_<insert_wave_number>/`
* [ ] Notify in the internal slack channel dedicated to this migration you have completed preparation for the wave

### Migration

* [ ] Notify in the internal slack channel dedicated to this migration you are starting the migration wave
* [ ] Notify the customer in the customer-facing slack channel you are starting the migration wave
* If migrating to `gitlab.com`:
  * [ ] Export only by running the following command: `nohup ./congregate.sh migrate --skip-users --skip-group-import --skip-project-import --commit > data/waves/wave_<insert_wave_number>/wave<insert-wave-here>.log 2>&1 &`
  * [ ] Import only with single (1) process by running the following command: `nohup ./congregate.sh migrate --processes=1 --skip-users --skip-group-export --skip-project-export --commit >> data/waves/wave_<insert_wave_number>/wave<insert-wave-here>.log 2>&1 &`
* If migrating to self-managed:
  * [ ] Run the following command `nohup ./congregate.sh migrate --skip-users --commit > data/waves/wave_<insert_wave_number>/wave<insert-wave-here>.log 2>&1 &`
* [ ] Monitor the wave periodically by running `tail -f data/waves/wave_<insert_wave_number>/wave<insert-wave-here>.log`
* [ ] Attach `data/congregate.log`, `data/audit.log`, and `data/waves/wave_<insert_wave_number>/wave<insert-wave-here>.log` to this issue
* [ ] Copy `data/congregate.log`, `data/audit.log`, and `data/waves/wave_<insert_wave_number>/wave<insert-wave-here>.log` to `/opt/congregate/data/waves/wave_<insert_wave_number>/`

### Post Migration

* [ ] Notify in the internal slack channel dedicated to this migration you are running the diff report
* [ ] Run `nohup ./congregate.sh generate-diff --staged > data/waves/wave_<insert_wave_number>/diff<insert-wave-here>.log 2>&1 &` to generate the various diff reports
* [ ] Reach out the whoever has rails console access to the destination instance and have them run the following script where `group_paths` is a list of all expected full_paths for this migration wave:

```ruby
group_paths = ['root_group/group-1', 'root_group/group-2', '...']

groups = group_paths.map { |path| Group.find_by_full_path(path) }
projects = groups.map(&:projects).flatten

import_failures = projects.map(&:import_failures).flatten
import_failures_count = import_failures.count
mr_import_failures = import_failures.select { |failure| failure.relation_key == 'merge_requests' }
services_import_failures = import_failures.select { |failure| failure.relation_key == 'services' }
protected_branches_import_failures = import_failures.select { |failure| failure.relation_key == 'protected_branches' }

p "Total number of import failures: #{import_failures_count}"
p "Number of Merge Request import failures: #{mr_import_failures.count} (this figure might not be actual amount of missing MRs)"
p "Number of Services import failures: #{services_import_failures.count}"
p "Number of Protected Branches import failures: #{protected_branches_import_failures.count}"
```

* [ ] Review the diff reports (`data/*_results.html`) once they are finished generating
    * Review the following:
        * Overall accuracy of groups and projects
        * Individual accuracy of each group and project
        * Confirm correct group and project members are present.
        * Confirm nothing has an accuracy of 0. If an asset is missing (one of the causes of an accuracy of 0), take note of the missing asset in this issue and plan to restage it for another, smaller run of this wave
        * If the namespaces are incorrect, meaning a project or a group has been migrated to the wrong location, do the following:
            * For projects:
                * If the project is in an incorrect namespace within the parent group, move the project to the correct group
                * If the project is in a completely incorrect, random location on the destination, confirm the spread of the leaked data, and refer to the [rollback instructions](#Rollback)
            * For groups:
                * If the group is not within the expected parent group, make a note of the incorrectly migrated group in this issue, delete the group, and refer to the [rollback instructions](#Rollback)
        * If random users are present in a group or project, refer to the [rollback instructions](#Rollback). 
            * Confirm these users are actually incorrect, look up the user through the API (`/api/v4/users/:id`)
* [ ] Post a comment in this issue containing the following information:
   * Projects: `<insert-overall-accuracy>`
   * Groups: `<insert-overall-accuracy>`
   * Users: `<insert-overall-accuracy>`
* [ ] If accuracy is greater than 90%, mark this migration as a success
* [ ] If accuracy is lower than 90%, review the diff reports again and see if any projects or groups are missing
* [ ] Attach `data/*_results.*` and `data/*_diff.json` to this issue
* [ ] Copy `data/*_results.*` and `data/*_diff.json` to `/opt/congregate/data/waves/wave_<insert_wave_number>/`
* [ ] Notify in the internal slack channel dedicated to this migration the diff report is finished generating with a link to the comment you just posted. If you need to run another small subset of this migration, mention that in the slack message as well.
* [ ] Notify the customer in the customer-facing slack channel the migration wave has finished

### Post Migration with Missing Groups and Projects

* [ ] If projects or groups are missing, confirm the projects and groups have successfully exported and confirm they don't actually exist on the destination instance
    * To confirm the exports have successfully exported, review the contents of `/opt/congregate/downloads` or the S3 bucket defined in the configuration. Make sure no export archive has a size of 42 bytes. That means the export archive is invalid.
    * To confirm the projects or groups don't actually exist on the destination instance, compare the results of the diff report and manually check where the project or group should be located.
    * To confirm the projects or groups don't actually exist on the destination instance, you may also `dry-run` a wave.
        * You can also search for the project with an API request to `/projects?search=<project-name>`
        * You can also search for the groups with an API request to `/groups?search=<group-name>` or `/groups/<url-encoded-full-path>`
* [ ] Stage _only_ those groups and projects and go through this runbook again, this time with the following command for the migration stage: `nohup ./congregate.sh migrate --skip-users --skip-group-export --skip-project-export --commit > data/waves/wave_<insert_wave_number>/wave<insert-wave-here>_attempt<insert-attempt>.log 2>&1 &`
* [ ] Monitor the wave periodically by running `tail -f data/waves/wave_<insert_wave_number>/wave<insert-wave-here>_attempt<insert-attempt>.log`
* [ ] Notify in the internal slack channel dedicated to this migration the migration has finished
* [ ] Notify the customer in the customer-facing slack channel the migration wave has finished
* [ ] Stitch together the various migration attempts by running `./congregate.sh stitch-results --result-type=<user|group|project> --no-of-files=<number-of-results-files-to-stitch>`
* [ ] Once the results have been stitched into a single JSON file, run the diff report on the newly created results file
* [ ] Attach `data/congregate.log`, `data/audit.log`, and `data/waves/wave_<insert_wave_number>/wave<insert-wave-here>_attempt<insert-attempt>.log` to this issue
* [ ] Copy `data/congregate.log`, `data/audit.log`, and `data/waves/wave_<insert_wave_number>/wave<insert-wave-here>_attempt<insert-attempt>.log` to `/opt/congregate/data/waves/wave_<insert_wave_number>/`

### Rollback

If **any** data was migrated incorrectly (i.e to the wrong namespace) to a random location, you **must** rollback the migration wave **completely**

* [ ] Notify in the internal slack channel dedicated to this migration you are running a rollback due an issue with the migration
* [ ] Run `nohup ./congregate.sh rollback --skip-users --commit > data/waves/wave_<insert_wave_number>/rollback.log 2>&1 &`
* [ ] Copy the rollback log and `data/audit.log` to `/opt/congregate/data/waves/wave_<insert_wave_number>/`
* [ ] Post a comment describing the reason for the rollback and attach the rollback log and `data/audit.log`
* [ ] Follow these [instructions in the handbook](https://about.gitlab.com/handbook/engineering/security/#engaging-the-security-on-call) and link to this issue.


/confidential