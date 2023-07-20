# Alternate "Migration" Methods

Below, we present some of the ways in which data can be moved from SCM systems to GitLab

## [Direct Transfer](https://docs.gitlab.com/ee/user/group/import/#migrate-groups-by-direct-transfer-recommended)
- This is not [Group Transfer](https://docs.gitlab.com/ee/user/group/manage.html#transfer-a-group)
- New migration method for GitLab -> GitLab
- Similar to our other existing importers like GitHub
- Still has some of the limitations of the file-based, but...
  - No admin token required!
- Not yet the default in Congregate

## [File-based Export/Import](https://docs.gitlab.com/ee/user/group/import/#migrate-groups-by-uploading-an-export-file-deprecated) (deprecated)
- Method for GitLab -> GitLab
- This was deprecated in GitLab 14.6
- Still enabled and usable
- Still the primary method used by Congregate 

## [Congregate](https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate)
- Wrapper around our various importers
  - File-based, Direct Transfer, GitHub, etc
- Compensates for some limitations of the various methods
  - [GitLab](https://gitlab-org.gitlab.io/professional-services-automation/tools/migration/congregate/gitlab-migration-features-matrix/)
    - Mostly based on the limitations of file-based in the GitLab scenario but some overlap with Direct Transfer
  - [GitHub](https://gitlab-org.gitlab.io/professional-services-automation/tools/migration/congregate/github-migration-features-matrix/)
  - [Bitbucket](https://gitlab-org.gitlab.io/professional-services-automation/tools/migration/congregate/bitbucket-migration-features-matrix/)
- File-based is still the default method in Congregate. Direct Transfer may become default within the next 6-12 months

## [GEO](https://docs.gitlab.com/ee/administration/geo/)
- Only for GitLab -> GitLab
- Self-managed generally, but being investigated for SM->GitLab Dedicated
- Does not work for SaaS (as source or destination)
- Can be difficult to set up, particularly when attaching to existing, long-running instances
- Wait time to replicate

## [Omnibus Backup/Restore](https://docs.gitlab.com/ee/administration/backup_restore/)
- Most "complete" method. Backup of the instance and data
- Not for SaaS (either side)
- Lacking feature parity between this and Chart version
- Currently will not backup remote object storage data

## [Chart Backup/Restore (K8s/Cloud-native Hybrid)](https://docs.gitlab.com/charts/architecture/backup-restore.html)
- Also most "complete"
- Not for SaaS (either side)
- Can have constraints based on the limitations of the toolbox pod on K8s
