from dataclasses import dataclass, field
from typing import List
from congregate.migration.meta.custom_importer.data_models.tree.merge_request_diff_file import MergeRequestDiffFile
from congregate.migration.meta.custom_importer.data_models.tree.merge_request_commit import MergeRequestCommit

@dataclass
class MergeRequestDiff:
    '''
        Dataclass for importing any merge/pull request diffs from another source instance

        This is the overarching dataclass for displaying merge request changes
    '''
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
