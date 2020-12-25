# Congregate Documentation

Congregate is an internal tool for GitLab professional services to handle migrating customers to GitLab. Congregate currently supports the following migration directions:

* GitLab self-managed :arrow_right: gitlab.com
* GitLab self-managed :arrow_right: GitLab self-managed
* Bitbucket Server :arrow_right: gitlab.com
* Bitbucket Server :arrow_right: GitLab self-managed
* GitHub Enterprise :arrow_right: gitlab.com
* GitHub Enterprise :arrow_right: GitLab self-managed

Our guidance on some other migrations at this time:

* Bitbucket Cloud
  * We support migrating BitBucket Server to GitLab as of GitLab 13.1 with the recent addition of the BitBucket Server import API
  * BitBucket Cloud is not slated to be supported in congregate due to a lack of an API to consume and its requirement to authenticate through OAuth
* GitHub.com
  * We have a [built-in importer](https://docs.gitlab.com/ee/user/project/import/github.html) for importing from GitHub.com
* SVN
  * We have some [documentation](https://docs.gitlab.com/ee/user/project/import/svn.html) on gitlab.com discussing migrating from SVN

## Contents

* [Getting Started](static_docs/setup.md)
* [README](static_docs/readme.md)
* [Migration Features](static_docs/migration-features.md)
  * [GitLab](static_docs/gitlab-migration-features-matrix.md)
  * [Bitbucket](static_docs/bitbucket-migration-features-matrix.md)
  * [GitHub](static_docs/github-migration-features-matrix.md)
* [Migration Metrics](static_docs/migration-metrics.md)
* [Development Environment Setup Tips](static_docs/local-development.md)
* [Writing Tests in Congregate](static_docs/writing-tests.md)
* [Bitbucket Development Setup](static_docs/bitbucket-development-setup.md)
* [GitHub Development Setup](static_docs/github-development-setup.md)
* [Migration Workflow](static_docs/workflow.md)
* [Code Quality Report](static_docs/code-quality.md)
* [Congregate Wiki](https://gitlab.com/gitlab-com/customer-success/tools/congregate/-/wikis/home)

## Indices and tables

* [Index](genindex)
* [Module Index](modindex)
* [Search](search)
