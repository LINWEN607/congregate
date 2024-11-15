from typing import Optional
from dataclasses import dataclass, asdict
from gitlab_ps_utils.dict_utils import strip_none
                    
@dataclass
class PushRule:
    author_email_regex: Optional[str] = None
    branch_name_regex: Optional[str] = None
    commit_committer_check: Optional[bool] = None
    commit_message_negative_regex: Optional[str] = None
    commit_message_regex: Optional[str] = None
    deny_delete_tag: Optional[bool] = None
    file_name_regex: Optional[str] = None
    is_sample: Optional[bool] = None
    max_file_size: Optional[int] = None
    member_check: Optional[bool] = None
    prevent_secrets: Optional[bool] = None
    regexp_uses_re2: Optional[bool] = None
    reject_non_dco_commits: Optional[bool] = None
    reject_unsigned_commits: Optional[bool] = None

    def to_dict(self):
        return strip_none(asdict(self))

                    