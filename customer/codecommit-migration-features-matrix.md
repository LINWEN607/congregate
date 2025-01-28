# CodeCommit

:white_check_mark: = supported

:heavy_minus_sign: = not yet supported / in development

:x: = not supported

NOTE: Features not listed in the matrix should be presumed to be not yet supported.

## CodeCommit

| Main           | Feature                   | Sub-feature | Congregate           |
| -------------- | ------------------------- | ----------- | -------------------- |
| **Project**    |
|                | GL Group creation         |             | :x:                * |
|                | User permission mapping   |             | :x:                * |
|                | Branch permission mapping |             | :x:                * |
| **Repository** |
|                | Project import            |             | :white_check_mark:   |
|                | Pull requests             |             | :white_check_mark: * |
|                | MR comments               |             | :white_check_mark: * |
|                | Git Repo                  |             | :white_check_mark:   |
|                | LFS Objects               |             | :x:                  |
|                | User permission mapping   |             | :x:                * |
|                | Branch permission mapping |             | :x:                * |
|                | Webhooks                  |             | :x:                  |
| **User**       |
|                | Account                   |             | :x:                * |
|                | SSH Keys                  |             | :x:                * |

*As AWS CodeCommit follows a permissioning model based around IAM, there is no consistent 
    1-1 migration strategy for customers as each customer may use a different methodology
    for user and group management.
