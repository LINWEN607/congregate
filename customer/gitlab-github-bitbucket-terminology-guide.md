# GitLab, GitHub, and Bitbucket – Terminology & Migration Guide

*This guide clarifies key terminology differences across GitLab, GitHub, and Bitbucket to support teams during migrations or cross-platform collaboration.*

---

## 1. Core Terminology Mapping

| **Concept**           | **GitLab**                                                           | **GitHub**        | **Bitbucket**     | **Notes**                                        |
|-----------------------|----------------------------------------------------------------------|-------------------|-------------------|--------------------------------------------------|
| **Top-level Container**| [Group](https://docs.gitlab.com/user/group/)                         | Organization      | Workspace         | Workspace ≈ Organization ≈ Group                 |
| **Organizational Unit**| [Subgroup](https://docs.gitlab.com/user/group/subgroups/)             | Organization      | Project           | Bitbucket *Project* ≈ GitLab *Group*             |
| **Repository**        | [Project](https://docs.gitlab.com/user/project/)                      | Repository        | Repository        | GitLab *Project* = Repo + CI/CD + Issues, etc.   |
| **Package Registry**  | [GitLab Package Registry](https://docs.gitlab.com/user/packages/package_registry/)  | GitHub Packages | ❌ None Native     | GitLab and GitHub both support multiple package formats (e.g., Maven, npm, PyPI), with GitLab offering additional flexibility in self-hosted and group-level use cases |
| **Merge Process**     | [Merge Request](https://docs.gitlab.com/user/project/merge_requests/)  | Pull Request      | Pull Request      | Same function, different name in GitLab          |
| **CI/CD** (More info under Advanced Feature Mapping)             | [Pipelines](https://docs.gitlab.com/ci/pipelines/)                    | GitHub Actions    | Bitbucket Pipelines| YAML-based, but syntax varies                    |
| **Issue Tracking**    | [Issues](https://docs.gitlab.com/user/project/issues/)                 | Issues            | Issues            | Consistent across platforms                      |
| **Access Tokens**     | [Personal/Group/Project Tokens](https://docs.gitlab.com/security/tokens/)| Personal Tokens | App Passwords     | GitLab offers more granular token scopes         |
| **Webhooks**          | [Webhooks](https://docs.gitlab.com/user/project/integrations/webhooks/)| Repo / Org Webhooks| Repo Webhooks    | GitLab & GitHub offer broader webhook levels     |

---

## 2. Organizational Structure Overview

| **Concept**         | **GitLab**              | **GitHub**             | **Bitbucket**               |
|---------------------|-------------------------|------------------------|-----------------------------|
| **Hierarchy**        | Group → Subgroup → Project | Organization → Repo  | Workspace → Project → Repo  |
| **Subgrouping**      | ✅ Yes                  | ⚠️ Teams (permissions) | ❌ Not Available             |
| **Visibility Levels**| Public / Internal / Private | Public / Internal¹* / Private | Public / Private²

### Note:
¹ GitHub’s Internal visibility is only available for Enterprise Cloud organizations and makes repos visible to all members of the enterprise.

² Bitbucket’s Public visibility is limited; Projects and Workspaces are always private.

---

## 3. Advanced Feature Mapping

| Feature              | GitLab        | GitHub        | Bitbucket     |
|----------------------|---------------|---------------|---------------|
| **Epics**            | ✅ Yes        | ❌ No native  | ❌ No native  |
| **Static Pages**     | GitLab Pages  | GitHub Pages  | ❌ None       |
| **Web IDE**          | Yes           | Codespaces    | Code Editor   |
| **Web Wikis**        | Yes           | Yes           | Code Editor   |
| **Container Registry**| Yes          | Yes           | Yes           |
| **CI/CD Config File**| `.gitlab-ci.yml` | `.github/workflows` | `bitbucket-pipelines.yml` |
| **Self-Hosted Option**| CE/EE        | Enterprise Server | Data Center  |
|**CI/CD Components & Catalog**|GitLab CI/CD Components & Catalog| GitHub Actions & Marketplace| Bitbucket Pipes & Catalog
---

## 4. Configuration File Equivalents

| Purpose           | GitLab                   | GitHub                   | Bitbucket               |
|-------------------|--------------------------|--------------------------|-------------------------|
| **CI/CD Config**  | `.gitlab-ci.yml`         | `.github/workflows/*.yml`| `bitbucket-pipelines.yml`|
| **Issue Templates**| `.gitlab/issue_templates/*.md` | `.github/ISSUE_TEMPLATE/*.md` | No standard path     |
| **MR/PR Templates**| `.gitlab/merge_request_templates/*.md` | `.github/PULL_REQUEST_TEMPLATE.md` | No standard path  |

---
