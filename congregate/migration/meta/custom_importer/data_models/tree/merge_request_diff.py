from dataclasses import dataclass, field
from typing import List
from congregate.migration.meta.custom_importer.data_models.tree.merge_request_diff_file import MergeRequestDiffFile
from congregate.migration.meta.custom_importer.data_models.tree.merge_request_commit import MergeRequestCommit
'''
"state": "collected",
            "created_at": "2022-04-07T14:28:23.847Z",
            "updated_at": "2022-04-07T14:28:23.950Z",
            "base_commit_sha": "2e21cf087f19cfc6f792548cdc75e35096703c0e",
            "real_size": "8",
            "head_commit_sha": "dd7911675d1b7761b31bee090780f8ea49fd7274",
            "start_commit_sha": "2e21cf087f19cfc6f792548cdc75e35096703c0e",
            "commits_count": 25,
            "files_count": 8,
            "sorted": true,
            "diff_type": "regular",
'''

@dataclass
class MergeRequestDiff:
    state: str
    created_at: str
    updated_at: str
    base_commit_sha: str
    real_size: str
    head_commit_sha: str
    start_commit_sha: str
    commits_count: int
    files_count: int
    sorted: bool
    diff_type: str
    merge_request_diff_commits: List[MergeRequestCommit] = field(default_factory=list)
    merge_request_diff_files: List[MergeRequestDiffFile] = field(default_factory=list)
