# Azure DevOps

:white_check_mark: = supported

:heavy_minus_sign: = not yet supported / in development

:x: = not supported

NOTE: Features not listed in the matrix should be presumed to be not yet supported.

## Azure DevOps (SaaS)

| Main           | Feature                     | Sub-feature                          | Congregate         |
| -------------- | --------------------------- | ------------------------------------ | ------------------ |
| **Project**    |                             |                                      |                    |
|                | GitLab Group creation       | Description, visibility setting      | :white_check_mark: |
|                | Members <sup>1</sup>        |                                      | :white_check_mark: |
|                | Variable Groups             | Variables <sup>2</sup>               | :white_check_mark: |
| **Repository** |                             |                                      |                    |
|                | Git repository data         |                                      | :white_check_mark: |
|                | Pull Requests (PRs)         | Author, reviewers, Merged By, PR comments, PR attachments | :white_check_mark: |
|                | Members <sup>1</sup>        |                                      | :white_check_mark: |
| **User**       |                             |                                      |                    |
|                | Account                     |                                      | :white_check_mark: |

1. Used to preserve contributions but does not align with [GitLab permissions](https://docs.gitlab.com/user/permissions/).
2. [Variable groups linked to secrets in Azure Key Vault](https://learn.microsoft.com/en-us/azure/devops/pipelines/library/link-variable-groups-to-key-vaults?view=azure-devops) are currently **not** migrated when the value is empty ([known issue](https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate/-/issues/1239))
