# Azure DevOps

:white_check_mark: = supported

:heavy_minus_sign: = not yet supported / in development

:x: = not supported

NOTE: Features not listed in the matrix should be presumed to be not yet supported.

## Azure DevOps (SaaS)

| Main           | Feature                   | Sub-feature | Congregate            |
| -------------- | ------------------------- | ----------- | --------------------- |
| **Project**    |
|                | GitLab Group creation *   |             | :x:                   |
| **Repository** |                           |             |                       |
|                | Git Repo (branches + tags)|             | :white_check_mark:    |
|                | Pull requests (PR)        |             | :white_check_mark:    |
|                | PR author                 |             | :white_check_mark:    |
|                | PR reviewers              |             | :white_check_mark:    |
|                | PR merged by              |             | :white_check_mark:    |
|                | PR comments               |             | :white_check_mark:    |
|                | PR attachments            |             | :white_check_mark:    |
| **User**       |                           |             |                       |
|                | Account                   |             | :white_check_mark:    |

* Target group in GitLab has to be created manually. See [open issue](https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate/-/issues/1147) to support this in congregate.
