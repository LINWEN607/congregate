# Migration Features

## GitLab

[Migration features matrix](./customer/gitlab-migration-features-matrix.md)

## BitBucket

[Migration features matrix](./customer/bitbucket-migration-features-matrix.md)

## GitHub

[Migration features matrix](./customer/github-migration-features-matrix.md)

## SVN

Congregate does not currently support automated SVN migrations and neither does GitLab

## TFS

Congregate does not currently support automated TFS migrations and neither does Gitlab

## Jenkins

We are currently working through migrating CI variables from Jenkins into GitLab

## TeamCity

We are currently working through migrating CI variables from TeamCity into GitLab

## Future features we would like to see in GitLab

- Group export/import API that includes projects
- Ability to specify GitHub Enterprise host directly through API request
- LFS support for BitBucket Server importer
- API Endpoint for BitBucket Cloud importer
- UI and API available to import SVN repos
- Being able to move a group/project with containers present to another namespace
  - We currently use congregate to do this for a customer since it is not possible through the UI

## Features we are not expecting in GitLab

- Container registry migration
- CI variable migration
- Any key migrations (SSH, GPG, Deploy)
- Runner migration (and we will not support this, either)

## Future features we expect to implement in Congregate

- Finish orchestrating GitHub migrations
- Migrate job definitions from Jenkins and TeamCity into GitLab (no conversion, just for reference)
- Add more support surrounding our BitBucket server migrations
- If there is an API available, orchestrate mass SVN migrations to GitLab
- See `~"congregate::New Feature"` for our list of existing new features we plan to implement into congregate
- See our [category grooming board](https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate/-/boards/1912553) for more information
