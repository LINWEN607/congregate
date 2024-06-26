USER_KEYS_TO_IGNORE = [
    "web_url",
    "last_sign_in_at",
    "last_activity_at",
    "current_sign_in_at",
    "created_at",
    "confirmed_at",
    "last_activity_on",
    "bio",
    "bio_html"
]

PROJECT_KEYS_TO_IGNORE = [
    "_links",
    "container_expiration_policy"
]

GROUP_KEYS_TO_IGNORE = [
    "web_url",
    "full_name",
    "ldap_cn",
    "ldap_access"
]

PROJECT_DIFF_KEYS_TO_IGNORE = [
    "id",
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
    "requirements_enabled",
    "forked_from_project",   # Handled as post-migration step
    "parent_id",
    "runners_token",
    "container_registry_image_prefix",
    "auto_devops_enabled",   # Because we deliberately disable it on destination
    "import_status",
    "import_type",
    "import_url",
    "description_html",
    "updated_at"
]

GROUP_DIFF_KEYS_TO_IGNORE = [
    "id",
    "projects",
    "runners_token",
    "web_url",
    "created_at",
    "marked_for_deletion_on",
    "prevent_forking_outside_group",
    "shared_with_groups",   # Temporarily, until we add shared_with_groups feature
    "file_template_project_id",
    "visibility",   # Private on import, unless imported into a parent group
    "description_html"
]

USER_DIFF_KEYS_TO_IGNORE = [
    "web_url",
    "last_sign_in_at",
    "last_activity_at",
    "current_sign_in_at",
    "created_at",
    "created_by",
    "confirmed_at",
    "last_activity_on",
    "current_sign_in_ip",
    "last_sign_in_ip",
    "source_id",
    "id",
    "author_id",
    "project_id",
    "target_id",
    "bio",
    "bio_html",
    "sign_in_count",
    "namespace_id"
]

MEMBER_ROLES = {
    "none": 0,
    "minimal": 5,
    "guest": 10,
    "reporter": 20,
    "developer": 30,
    "maintainer": 40,
    "owner": 50
}
