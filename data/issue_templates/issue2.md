# Confirm SWC builds and deploys in non-prod

## Welcome to GitLab!

Once you have signed off Issue 1 for this Software Component, you then need to generate a build artifact & deploy it to a non-PROD environment. There are steps below highlighting some of the steps you may need to take. Once this Issue and Issue 1 for this Software Component are closed, this Software Component will be reported as having successfully migrated to DevCloud.

## Things to look for

1. Have you been able to generate a build artifact & deploy to at least a non-PROD environment? 
1. Build is running
1. Build artifacts are published to artifact repository
1. Test jobs are running (as applicable)
1. Deploy/configure jobs are able to pull artifacts and deploy to non-production environment

## Notes
Once you have verified the above items, you can **close this issue** by clicking the orange close button. We will be tracking the migration completeness using this indicator across all SWCs.

If you are having trouble transforming your CICD Pipeline, please refer to [the documentation]({{faq_page}}), or open a [support request here]({{jira_page}}).

## Repos Migrated so far