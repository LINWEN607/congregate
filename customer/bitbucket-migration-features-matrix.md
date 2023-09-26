# BitBucket

:white_check_mark: = supported

:heavy_minus_sign: = not yet supported / in development

:x: = not supported

NOTE: Features not listed in the matrix should be presumed to be not yet supported.

## Bitbucket Server

| Main           | Feature                    | Sub-feature | GitLab BBS importer  | Congregate           |
| -------------- | -------------------------- | ----------- | -------------------- | -------------------- |
| **Project**    |
|                | GL Group creation          |             | :white_check_mark:   | :white_check_mark:   |
|                | Members/permission mapping |             | :x:                  | :white_check_mark:   |
| **Repository** |
|                | Project import             |             | :white_check_mark:   | :white_check_mark:   |
|                | Pull requests              |             | :white_check_mark:   | :white_check_mark:   |
|                | MR comments                |             | :white_check_mark: * | :white_check_mark: * |
|                | Git Repo                   |             | :white_check_mark:   | :white_check_mark:   |
|                | LFS Objects                |             | :white_check_mark:   | :white_check_mark:   |
|                | Members/permission mapping |             | :x:                  | :white_check_mark:   |
| **User**       |
|                | Account                    |             | :x:                  | :white_check_mark:   |
|                | SSH Keys                   |             | :x:                  | :white_check_mark:   |

*See [limitations](https://docs.gitlab.com/ee/user/project/import/bitbucket_server.html#items-that-are-not-imported) of the BB server importer

## BitBucket Cloud

Congregate does not currently support importing from BitBucket Cloud due to a lack of an import API for BB cloud
