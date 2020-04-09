<!-- 
    Copy the contents of this runbook into an issue when running through a migration wave
-->

# <customer name> Migration Wave <insert-number-here>

This runbook covers the process of migrating a wave of groups and projects from a source GitLab instance to a destination GitLab instance. This is assuming all users have already been migrated.

## Groups to migrate

<!-- 

Copy the following data and add subsequent columns for wave migration or nested group migration

Completed | Group Name | Total Projects | Group Size
--- | --- | --- | ---
:x: | [name] | [total-projects] | [group-size]

Copy the following data and add subsequent columns for single group migration

Completed | Project Path | Repo Size
--- | --- | ---
:x: | [name] | [total-projects] 

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
* [ ] Run `congregate list` at the beginning of the migration blackout period
* [ ] Stage projects based on the wave schedule in the UI
* [ ] Stage groups based on the wave schedule in the UI
* [ ] Create a directory called "waves" in `/opt/congregate/data` in the container if it doesn't already exist
* [ ] Create a directory called `wave_<insert_wave_number>` in `/opt/congregate/data/waves` if it doesn't already exist
* [ ] Copy all staged data to `/opt/congregate/data/waves/wave_<insert_wave_number>/`
* [ ] Notify in the slack channel dedicated to this migration you have completed preparation for the wave

### Dry run

* [ ] Run the following command: `nohup ./congregate.sh migrate --skip-users migrate > data/waves/wave_<insert_wave_number>/wave_<insert_wave_number>_dry_run.log 2>&1 &`
* [ ] Spot check the dry run logs
* [ ] Confirm everything looks correct and move on to the next step in the runbook
* [ ] Attach the dry run logs to this issue
* [ ] Copy the dry run logs to `/opt/congregate/data/waves/wave_<insert_wave_number>/`
* [ ] Notify in the slack channel dedicated to this migration you have completed preparation for the wave

### Migration

* [ ] Notify in the slack channel dedicated to this migration you are starting the migration wave
* [ ] Run the following command: `nohup ./congregate.sh migrate --skip-users --commit > data/waves/wave_<insert_wave_number>/wave<insert-wave-here>.log 2>&1 &`
* [ ] Monitor the wave periodically by running `tail -f data/waves/wave_extra/wave<insert-wave-here>.log`
* [ ] Notify in the slack channel dedicated to this migration the migration has finished
* [ ] Attach `data/congregate.log`, `data/audit.log`, and `data/waves/wave_extra/wave<insert-wave-here>.log` to this issue
* [ ] Copy `data/congregate.log`, `data/audit.log`, and `data/waves/wave_extra/wave<insert-wave-here>.log` to `/opt/congregate/data/waves/wave_<insert_wave_number>/`

### Post Migration

* [ ] Notify in the slack channel dedicated to this migration you are running the diff report
* [ ] Run `congregate generate-diff --staged` to generate the various diff reports
* [ ] Review the diff reports once they are finished generating
* [ ] Post a comment in this issue containing the following information:
   * Projects: `<insert-overall-accuracy>`
   * Groups: `<insert-overall-accuracy>`
   * Users: `<insert-overall-accuracy>`
* [ ] If accuracy is greater than 90%, mark this migration as a success
* [ ] If accuracy is lower than 90%, review the diff reports again and see if any projects or groups are missing
* [ ] Attach `data/*_results.*` and `data/*_diff.json` to this issue
* [ ] Copy `data/*_results.*` and `data/*_diff.json` to `/opt/congregate/data/waves/wave_<insert_wave_number>/`
* [ ] Notify in the slack channel dedicated to this migration the diff report is finished generating with a link to the comment you just posted. If you need to run another small subset of this migration, mention that in the slack message as well.


### Post Migration with Missing Groups and Projects

* [ ] If projects or groups are missing, confirm the projects and groups have successfully exported and confirm they don't actually exist on the destination instance
* [ ] Stage _only_ those groups and projects and go through this runbook again, this time with the following command for the migration stage: `nohup ./congregate.sh migrate --skip-users --skip-group-export --skip-project-export --processes=1 --commit > data/waves/wave_<insert_wave_number>/wave<insert-wave-here>_attempt<insert-attempt>.log 2>&1 &`
* [ ] Monitor the wave periodically by running `tail -f data/waves/wave_extra/wave<insert-wave-here>_attempt<insert-attempt>.log`
* [ ] Notify in the slack channel dedicated to this migration the migration has finished
* [ ] Attach `data/congregate.log`, `data/audit.log`, and `data/waves/wave_extra/wave<insert-wave-here>_attempt<insert-attempt>.log` to this issue
* [ ] Copy `data/congregate.log`, `data/audit.log`, and `data/waves/wave_extra/wave<insert-wave-here>_attempt<insert-attempt>.log` to `/opt/congregate/data/waves/wave_<insert_wave_number>/`

### Rollback

If data was migrated incorrectly, i.e to the wrong namespace, you **must** rollback the migration **completely**

* [ ] Notify in the slack channel dedicated to this migration you are running a rollback due an issue with the migration
* [ ] Run `nohup ./congregate.sh rollback --skip-users --commit > data/waves/wave_<insert_wave_number>/rollback.log 2>&1 &`
* [ ] Post a comment describing the reason for the rollback and attach the rollback log and `data/audit.log` and
* [ ] Follow these [instructions in the handbook](https://about.gitlab.com/handbook/engineering/security/#engaging-the-security-on-call) and link to this issue.

