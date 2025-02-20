# Congregate Documentation

Congregate is an internal tool for GitLab Professional Services to handle migrating customers to GitLab. Congregate currently supports the following migration directions:

* GitLab self-managed   :arrow_right: gitlab.com
* GitLab self-managed   :arrow_right: GitLab self-managed
* gitlab.com            :arrow_right: gitlab.com
* gitlab.com            :arrow_right: GitLab self-managed
* Bitbucket Server      :arrow_right: gitlab.com
* Bitbucket Server      :arrow_right: GitLab self-managed
* GitHub Enterprise     :arrow_right: gitlab.com
* GitHub Enterprise     :arrow_right: GitLab self-managed
* GitHub.com            :arrow_right: gitlab.com
* GitHub.com            :arrow_right: GitLab self-managed

Our guidance on some other migrations at this time:

* BitBucket Cloud - Congregate currently does not support [importing from BB Cloud](https://docs.gitlab.com/ee/user/project/import/bitbucket.html)
  * With the [API endpoint](https://docs.gitlab.com/ee/api/import.html#import-repository-from-bitbucket-cloud) introduced in 17.0 this is now possible to automate
* SVN - We have some [documentation](https://docs.gitlab.com/ee/user/project/import/svn.html) on gitlab.com discussing migrating from SVN
