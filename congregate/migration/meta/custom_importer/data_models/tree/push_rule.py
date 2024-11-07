
from dataclasses import dataclass, asdict
from gitlab_ps_utils.dict_utils import strip_none
                    
'''
{
    "author_email_regex": "<class 'NoneType'>",
    "branch_name_regex": "<class 'NoneType'>",
    "commit_committer_check": "<class 'NoneType'>",
    "commit_message_negative_regex": "<class 'NoneType'>",
    "commit_message_regex": "<class 'NoneType'>",
    "deny_delete_tag": "<class 'NoneType'>",
    "file_name_regex": "<class 'NoneType'>",
    "is_sample": "<class 'bool'>",
    "max_file_size": "<class 'int'>",
    "member_check": "<class 'bool'>",
    "prevent_secrets": "<class 'bool'>",
    "regexp_uses_re2": "<class 'bool'>",
    "reject_non_dco_commits": "<class 'NoneType'>",
    "reject_unsigned_commits": "<class 'NoneType'>"
}             
'''

@dataclass
class PushRule:
    author_email_regex: str | None = None
    branch_name_regex: str | None = None
    commit_committer_check: bool | None = None
    commit_message_negative_regex: str | None = None
    commit_message_regex: str | None = None
    deny_delete_tag: bool | None = None
    file_name_regex: str | None = None
    is_sample: bool
    max_file_size: int
    member_check: bool
    prevent_secrets: bool
    regexp_uses_re2: bool
    reject_non_dco_commits: bool | None = None
    reject_unsigned_commits: bool | None = None

    def to_dict(self):
        return strip_none(asdict(self))

                    