# Migration Runbooks

What to do when conducting a migration

## About this directory

Refer to various runbooks in this folder when conducting various types of migrations

## Where are these runbooks used?

These runbooks currently get [automatically pushed](https://gitlab.com/gitlab-com/customer-success/tools/congregate/-/blob/master/.gitlab-ci.yml#L287) to the following projects to be used as issue templates:

- [Migration Engagement Template](https://gitlab.com/gitlab-com/customer-success/professional-services-group/project-templates/migration-template)
- [PS-Migration Project](https://gitlab.com/gitlab-com/customer-success/professional-services-group/ps-migration)


## General Troubleshooting
This section is intended to show known issues and how to solve them when working with Congregate. 

When trying to run any Congergate command, if you get an error that says `Congregate is already running at <pid>`, you should try to kill the congregate process by:
1. run `ps aux` to see the list of processes and process ids (pid)
1. find the congregate process that is running and take note of its pid. 
1. run `kill -9 <pid>`

Once the process is killed, if you're still getting the error that congergate is still running, that means that congregate wans't shutdown propelry and there is a lock file that exists at `/tmp/congergate.pid`. Simply run a `rm -f /tmp/congregate.pid` to resolve then rerun congregate command you were trying to use. 
