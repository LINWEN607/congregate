# Welcome to Congregate\'s documentation\!

Congregate is an internal tool for GitLab professional services to handle migrating customers to GitLab. Congregate currently supports the following migration directions:

* Self-managed to gitlab.com
* Self-managed to self-managed

Our guidance on some other migrations at this time:

* Bitbucket
  * While there is some code in congregate for a BitBucket migration, we would suggest customers use the internal BitBucket importer for the time being. We are actively working to scale up our BitBucket Server migrations, but it is not fully implemented.
  * If scale is a concern for customers, please reach out to professional services for a consulting services quote.
* GitHub
  * We have a [built-in importer](https://docs.gitlab.com/ee/user/project/import/github.html) for importing from GitHub
* SVN
  * We have some [documentation](https://docs.gitlab.com/ee/user/project/import/svn.html) on gitlab.com discussing migrating from SVN

## Contents

* [Getting Started](static_docs/setup.md)
* [README](static_docs/readme.md)
* [Migration Prerequisites](static_docs/migration-prerequisites.md)
* [Migration Metrics](static_docs/migration-metrics.md)
* [Development Environment Setup Tips](static_docs/local-development.md)
* [Writing Tests in Congregate](static_docs/writing-tests.md)
* [Bitbucket Development Setup](static_docs/bitbucket-development-setup.md)
* [Migration Workflow](static_docs/workflow.md)
* [Code Quality Report](static_docs/code-quality.md)
* [Congregate Wiki](https://gitlab.com/gitlab-com/customer-success/tools/congregate/-/wikis/home)

## Indices and tables

* [Index](genindex)
* [Module Index](modindex)
* [Search](search)
