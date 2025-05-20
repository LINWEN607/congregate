# BitBucket

:white_check_mark: = supported

:heavy_minus_sign: = not yet supported / in development

:x: = not supported

NOTE: Features not listed in the matrix should be presumed to be not yet supported.

## Bitbucket Server

| Main           | Feature                   | Sub-feature | GitLab BBS importer   | GitLab BBC importer | Congregate             |
| -------------- | ------------------------- | ----------- | --------------------- | ------------------- | ---------------------- |
| **Project**    |
|                | GitLab Group creation *   |             | :white_check_mark:    | :white_check_mark:  | :white_check_mark:     |
|                | User permission mapping   |             | :x:                   | :x:                 | :white_check_mark:     |
|                | Branch permission mapping |             | :x:                   | :x:                 | :x:                    |
| **Repository** |
|                | Project import            |             | :white_check_mark:    | :white_check_mark:  | :white_check_mark:     |
|                | Pull requests             |             | :white_check_mark:    | :white_check_mark:  | :white_check_mark:     |
|                | MR comments               |             | :white_check_mark: ** | :white_check_mark:  | :white_check_mark: **  |
|                | Git Repo                  |             | :white_check_mark:    | :white_check_mark:  | :white_check_mark:     |
|                | LFS Objects               |             | :white_check_mark:    | :white_check_mark:  | :white_check_mark:     |
|                | Milestones                |             | :x:                   | :white_check_mark:  | :white_check_mark: bbc |
|                | User permission mapping   |             | :x:                   | :x:                 | :white_check_mark:     |
|                | Branch permission mapping |             | :x:                   | :x:                 | :white_check_mark:     |
|                | Webhooks                  |             | :x:                   | :x:                 | :x:                    |
|                | Pull request approvals    |             | :x:                   | :x:                 | :x:                    |
|                | Approval rules            |             | :x:                   | :x:                 | :x:                    |
| **User**       |
|                | Account                   |             | :x:                   | :x:                 | :white_check_mark: *** |
|                | SSH Keys                  |             | :x:                   | :x:                 | :white_check_mark: *** |

* `The importer creates any new namespaces (groups) if they don’t exist. If the namespace is taken, the repository imports under the namespace of the user who started the import process.` ([source](https://docs.gitlab.com/ee/user/project/import/bitbucket_server.html#user-assignment))

** See [limitations](https://docs.gitlab.com/ee/user/project/import/bitbucket_server.html#items-that-are-not-imported) of the BitBucket Server importer

*** BitBucket Cloud does not currently have support for user account and SSH key migration due to lack of support via BB Cloud's API.

## BitBucket Cloud

With the [API endpoint](https://docs.gitlab.com/ee/api/import.html#import-repository-from-bitbucket-cloud) introduced in 17.0 Congregate now supports [importing from BB Cloud](https://docs.gitlab.com/ee/user/project/import/bitbucket.html).

For usage see the [migration doc](/docs/customer/bitbucket-cloud-migration-doc.md).
