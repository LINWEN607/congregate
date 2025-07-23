# Congregate

[![lint score](https://user-content.gitlab-static.net/4ea5cdfa13fa28766d712c48e04ee724de3b84aa/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f6c696e7425323073636f72652d382e39382d626c75652e737667)](https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate/tree/master)
[![pipeline status](https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate/badges/master/pipeline.svg)](https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate/-/pipelines?page=1&scope=all&ref=master)
[![coverage](https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate/badges/master/coverage.svg)](https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate/-/tree/master/congregate/tests)
[![latest release](https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate/-/badges/release.svg)](https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate/-/releases)

![Congregate](./img/overview.png)

## Congregate Migration Tool

Congregate is a migration orchestration tool that moves data from various source systems into a destination GitLab instance. Built as a wrapper around the [GitLab APIs](https://docs.gitlab.com/ee/api/api_resources.html#rest-api-resources), it supports many migration methodologies, focusing on the following two GitLab->GitLab migration methods:

- **[Direct Transfer](https://docs.gitlab.com/user/group/import)** - Direct API-based migration
- **[File Based](https://docs.gitlab.com/user/project/settings/import_export)** - Export/import via files

[GitLab Professional Services](https://about.gitlab.com/professional-services) uses Congregate for large-scale migration engagements.

## Core Migration Components

Most migrations involve moving or verifying:
- [Users](https://docs.gitlab.com/ee/api/users.html)
- [Groups](https://docs.gitlab.com/ee/api/group_import_export.html)  
- [Projects](https://docs.gitlab.com/ee/api/project_import_export.html)

## Additional Features

Congregate extends GitLab's built-in importers with support for items such as packages and container registries. For a complete feature listing, see the [Feature Matrices](https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate/-/blob/master/customer). The following are the more common feature Matrices;

- [GitHub](./customer/github-migration-features-matrix.md)
- [BitBucket](./customer/bitbucket-migration-features-matrix.md)
- [GitLab](./customer/gitlab-migration-features-matrix.md)
- [Azure DevOps](./customer/ado-migration-features-matrix.md)
- [CodeCommit](./customer/codecommit-migration-features-matrix.md)

## Trying Congregate

Congregate is available for evaluation and users are encouraged to explore its features to ensure it meets their needs.  Before using it for your migration, please:

- Review the available features in the Feature [Feature Matrices](https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate/-/blob/master/customer) to ensure Congregate meets your requirements
- Check the current [Quick-start guide to using congregate](./docs/using-congregate.md#quick-start)
- **Important:** Migrations to gitlab.com using [file-based export/import](https://docs.gitlab.com/user/project/settings/import_export/) require an Administrator token. These are currently only available to [GitLab Professional Services](https://about.gitlab.com/professional-services) team members.

## Support

- Community support is provided on a best-effort basis through [GitLab issues](https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate/-/issues) with asynchronous responses
- For dedicated support with SLAs and guaranteed response times, please engage our [Professional Services](https://about.gitlab.com/professional-services/) team
- For support questions please [create an issue](https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate/-/issues/new?issuable_template=congregate-support) using our Congregate support [issue template](./.gitlab/issue_templates/congregate-support.md). 

## Links

### Getting Started

- [Frequently asked Migration Questions](./customer/famq.md)
- [Migration Service Delivery Kit](https://gitlab.com/gitlab-org/professional-services-automation/delivery-kits/migration-template)
- [Quick-start guide to using congregate](./docs/using-congregate.md#quick-start)

### Documentation

- [Congregate Commands Help Page](./congregate/main.py#L5)
- [Congregate technical documentation](https://gitlab-org.gitlab.io/professional-services-automation/tools/migration/congregate/)
- [Project Structure](STRUCTURE.md)

### Congregate Development

- [Contributing Guide](CONTRIBUTING.md)
- [Using Congregate - Full test environment setup](./docs/full_setup.md)
- [Setup Development Environment](./docs/setup-dev-env.md)
- [Technical Troubleshooting](./docs/troubleshooting.md)

### Resources

- Released under the [MIT License](LICENSE)
- [GitLab Partner Program](https://about.gitlab.com/partners/)
