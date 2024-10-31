from dataclasses import dataclass, asdict, field
from typing import Optional, List


@dataclass
class UserPayload():
    username: str
    name: str
    email: str
    state: Optional[str] = ""
    location: Optional[str] = ""
    skype: Optional[str] = ""
    linkedin: Optional[str] = ""
    twitter: Optional[str] = ""
    website_url: Optional[str] = ""
    organization: Optional[str] = ""
    identities: Optional[List[dict]] = field(default_factory=list)
    can_create_group: Optional[bool] = False
    can_create_project: Optional[bool] = False
    two_factor_enabled: Optional[bool] = False
    external: Optional[bool] = False

    # Parameters that may not have existed yet on older GitLab versions
    projects_limit: Optional[int] = None  # May be popped during listing
    bio: Optional[str] = ""   # Supports Markdown as of 13.2
    public_email: Optional[str] = ""
    discord: Optional[str] = ""
    job_title: Optional[str] = ""
    pronouns: Optional[str] = ""
    bot: Optional[bool] = False
    work_information: Optional[str] = ""
    local_time: Optional[str] = ""
    theme_id: Optional[int] = 1
    color_scheme_id: Optional[int] = 1
    private_profile: Optional[bool] = False
    commit_email: Optional[str] = ""
    note: Optional[str] = ""

    # POST fields
    extern_uid: Optional[str] = ""
    provider: Optional[str] = ""
    group_id_for_saml: Optional[int] = None
    skip_confirmation: Optional[bool] = None
    reset_password: Optional[bool] = None
    force_random_password: Optional[bool] = None

    # + Premium / Ultimate parameters
    scim_identities: Optional[List[dict]] = field(default_factory=list)
    shared_runners_minutes_limit: Optional[int] = None
    extra_shared_runners_minutes_limit: Optional[int] = None
    provisioned_by_group_id: Optional[int] = None
    using_license_seat: Optional[bool] = False

    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v not in ["", [], None]}
