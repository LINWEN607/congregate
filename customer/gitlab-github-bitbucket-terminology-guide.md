# GitLab, GitHub, and Bitbucket – Terminology & Migration Guide

*This guide clarifies key terminology differences across GitLab, GitHub, and Bitbucket to support teams during migrations or cross-platform collaboration.*

---

## 1. Core Terminology Mapping

| Concept              | GitLab            | GitHub            | Bitbucket         | Notes                                                  |
|----------------------|-------------------|-------------------|-------------------|--------------------------------------------------------|
| **Top-level Container**  | Group             | Organization      | Workspace         | Workspace (Bitbucket) ≈ Organization ≈ Group           |
| **Organizational Unit**  | Group / Subgroup  | Organization      | Project           | Bitbucket *Project* ≈ GitLab *Group*                   |
| **Repository**           | Project           | Repository        | Repository        | GitLab *Project* = Repo + CI/CD + Issues, etc.         |
| **Merge Process**        | Merge Request     | Pull Request      | Pull Request      | Same function, different name in GitLab                |
| **CI/CD**                | GitLab CI/CD      | GitHub Actions    | Bitbucket Pipelines| YAML-based, but syntax varies                          |
| **Issue Tracking**       | Issues            | Issues            | Issues            | Consistent across platforms                            |
| **Access Tokens**        | Personal/Group/Project | Personal Access Tokens | App Passwords / PAT | GitLab has more token scopes                           |
| **Webhooks**             | Project / Group   | Repo / Org        | Repo              | GitLab & GitHub offer higher-level webhooks            |

---

## 2. Organizational Structure Overview

| **Concept**         | **GitLab**              | **GitHub**             | **Bitbucket**               |
|---------------------|-------------------------|------------------------|-----------------------------|
| **Hierarchy**        | Group → Subgroup → Project | Organization → Repo  | Workspace → Project → Repo  |
| **Subgrouping**      | ✅ Yes                  | ⚠️ Teams (permissions) | ❌ Not Available             |

---

## 3. Advanced Feature Mapping

| Feature              | GitLab        | GitHub        | Bitbucket     |
|----------------------|---------------|---------------|---------------|
| **Epics**            | ✅ Yes        | ❌ No native  | ❌ No native  |
| **Static Pages**     | GitLab Pages  | GitHub Pages  | ❌ None       |
| **Web IDE**          | Yes           | Codespaces    | Code Editor   |
| **Container Registry**| Yes          | Yes           | Yes           |
| **CI/CD Config File**| `.gitlab-ci.yml` | `.github/workflows` | `bitbucket-pipelines.yml` |
| **Self-Hosted Option**| CE/EE        | Enterprise Server | Data Center  |

---

## 4. Configuration File Equivalents

| Purpose           | GitLab                   | GitHub                   | Bitbucket               |
|-------------------|--------------------------|--------------------------|-------------------------|
| **CI/CD Config**  | `.gitlab-ci.yml`         | `.github/workflows/*.yml`| `bitbucket-pipelines.yml`|
| **Issue Templates**| `.gitlab/issue_templates/*.md` | `.github/ISSUE_TEMPLATE/*.md` | No standard path     |
| **MR/PR Templates**| `.gitlab/merge_request_templates/*.md` | `.github/PULL_REQUEST_TEMPLATE.md` | No standard path  |

---
