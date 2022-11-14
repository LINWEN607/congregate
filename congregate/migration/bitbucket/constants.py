# Based on https://confluence.atlassian.com/bitbucketserverkb/4-levels-of-bitbucket-server-permissions-779171636.html

BBS_ADMINS = ["SYS_ADMIN", "ADMIN"]

BBS_REPO_PERM_MAP = {
    "REPO_ADMIN": 50,   # Owner (as of 14.9)
    "REPO_WRITE": 30,   # Developer
    "REPO_READ": 20     # Reporter
}

BBS_PROJECT_PERM_MAP = {
    "PROJECT_ADMIN": 50,    # Owner
    "PROJECT_WRITE": 30,    # Developer
    "PROJECT_READ": 20      # Reporter
}


GL_PROJECT_PERM_MAP = {
    50: "REPO_ADMIN",   # Owner (as of 14.9)
    30: "REPO_WRITE",   # Developer
    20: "REPO_READ"     # Reporter
}

GL_GROUP_PERM_MAP = {
    50: "PROJECT_ADMIN",    # Owner
    30: "PROJECT_WRITE",    # Developer
    20: "PROJECT_READ"      # Reporter
}

PR_STATE_MAPPING = {
    "OPEN": "opened",
    "MERGED": "merged",
    "DECLINED": "closed"
}

BBS_KEYS_TO_IGNORE = [
    "_links",
    "last_activity_at",
    "created_at",
    "http_url_to_repo",
    "readme_url",
    "web_url",
    "ssh_url_to_repo",
    "project",
    "forking_access_level",
    "container_expiration_policy",
    "approvals_before_merge",
    "mirror",
    "packages_enabled",
    "external_authorization_classification_label",
    "service_desk_address",
    "service_desk_enabled",
    "marked_for_deletion_at",
    "marked_for_deletion_on",
    "compliance_frameworks",
    "forked_from_project",
    "author_email",
    "author_name",
    "authored_date",
    "committed_date",
    "committer_email",
    "committer_name",
    "created_at",
    "message",
    "parent_ids",
    "title",
    "short_id",
    "id",
    "iid",
    "project_id",
    "source_project_id",
    "target_project_id"
]
