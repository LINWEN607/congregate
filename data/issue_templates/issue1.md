Confirm source code and CI/CD data Migration

Welcome to GitLab! Once your source code & other repo contents have been migrated, you need to verify that the migration has been successful by signing off this Issue. There are steps below highlighting some of the things to look out for. Once this Issue and Issue 2 for this Software Component are closed, this Software Component will be reported as having successfully migrated to DevCloud.

- [ ] Has your source code and other repo/organisation contents successfully migrated? Specifically for each repository, check:
- [ ] number of branches,
- [ ] number of commits,
- [ ] latest commit hashes,
- [ ] number of users,
- [ ] and merge requests

Once you have verified the above items, you can close this issue by clicking the orange close button. We will be tracking the migration completeness using this indicator across all SWCs. 

If you are seeing data inconsistencies in migration, please check out our FAQ page {{faq_page}} or open a support request {{jira_page}}

Variable Substitution Test:
{{self.config.destination_host}}