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

* Bitbucket Cloud
  * We support migrating BitBucket Server to GitLab as of GitLab 13.1 with the recent addition of the BitBucket Server import API
  * BitBucket Cloud is not slated to be supported in congregate due to a lack of an API to consume and its requirement to authenticate through OAuth
* SVN
  * We have some [documentation](https://docs.gitlab.com/ee/user/project/import/svn.html) on gitlab.com discussing migrating from SVN
