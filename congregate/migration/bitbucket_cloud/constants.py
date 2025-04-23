# Based on https://developer.atlassian.com/cloud/bitbucket/rest/api-group-repositories/

BBC_REPO_PERM_MAP = {
    "REPO_ADMIN": 50,   # Owner (as of 14.9)
    "REPO_WRITE": 30,   # Developer
    "REPO_READ": 20     # Reporter
}

BBC_PROJECT_PERM_MAP = {
    "PROJECT_ADMIN": 50,    # Owner
    "REPO_CREATE": 40,      # Maintainer
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
    40: "REPO_CREATE",      # Maintainer
    30: "PROJECT_WRITE",    # Developer
    20: "PROJECT_READ"      # Reporter
}

PR_STATE_MAPPING = {
    "OPEN": "opened",
    "MERGED": "merged",
    "DECLINED": "closed"
}
