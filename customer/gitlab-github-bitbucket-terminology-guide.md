# GitLab, GitHub, and Bitbucket – Terminology Guide

*This guide clarifies key terminology differences across GitLab, GitHub, and Bitbucket to support teams during migrations or cross-platform collaboration.*

---

## 1. Core Terminology Mapping

| **Concept**            | **GitLab**                                                                 | **GitHub**        | **Bitbucket Cloud** | **Bitbucket Server / DC** | **Notes**                                                                 |
|------------------------|----------------------------------------------------------------------------|-------------------|----------------------|----------------------------|----------------------------------------------------------------------------|
| **Top-level Container**| [Group](https://docs.gitlab.com/user/group/)                               | Organization      | Workspace             | ❌ None (starts at Project) | Workspace ≈ Organization ≈ Group (Cloud only)                             |
| **Organizational Unit**| [Subgroup](https://docs.gitlab.com/user/group/subgroups/)                  | Organization      | Project               | Project                    | Bitbucket *Project* ≈ GitLab *Group*                                      |
| **Repository**         | [Project](https://docs.gitlab.com/user/project/)                           | Repository        | Repository            | Repository                 | GitLab *Project* = Repo + CI/CD + Issues, etc.                            |
| **Package Registry**   | [Package Registry](https://docs.gitlab.com/user/packages/package_registry/)| GitHub Packages   | ❌ None Native         | ❌ None Native             | GitLab and GitHub support multiple formats (e.g., Maven, npm, PyPI)       |
| **Merge Process**      | [Merge Request](https://docs.gitlab.com/user/project/merge_requests/)      | Pull Request      | Pull Request          | Pull Request               | Same function, different name                                             |
| **CI/CD**              | [Pipelines](https://docs.gitlab.com/ci/pipelines/)                         | GitHub Actions    | Bitbucket Pipelines   | Jenkins / Bamboo           | YAML-based, but syntax varies                                             |
| **Issue Tracking**     | [Issues](https://docs.gitlab.com/user/project/issues/)                     | Issues            | Issues                | Issues                     | Consistent across platforms                                               |
| **Access Tokens**      | [Personal/Group/Project Tokens](https://docs.gitlab.com/security/tokens/)  | Personal Tokens   | App Passwords         | Application Links          | GitLab offers more granular token scopes                                  |
| **Webhooks**           | [Webhooks](https://docs.gitlab.com/user/project/integrations/webhooks/)    | Repo / Org Webhooks| Repo Webhooks         | Repo Webhooks              | GitLab & GitHub offer broader webhook levels                              |

---

## 2. Organizational Structure Overview

| **Concept**           | **GitLab**                       | **GitHub**                     | **Bitbucket Cloud**             | **Bitbucket Server / DC**        |
|-----------------------|----------------------------------|--------------------------------|----------------------------------|----------------------------------|
| **Hierarchy**         | Group → Subgroup → Project       | Organization → Repository      | Workspace → Project → Repository| Project → Repository              |
| **Subgrouping**       | ✅ Yes                            | ⚠️ Teams (permission scope)     | ❌ Not Available                 | ❌ Not Available                  |
| **Visibility Levels** | Public / Internal / Private      | Public / Internal¹ / Private   | Public / Private                | Public / Private                 |

### Note:
¹ GitHub's *Internal* visibility is available only in Enterprise Cloud orgs and exposes repos to all members.  
² Bitbucket’s *Public* visibility is limited; Projects and Workspaces are private by default.

---

## 3. Advanced Feature Mapping

| Feature                        | GitLab                                 | GitHub                         | Bitbucket                         |
|--------------------------------|----------------------------------------|--------------------------------|-----------------------------------|
| **Epics**                      | ✅ Yes                                 | ❌ No native                    | ❌ No native                       |
| **Static Pages**               | GitLab Pages                           | GitHub Pages                   | ❌ None                            |
| **Web IDE**                    | Yes                                    | Codespaces                     | Code Editor                       |
| **Web Wikis**                  | Yes                                    | Yes                            | Code Editor                       |
| **Container Registry**         | Yes                                    | Yes                            | Yes                               |
| **CI/CD Config File**          | `.gitlab-ci.yml`                       | `.github/workflows/*.yml`      | `bitbucket-pipelines.yml`         |
| **Self-Hosted Option**         | CE/EE                                  | GitHub Enterprise Server       | Bitbucket Data Center             |
| **CI/CD Components & Catalog** | GitLab CI/CD Components & Catalog      | GitHub Actions & Marketplace   | Bitbucket Pipes & Catalog         |

---

## 4. Configuration File Equivalents

| Purpose                | GitLab                                 | GitHub                                 | Bitbucket                   |
|------------------------|----------------------------------------|----------------------------------------|-----------------------------|
| **CI/CD Config**       | `.gitlab-ci.yml`                       | `.github/workflows/*.yml`              | `bitbucket-pipelines.yml`   |
| **Issue Templates**    | `.gitlab/issue_templates/*.md`         | `.github/ISSUE_TEMPLATE/*.md`          | ❌ No standard path         |
| **MR/PR Templates**    | `.gitlab/merge_request_templates/*.md` | `.github/PULL_REQUEST_TEMPLATE.md`     | ❌ No standard path         |

---

## 5. Analytics & Reporting

| **Feature**              | **GitLab**                             | **GitHub**                       | **Bitbucket**                   |
|--------------------------|----------------------------------------|----------------------------------|---------------------------------|
| **Repository Analytics** | ✅ Repository insights                 | ✅ Insights                       | ✅ Repository insights           |
| **CI/CD Analytics**      | ✅ Pipeline metrics                    | ✅ Actions usage insights         | ✅ Pipeline duration & status    |
| **DevOps Reports**       | ✅ Value Stream Analytics, DORA metrics| ❌ Limited native offering        | ❌ Limited native offering       |

---

## 6. Security & Compliance Features

| **Feature**              | **GitLab**                                                        | **GitHub**                                       | **Bitbucket**                                 |
|--------------------------|-------------------------------------------------------------------|--------------------------------------------------|-----------------------------------------------|
| **Native Security Tools**| ✅ Built-in SAST, DAST, Dependency, Container Scanning            | ✅ GitHub Advanced Security (CodeQL, etc.)        | ❌ No native tools (uses integrations)         |
| **Dependency Scanning**  | ✅ Included in CI/CD                                               | ✅ Dependabot                                    | ⚠️ Snyk (integration only)                    |
| **Secret Detection**     | ✅ Built-in                                                       | ✅ Secret Scanning                               | ⚠️ Snyk (integration only)                    |
| **Security Dashboard**   | ✅ GitLab Security Dashboard                                      | ✅ GitHub Security Overview                       | ⚠️ Snyk Dashboard (integration only)          |
