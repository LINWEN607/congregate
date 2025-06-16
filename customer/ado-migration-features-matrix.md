# Azure DevOps

:white_check_mark: = supported

:heavy_minus_sign: = not yet supported / in development

:x: = not supported

NOTE: Features not listed in the matrix should be presumed to be not yet supported.

## Azure DevOps (SaaS)

:white_check_mark: = Supported  
:heavy_minus_sign: = Not yet supported / in development  
:construction: = Partial / Work in progress

| Service / Element    | Feature                          | Sub-Feature                                           | Congregate         | Scripts / other tools | Comment                                   |
| -------------------- | -------------------------------- | ----------------------------------------------------- | ------------------ | --------------------- | ----------------------------------------- |
| **Structure**        |                                  |                                                       |                    |                       |                                           |
|                      | Groups and Projects <sup>1</sup> | Description, visibility settings                      | :white_check_mark: |                       |                                           |
|                      | User membership <sup>2</sup>     |                                                       | :heavy_minus_sign: |                       | Use SAML (JIT) or SCIM; SAML Group Links; |
| **User accounts**    | GitLab User account              | Username, email, display name, state                  | :white_check_mark: |                       |                                           |
| **Overview**         |                                  |                                                       |                    |                       |                                           |
|                      | Wiki <sup>3</sup>                |                                                       |                    |                       |                                           |
| **Azure Boards**     |                                  |                                                       |                    |                       |                                           |
|                      | Work Item (WI)                   | Title, Description, Timestamp, State                  | :white_check_mark: |                       |                                           |
|                      |                                  | WI Author, assignees                                  | :white_check_mark: |                       |                                           |
|                      |                                  | WI comments (as-is)                                   | :white_check_mark: |                       |                                           |
|                      |                                  | WI attachments, formatting                            | :construction:     |                       | Enhancements Epic <sup>4</sup>            |
| **Azure Repos**      |                                  |                                                       |                    |                       |                                           |
|                      | Git                              |                                                       |                    |                       |                                           |
|                      |                                  | Commits, branches, tags                               | :white_check_mark: |                       |                                           |
|                      |                                  | Pull Requests (PR)                                    | :white_check_mark: |                       |                                           |
|                      |                                  | PR author, assignees, reviewers, merged by, closed by | :white_check_mark: |                       |                                           |
|                      |                                  | PR comments, attachments, formatting                  | :white_check_mark: |                       |                                           |
|                      | TFVC                             |                                                       |                    | :construction:        | Enhancements Epic <sup>5</sup>            |
| **Azure Pipelines**  |                                  |                                                       |                    |                       |                                           |
|                      | Pipelines                        | YAML                                                  | :construction:     |                       |                                           |
|                      | Variable Groups                  | Variables <sup>6</sup>                                |                    |                       |                                           |
| **Azure Test Plans** |                                  |                                                       | :heavy_minus_sign: | :heavy_minus_sign:    | Does not have equivalent in GitLab        |
| **Azure Artifacts**  | Feeds                            |                                                       | :construction:     |                       |                                           |

1. Azure DevOps Project is migrated as GitLab Group, Azure DevOps Repo is migrated as GitLab Project. Can also be prepended with top-level or sugroup(s) (e.g. `url/top-level-group/subgroup/`)
2. Used to preserve contributions but does not align with [GitLab permissions](https://docs.gitlab.com/user/permissions/). It's recommended to use SAML (JIT) or SCIM to provision users; [SAML Group Links](https://docs.gitlab.com/user/group/saml_sso/group_sync/) to grant access to GitLab.
3. We are migrating only `projectWiki` as [Group Wiki](https://docs.gitlab.com/user/project/wiki/group/); we are migrating `codeWiki` as [Project Wiki](https://docs.gitlab.com/user/project/wiki/)
4. [Enhancements Epic](https://gitlab.com/groups/gitlab-org/professional-services-automation/tools/migration/-/epics/129)
5. [Enhancements Epic](https://gitlab.com/groups/gitlab-org/professional-services-automation/tools/migration/-/epics/118)
6. [Variable groups linked to secrets in Azure Key Vault](https://learn.microsoft.com/en-us/azure/devops/pipelines/library/link-variable-groups-to-key-vaults?view=azure-devops) are currently **not** migrated when the value is empty ([known issue](https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate/-/issues/1239))
