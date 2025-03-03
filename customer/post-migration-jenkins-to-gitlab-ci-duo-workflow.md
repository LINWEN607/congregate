# Post-Migration Guide: Adopting GitLab CI from Jenkins with Duo Workflow

## Overview
After successfully migrating your source code repositories to GitLab using Congregate, the next step is to transition from your previous CI system (e.g., Jenkins) to GitLab CI/CD while enabling **Duo Workflow**. This guide provides steps to set up Duo Workflow and references the Migration Delivery Kit to assist in translating your previous CI/CD pipelines.

## Prerequisites
Before proceeding, ensure you have:
- Migrated your source code to GitLab using [Congregate](https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate).
- Access to a GitLab instance with Duo Workflow enabled.
- Appropriate permissions to configure CI/CD pipelines.
- A **Jenkinsfile** or equivalent CI/CD pipeline definition from your previous system.

## Steps to Enable Duo Workflow and Transition CI/CD

### 1. Verify Migration Success
Ensure your repositories, branches, and pipeline configurations were migrated correctly. Run the following checks:
- The repository is available in your target GitLab group.
- Branches have been migrated successfully.
- The necessary GitLab users and permissions are set up correctly.

### 2. Enable Duo Workflow
Follow the official GitLab documentation to set up Duo Workflow: [GitLab Duo Workflow Setup](https://docs.gitlab.com/user/duo_workflow/set_up/).

### 3. Transition Your CI/CD Pipelines with the Migration Delivery Kit
Once Duo Workflow is enabled, you need to transition your existing CI/CD pipelines from Jenkins to GitLab CI/CD.

- Use the [Migration Delivery Kit](https://gitlab.com/gitlab-org/professional-services-automation/delivery-kits/migration-delivery-kits/migration-delivery-kit/-/blob/main/Jenkins/jenkins-to-gitlab-duo-workflow.md?ref_type=heads) for step-by-step guidance on translating Jenkinsfile-based pipelines to GitLab CI/CD.
- This guide will help you map your existing Jenkins pipeline structure to GitLab’s CI/CD YAML syntax.
- Follow best practices for structuring your GitLab CI/CD configuration in alignment with Duo Workflow.

### 4. Validate the Migration
- Run a test pipeline to confirm that GitLab CI/CD is properly configured.
- Monitor the execution logs in GitLab CI/CD > Pipelines.
- If issues arise, refer to the [Duo Workflow Troubleshooting Guide](https://docs.gitlab.com/user/duo_workflow/set_up/#troubleshooting).

### 5. Review Security & Compliance
- Apply any security scanning tools necessary (SAST, DAST, dependency scanning, etc.).
- Ensure proper access control and branch protection rules are in place.

## Additional Resources
- [Jenkins to GitLab Duo Workflow Migration Guide (Delivery Kit)](https://gitlab.com/gitlab-org/professional-services-automation/delivery-kits/migration-delivery-kits/migration-delivery-kit/-/blob/main/Jenkins/jenkins-to-gitlab-duo-workflow.md?ref_type=heads)
- [GitLab Duo Workflow Documentation](https://docs.gitlab.com/user/duo_workflow/set_up/)
- [GitLab Professional Services Migration Tools](https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate)

## Conclusion
Use the [Migration Delivery Kit](https://gitlab.com/gitlab-org/professional-services-automation/delivery-kits/migration-delivery-kits/migration-delivery-kit/-/blob/main/Jenkins/jenkins-to-gitlab-duo-workflow.md?ref_type=heads) to transition your existing CI/CD pipelines seamlessly. If you encounter any issues, refer to the official GitLab documentation or reach out to GitLab Professional Services for assistance.
