# Congregate

Come together, right now

...over me

## Dependencies

- [jq](https://stedolan.github.io/jq/download/)
- [cURL](https://curl.haxx.se/download.html)

## Major Goal - CLI Tool

Assist with migrating contents of multiple GitLab instances into a single (monolithic?) GitLab instance.

This tool covers the following processes:
- Define instances that need to be migrated
- Export the projects of those instances to a storage location of your choice (S3, GCP, bare metal, etc)
- Import those projects to the parent GitLab instance
- Provide logs to document and monitor the process

## Far Away Goal - UI integration

The UI integration will help provide all of the features of the CLI directly within a GitLab instance and leverage Meltano for metrics.