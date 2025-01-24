"""
    Congregate - GitLab instance migration utility

    Copyright (c) 2023 - GitLab
"""

from congregate.migration.meta.ext_ci_class import ExternalCiSourceLookup

EXT_CI_SOURCE_CLASSES = [
    ExternalCiSourceLookup(
        source='jenkins',
        module='congregate.migration.jenkins.base',
        class_name='JenkinsClient'
    ),
    ExternalCiSourceLookup(
        source='teamcity',
        module='congregate.migration.teamcity.base',
        class_name='TeamCityClient'
    )
]

TOP_LEVEL_RESERVED_NAMES = {
    "-",
    ".well-known",
    "404.html",
    "422.html",
    "500.html",
    "502.html",
    "503.html",
    "admin",
    "api",
    "apple-touch-icon.png",
    "assets",
    "dashboard",
    "deploy.html",
    "explore",
    "favicon.ico",
    "favicon.png",
    "files",
    "groups",
    "health_check",
    "help",
    "import",
    "jwt",
    "login",
    "oauth",
    "profile",
    "projects",
    "public",
    "robots.txt",
    "s",
    "search",
    "sitemap",
    "sitemap.xml",
    "sitemap.xml.gz",
    "slash-command-logo.png",
    "snippets",
    "unsubscribes",
    "uploads",
    "users",
    "v2"
}

SUBGROUP_RESERVED_NAMES = {
    "-",
    # add more if needed from the doc
}

PROJECT_RESERVED_NAMES = {
    "-",
    "badges",
    "blame",
    "blob",
    "builds",
    "commits",
    "create",
    "create_dir",
    "edit",
    "environments/folders",
    "files",
    "find_file",
    "gitlab-lfs/objects",
    "info/lfs/objects",
    "new",
    "preview",
    "raw",
    "refs",
    "tree",
    "update",
    "wikis"
}
