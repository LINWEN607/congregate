# Fixing Missings Groups via Direct Transfer

These scripts are designed to:

1. [get-group-ids.py](./get-group-ids.py) is used to ingest a file of missing groups (missing from destination). Please see [missing-groups.txt](./missing-groups.txt)
2. Output a file in Congregates wave CSV format that can be ingested by [fix-groups.py](./fix-groups.py) to upload the groups via DT

The comment headers for the individual files discuss their usage. Please consult them for more.