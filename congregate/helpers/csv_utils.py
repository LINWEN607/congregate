import json
import csv
import os

def write_projects_csv(json_path, csv_path):
    """
    Reads a list of project objects from 'json_path' (projects.json) and writes them to 'csv_path'.
    """

    if not os.path.isfile(json_path):
        print(f"JSON file not found: {json_path}")
        return

    with open(json_path, "r", encoding="utf-8") as jf:
        projects = json.load(jf)
        if not isinstance(projects, list):
            print(f"Expected a list of projects in {json_path}, got something else.")
            return

    # Define all possible CSV columns (flattening nested items like 'namespace.*'):
    fieldnames = [
        "id",
        "name",
        "name_with_namespace",
        "path",
        "path_with_namespace",
        "archived",
        "visibility",
        "default_branch",
        "ssh_url_to_repo",
        "http_url_to_repo",
        "web_url",
        "readme_url",
        "avatar_url",
        "creator_id",
        "created_at",
        "last_activity_at",
        "updated_at",
        "star_count",
        "forks_count",
        "empty_repo",
        "public_jobs",
        "build_timeout",
        "build_git_strategy",
        "repository_storage",
        "repository_object_format",
        "packages_enabled",
        "lfs_enabled",
        "merge_method",
        "issues_enabled",
        "merge_requests_enabled",
        "jobs_enabled",
        "wiki_enabled",
        "snippets_enabled",
        "service_desk_enabled",
        "emails_enabled",
        "emails_disabled",
        "mirror",
        "import_status",
        "import_type",
        "import_url",
        "autoclose_referenced_issues",
        "printing_merge_request_link_enabled",
        "only_allow_merge_if_pipeline_succeeds",
        "only_allow_merge_if_all_discussions_are_resolved",
        "only_allow_merge_if_all_status_checks_passed",
        "remove_source_branch_after_merge",
        "request_access_enabled",
        "shared_runners_enabled",
        "group_runners_enabled",
        "forking_access_level",
        "issues_access_level",
        "merge_requests_access_level",
        "snippets_access_level",
        "container_registry_access_level",
        "security_and_compliance_access_level",
        "analytics_access_level",
        "environments_access_level",
        "releases_access_level",
        "feature_flags_access_level",
        "infrastructure_access_level",
        "monitor_access_level",
        "model_experiments_access_level",
        "model_registry_access_level",
        "repository_access_level",
        "pages_access_level",
        "wiki_access_level",
        "builds_access_level",
        "ci_allow_fork_pipelines_to_run_in_parent_project",
        "ci_job_token_scope_enabled",
        "ci_default_git_depth",
        "ci_config_path",
        "ci_restrict_pipeline_cancellation_role",
        "ci_separated_caches",
        "ci_forward_deployment_enabled",
        "ci_forward_deployment_rollback_allowed",
        "allow_pipeline_trigger_approve_deployment",
        "allow_merge_on_skipped_pipeline",
        "auto_cancel_pending_pipelines",
        "auto_devops_enabled",
        "auto_devops_deploy_strategy",
        "marked_for_deletion_at",
        "marked_for_deletion_on",
        "runner_token_expiration_interval",
        "runners_token",
        "description",
        "description_html",
        "merge_commit_template",
        "merge_requests_template",
        "squash_commit_template",
        "suggestion_commit_message",
        "remove_source_branch_after_merge",
        "security_and_compliance_enabled",
        "service_desk_address",
        "warn_about_potentially_unwanted_characters",
        "prevent_merge_without_jira_issue",
        "resolve_outdated_diff_discussions",
        "restrict_user_defined_variables",
        "keep_latest_artifact",
        "pages_access_level",
        "compliance_frameworks_json",
        "namespace_json",
        "shared_with_groups_json",
        "members_json",
        "tag_list_json",
        "topics_json",
        "groups_json",
    ]

    with open(csv_path, "w", newline="", encoding="utf-8") as cf:
        writer = csv.DictWriter(cf, fieldnames=fieldnames)
        writer.writeheader()

        for proj in projects:
            # Safely fetch each field, converting None -> "" for CSV
            def val(key):
                return proj.get(key, "") if proj.get(key, "") is not None else ""

            row = {
                "id": val("id"),
                "name": val("name"),
                "name_with_namespace": val("name_with_namespace"),
                "path": val("path"),
                "path_with_namespace": val("path_with_namespace"),
                "archived": str(val("archived")).lower(),
                "visibility": val("visibility"),
                "default_branch": val("default_branch"),
                "ssh_url_to_repo": val("ssh_url_to_repo"),
                "http_url_to_repo": val("http_url_to_repo"),
                "web_url": val("web_url"),
                "readme_url": val("readme_url"),
                "avatar_url": val("avatar_url"),
                "creator_id": val("creator_id"),
                "created_at": val("created_at"),
                "last_activity_at": val("last_activity_at"),
                "updated_at": val("updated_at"),
                "star_count": val("star_count"),
                "forks_count": val("forks_count"),
                "empty_repo": str(val("empty_repo")).lower(),
                "public_jobs": str(val("public_jobs")).lower(),
                "build_timeout": val("build_timeout"),
                "build_git_strategy": val("build_git_strategy"),
                "repository_storage": val("repository_storage"),
                "repository_object_format": val("repository_object_format"),
                "packages_enabled": str(val("packages_enabled")).lower(),
                "lfs_enabled": str(val("lfs_enabled")).lower(),
                "merge_method": val("merge_method"),
                "issues_enabled": str(val("issues_enabled")).lower(),
                "merge_requests_enabled": str(val("merge_requests_enabled")).lower(),
                "jobs_enabled": str(val("jobs_enabled")).lower(),
                "wiki_enabled": str(val("wiki_enabled")).lower(),
                "snippets_enabled": str(val("snippets_enabled")).lower(),
                "service_desk_enabled": str(val("service_desk_enabled")).lower(),
                "emails_enabled": str(val("emails_enabled")).lower(),
                "emails_disabled": str(val("emails_disabled")).lower(),
                "mirror": str(val("mirror")).lower(),
                "import_status": val("import_status"),
                "import_type": val("import_type"),
                "import_url": val("import_url"),
                "autoclose_referenced_issues": str(val("autoclose_referenced_issues")).lower(),
                "printing_merge_request_link_enabled": str(val("printing_merge_request_link_enabled")).lower(),
                "only_allow_merge_if_pipeline_succeeds": str(val("only_allow_merge_if_pipeline_succeeds")).lower(),
                "only_allow_merge_if_all_discussions_are_resolved": str(val("only_allow_merge_if_all_discussions_are_resolved")).lower(),
                "only_allow_merge_if_all_status_checks_passed": str(val("only_allow_merge_if_all_status_checks_passed")).lower(),
                "remove_source_branch_after_merge": str(val("remove_source_branch_after_merge")).lower(),
                "request_access_enabled": str(val("request_access_enabled")).lower(),
                "shared_runners_enabled": str(val("shared_runners_enabled")).lower(),
                "group_runners_enabled": str(val("group_runners_enabled")).lower(),
                "forking_access_level": val("forking_access_level"),
                "issues_access_level": val("issues_access_level"),
                "merge_requests_access_level": val("merge_requests_access_level"),
                "snippets_access_level": val("snippets_access_level"),
                "container_registry_access_level": val("container_registry_access_level"),
                "security_and_compliance_access_level": val("security_and_compliance_access_level"),
                "analytics_access_level": val("analytics_access_level"),
                "environments_access_level": val("environments_access_level"),
                "releases_access_level": val("releases_access_level"),
                "feature_flags_access_level": val("feature_flags_access_level"),
                "infrastructure_access_level": val("infrastructure_access_level"),
                "monitor_access_level": val("monitor_access_level"),
                "model_experiments_access_level": val("model_experiments_access_level"),
                "model_registry_access_level": val("model_registry_access_level"),
                "repository_access_level": val("repository_access_level"),
                "pages_access_level": val("pages_access_level"),
                "wiki_access_level": val("wiki_access_level"),
                "builds_access_level": val("builds_access_level"),
                "ci_allow_fork_pipelines_to_run_in_parent_project": str(val("ci_allow_fork_pipelines_to_run_in_parent_project")).lower(),
                "ci_job_token_scope_enabled": str(val("ci_job_token_scope_enabled")).lower(),
                "ci_default_git_depth": val("ci_default_git_depth"),
                "ci_config_path": val("ci_config_path"),
                "ci_restrict_pipeline_cancellation_role": val("ci_restrict_pipeline_cancellation_role"),
                "ci_separated_caches": str(val("ci_separated_caches")).lower(),
                "ci_forward_deployment_enabled": str(val("ci_forward_deployment_enabled")).lower(),
                "ci_forward_deployment_rollback_allowed": str(val("ci_forward_deployment_rollback_allowed")).lower(),
                "allow_pipeline_trigger_approve_deployment": str(val("allow_pipeline_trigger_approve_deployment")).lower(),
                "allow_merge_on_skipped_pipeline": str(val("allow_merge_on_skipped_pipeline")).lower(),
                "auto_cancel_pending_pipelines": val("auto_cancel_pending_pipelines"),
                "auto_devops_enabled": str(val("auto_devops_enabled")).lower(),
                "auto_devops_deploy_strategy": val("auto_devops_deploy_strategy"),
                "marked_for_deletion_at": val("marked_for_deletion_at"),
                "marked_for_deletion_on": val("marked_for_deletion_on"),
                "runner_token_expiration_interval": val("runner_token_expiration_interval"),
                "runners_token": val("runners_token"),
                "description": val("description"),
                "description_html": val("description_html"),
                "merge_commit_template": val("merge_commit_template"),
                "merge_requests_template": val("merge_requests_template"),
                "squash_commit_template": val("squash_commit_template"),
                "suggestion_commit_message": val("suggestion_commit_message"),
                "security_and_compliance_enabled": str(val("security_and_compliance_enabled")).lower(),
                "service_desk_address": val("service_desk_address"),
                "warn_about_potentially_unwanted_characters": str(val("warn_about_potentially_unwanted_characters")).lower(),
                "prevent_merge_without_jira_issue": str(val("prevent_merge_without_jira_issue")).lower(),
                "resolve_outdated_diff_discussions": str(val("resolve_outdated_diff_discussions")).lower(),
                "restrict_user_defined_variables": str(val("restrict_user_defined_variables")).lower(),
                "keep_latest_artifact": str(val("keep_latest_artifact")).lower(),
                "pages_access_level": val("pages_access_level"),
                # JSON columns
                "compliance_frameworks_json": json.dumps(proj.get("compliance_frameworks", {}), ensure_ascii=False),
                "namespace_json": json.dumps(proj.get("namespace", {}), ensure_ascii=False),
                "members_json": json.dumps(proj.get("members", []), ensure_ascii=False),
                "shared_with_groups_json": json.dumps(proj.get("shared_with_groups", []), ensure_ascii=False),
                "tag_list_json": json.dumps(proj.get("tag_list", []), ensure_ascii=False),
                "topics_json": json.dumps(proj.get("topics", []), ensure_ascii=False),
                "groups_json": json.dumps(proj.get("groups", {}), ensure_ascii=False), # "groups" only exists on bitbucket, should be empty on GitLab
            }

            writer.writerow(row)

def write_users_csv(json_path, csv_path):
    """
    Reads a list of user objects from 'json_path' and writes them to 'csv_path'.
    """

    if not os.path.isfile(json_path):
        print(f"JSON file not found: {json_path}")
        return

    with open(json_path, "r", encoding="utf-8") as jf:
        users = json.load(jf)
        if not isinstance(users, list):
            print(f"Expected a list of user objects in {json_path}, got something else.")
            return
        
    fieldnames = [
        "id",
        "username",
        "email",
        "name",
        "avatar_url",
        "bot",
        "can_create_group",
        "can_create_project",
        "color_scheme_id",
        "commit_email",
        "discord",
        "email_reset_offered_at",
        "enterprise_group_associated_at",
        "enterprise_group_id",
        "external",
        "extra_shared_runners_minutes_limit",
        "followers",
        "following",
        "is_admin",
        "is_auditor",
        "is_followed",
        "job_title",
        "linkedin",
        "local_time",
        "location",
        "locked",
        "namespace_id",
        "note",
        "organization",
        "private_profile",
        "projects_limit",
        "pronouns",
        "provisioned_by_group_id",
        "public_email",
        "shared_runners_minutes_limit",
        "skype",
        "state",
        "theme_id",
        "twitter",
        "two_factor_enabled",
        "using_license_seat",
        "website_url",
        "work_information",
        "created_by_json",
        "identities_json",
        "scim_identities_json",
    ]

    with open(csv_path, "w", newline="", encoding="utf-8") as cf:
        writer = csv.DictWriter(cf, fieldnames=fieldnames)
        writer.writeheader()

        for user in users:
            def val(key):
                raw = user.get(key, "")
                if raw is None:
                    return ""
                if isinstance(raw, bool):
                    return str(raw).lower()
                return raw

            row = {
                "id": val("id"),
                "username": val("username"),
                "email": val("email"),
                "name": val("name"),
                "avatar_url": val("avatar_url"),
                "bot": val("bot"),
                "can_create_group": val("can_create_group"),
                "can_create_project": val("can_create_project"),
                "color_scheme_id": val("color_scheme_id"),
                "commit_email": val("commit_email"),
                "discord": val("discord"),
                "email_reset_offered_at": val("email_reset_offered_at"),
                "enterprise_group_associated_at": val("enterprise_group_associated_at"),
                "enterprise_group_id": val("enterprise_group_id"),
                "external": val("external"),
                "extra_shared_runners_minutes_limit": val("extra_shared_runners_minutes_limit"),
                "followers": val("followers"),
                "following": val("following"),
                "is_admin": val("is_admin"),
                "is_auditor": val("is_auditor"),
                "is_followed": val("is_followed"),
                "job_title": val("job_title"),
                "linkedin": val("linkedin"),
                "local_time": val("local_time"),
                "location": val("location"),
                "locked": val("locked"),
                "namespace_id": val("namespace_id"),
                "note": val("note"),
                "organization": val("organization"),
                "private_profile": val("private_profile"),
                "projects_limit": val("projects_limit"),
                "pronouns": val("pronouns"),
                "provisioned_by_group_id": val("provisioned_by_group_id"),
                "public_email": val("public_email"),
                "shared_runners_minutes_limit": val("shared_runners_minutes_limit"),
                "skype": val("skype"),
                "state": val("state"),
                "theme_id": val("theme_id"),
                "twitter": val("twitter"),
                "two_factor_enabled": val("two_factor_enabled"),
                "using_license_seat": val("using_license_seat"),
                "website_url": val("website_url"),
                "work_information": val("work_information"),
                # JSON columns
                "created_by_json": json.dumps(user.get("created_by", {}), ensure_ascii=False),
                "scim_identities_json": json.dumps(user.get("scim_identities", {}), ensure_ascii=False),
                "identities_json": json.dumps(user.get("identities", []), ensure_ascii=False),
            }

            writer.writerow(row)

def write_groups_csv(json_path, csv_path):
    """
    Reads a list of group objects from 'json_path' (groups.json) and writes them to 'csv_path'.
    """

    if not os.path.isfile(json_path):
        print(f"JSON file not found: {json_path}")
        return

    with open(json_path, "r", encoding="utf-8") as jf:
        groups = json.load(jf)
        if not isinstance(groups, list):
            print(f"Expected a list of groups in {json_path}, got something else.")
            return

    fieldnames = [
        "id",
        "name",
        "path",
        "full_path",
        "visibility",
        "avatar_url",
        "description",
        "created_at",
        "organization_id",
        "parent_id",
        "emails_enabled",
        "emails_disabled",
        "lfs_enabled",
        "wiki_access_level",
        "project_creation_level",
        "subgroup_creation_level",
        "shared_runners_setting",
        "require_two_factor_authentication",
        "two_factor_grace_period",
        "share_with_group_lock",
        "lock_duo_features_enabled",
        "lock_math_rendering_limits_enabled",
        "math_rendering_limits_enabled",
        "duo_features_enabled",
        "marked_for_deletion_on",
        "mentions_disabled",
        "repository_storage",
        "default_branch",
        "default_branch_protection",
        "emails_disabled",
        "empty_repo",
        "request_access_enabled",
        "default_branch_protection_defaults_json",
        "desc_groups_json",
        "members_json",
        "projects_json",
        "groups_json",
    ]

    with open(csv_path, "w", newline="", encoding="utf-8") as cf:
        writer = csv.DictWriter(cf, fieldnames=fieldnames)
        writer.writeheader()

        for group in groups:
            def val(key):
                raw = group.get(key, "")
                if raw is None:
                    return ""
                if isinstance(raw, bool):
                    return str(raw).lower()
                return raw

            row = {
                "id": val("id"),
                "name": val("name"),
                "path": val("path"),
                "full_path": val("full_path"),
                "visibility": val("visibility"),
                "avatar_url": val("avatar_url"),
                "description": val("description"),
                "created_at": val("created_at"),
                "organization_id": val("organization_id"),
                "parent_id": val("parent_id"),
                "emails_enabled": str(val("emails_enabled")).lower(),
                "emails_disabled": str(val("emails_disabled")).lower(),
                "lfs_enabled": str(val("lfs_enabled")).lower(),
                "wiki_access_level": val("wiki_access_level"),
                "project_creation_level": val("project_creation_level"),
                "subgroup_creation_level": val("subgroup_creation_level"),
                "shared_runners_setting": val("shared_runners_setting"),
                "require_two_factor_authentication": str(val("require_two_factor_authentication")).lower(),
                "two_factor_grace_period": val("two_factor_grace_period"),
                "share_with_group_lock": str(val("share_with_group_lock")).lower(),
                "lock_duo_features_enabled": str(val("lock_duo_features_enabled")).lower(),
                "lock_math_rendering_limits_enabled": str(val("lock_math_rendering_limits_enabled")).lower(),
                "math_rendering_limits_enabled": str(val("math_rendering_limits_enabled")).lower(),
                "duo_features_enabled": str(val("duo_features_enabled")).lower(),
                "marked_for_deletion_on": val("marked_for_deletion_on"),
                "mentions_disabled": str(val("mentions_disabled")).lower() if val("mentions_disabled") else "",
                "repository_storage": val("repository_storage"),
                "default_branch": val("default_branch"),
                "default_branch_protection": val("default_branch_protection"),
                "request_access_enabled": str(val("request_access_enabled")).lower(),
                # JSON columns
                "default_branch_protection_defaults_json": json.dumps(group.get("default_branch_protection_defaults", {}), ensure_ascii=False),
                "desc_groups_json": json.dumps(group.get("desc_groups", {}), ensure_ascii=False),
                "members_json": json.dumps(group.get("members", []), ensure_ascii=False),
                "projects_json": json.dumps(group.get("projects", []), ensure_ascii=False),
                "groups_json": json.dumps(group.get("groups", {}), ensure_ascii=False), # "groups" only exists on bitbucket, should be empty on GitLab
            }

            writer.writerow(row)

def parse_projects_csv(app_path, scm_source=None):
    """
    Reads data/projects.csv and rebuilds the full projects structure
    """
    csv_path = f"{app_path}/data/projects.csv"
    projects_list = []
    if scm_source:
        csv_path = f"{app_path}/data/projects-{scm_source}.csv"

    if os.path.exists(csv_path):
        with open(csv_path, "r", encoding="utf-8") as cf:
            reader = csv.DictReader(cf)
            for row in reader:
                project = {
                    "id": int(row.get("id", "")) if row.get("id", "").isdigit() else row.get("id", ""),
                    "name": row.get("name", "") or "",
                    "name_with_namespace": row.get("name_with_namespace", "") or "",
                    "path": row.get("path", "") or "",
                    "path_with_namespace": row.get("path_with_namespace", "") or "",
                    "archived": parse_bool(row.get("archived", "")),
                    "visibility": row.get("visibility", "") or "private",
                    "default_branch": row.get("default_branch", "") or None,
                    "ssh_url_to_repo": row.get("ssh_url_to_repo", "") or "",
                    "http_url_to_repo": row.get("http_url_to_repo", "") or "",
                    "web_url": row.get("web_url", "") or "",
                    "readme_url": row.get("readme_url", "") or "",
                    "avatar_url": row.get("avatar_url", "") or None,
                    "creator_id": parse_int(row.get("creator_id", "")),
                    "created_at": row.get("created_at", "") or None,
                    "last_activity_at": row.get("last_activity_at", "") or None,
                    "updated_at": row.get("updated_at", "") or None,
                    "star_count": parse_int(row.get("star_count", "")) or 0,
                    "forks_count": parse_int(row.get("forks_count", "")) or 0,
                    "empty_repo": parse_bool(row.get("empty_repo", "")),
                    "public_jobs": parse_bool(row.get("public_jobs", "")),
                    "build_timeout": parse_int(row.get("build_timeout", "")) or 3600,
                    "build_git_strategy": row.get("build_git_strategy", "") or "fetch",
                    "repository_storage": row.get("repository_storage", "") or "",
                    "repository_object_format": row.get("repository_object_format", "") or "",
                    "packages_enabled": parse_bool(row.get("packages_enabled", "")),
                    "lfs_enabled": parse_bool(row.get("lfs_enabled", "")),
                    "merge_method": row.get("merge_method", "") or "merge",
                    "issues_enabled": parse_bool(row.get("issues_enabled", "")),
                    "merge_requests_enabled": parse_bool(row.get("merge_requests_enabled", "")),
                    "jobs_enabled": parse_bool(row.get("jobs_enabled", "")),
                    "wiki_enabled": parse_bool(row.get("wiki_enabled", "")),
                    "snippets_enabled": parse_bool(row.get("snippets_enabled", "")),
                    "service_desk_enabled": parse_bool(row.get("service_desk_enabled", "")),
                    "emails_enabled": parse_bool(row.get("emails_enabled", "")),
                    "emails_disabled": parse_bool(row.get("emails_disabled", "")),
                    "mirror": parse_bool(row.get("mirror", "")),
                    "import_status": row.get("import_status", "") or "",
                    "import_type": row.get("import_type", "") or "",
                    "import_url": row.get("import_url", "") or None,
                    "autoclose_referenced_issues": parse_bool(row.get("autoclose_referenced_issues", "")),
                    "printing_merge_request_link_enabled": parse_bool(row.get("printing_merge_request_link_enabled", "")),
                    "only_allow_merge_if_pipeline_succeeds": parse_bool(row.get("only_allow_merge_if_pipeline_succeeds", "")),
                    "only_allow_merge_if_all_discussions_are_resolved": parse_bool(row.get("only_allow_merge_if_all_discussions_are_resolved", "")),
                    "only_allow_merge_if_all_status_checks_passed": parse_bool(row.get("only_allow_merge_if_all_status_checks_passed", "")),
                    "remove_source_branch_after_merge": parse_bool(row.get("remove_source_branch_after_merge", "")),
                    "request_access_enabled": parse_bool(row.get("request_access_enabled", "")),
                    "shared_runners_enabled": parse_bool(row.get("shared_runners_enabled", "")),
                    "group_runners_enabled": parse_bool(row.get("group_runners_enabled", "")),
                    "forking_access_level": row.get("forking_access_level", "") or "enabled",
                    "issues_access_level": row.get("issues_access_level", "") or "enabled",
                    "merge_requests_access_level": row.get("merge_requests_access_level", "") or "enabled",
                    "snippets_access_level": row.get("snippets_access_level", "") or "enabled",
                    "container_registry_access_level": row.get("container_registry_access_level", "") or "enabled",
                    "security_and_compliance_access_level": row.get("security_and_compliance_access_level", "") or "private",
                    "analytics_access_level": row.get("analytics_access_level", "") or "enabled",
                    "environments_access_level": row.get("environments_access_level", "") or "enabled",
                    "releases_access_level": row.get("releases_access_level", "") or "enabled",
                    "feature_flags_access_level": row.get("feature_flags_access_level", "") or "enabled",
                    "infrastructure_access_level": row.get("infrastructure_access_level", "") or "enabled",
                    "monitor_access_level": row.get("monitor_access_level", "") or "enabled",
                    "model_experiments_access_level": row.get("model_experiments_access_level", "") or "enabled",
                    "model_registry_access_level": row.get("model_registry_access_level", "") or "enabled",
                    "repository_access_level": row.get("repository_access_level", "") or "enabled",
                    "pages_access_level": row.get("pages_access_level", "") or "private",
                    "wiki_access_level": row.get("wiki_access_level", "") or "enabled",
                    "builds_access_level": row.get("builds_access_level", "") or "enabled",
                    "ci_allow_fork_pipelines_to_run_in_parent_project": parse_bool(row.get("ci_allow_fork_pipelines_to_run_in_parent_project", "")),
                    "ci_job_token_scope_enabled": parse_bool(row.get("ci_job_token_scope_enabled", "")),
                    "ci_default_git_depth": parse_int(row.get("ci_default_git_depth", "")) or 20,
                    "ci_config_path": row.get("ci_config_path", "") or None,
                    "ci_restrict_pipeline_cancellation_role": row.get("ci_restrict_pipeline_cancellation_role", "") or "developer",
                    "ci_separated_caches": parse_bool(row.get("ci_separated_caches", "")),
                    "ci_forward_deployment_enabled": parse_bool(row.get("ci_forward_deployment_enabled", "")),
                    "ci_forward_deployment_rollback_allowed": parse_bool(row.get("ci_forward_deployment_rollback_allowed", "")),
                    "allow_pipeline_trigger_approve_deployment": parse_bool(row.get("allow_pipeline_trigger_approve_deployment", "")),
                    "allow_merge_on_skipped_pipeline": parse_bool(row.get("allow_merge_on_skipped_pipeline", "")),
                    "auto_cancel_pending_pipelines": row.get("auto_cancel_pending_pipelines", "") or "enabled",
                    "auto_devops_enabled": parse_bool(row.get("auto_devops_enabled", "")),
                    "auto_devops_deploy_strategy": row.get("auto_devops_deploy_strategy", "") or "continuous",
                    "marked_for_deletion_at": row.get("marked_for_deletion_at", "") or None,
                    "marked_for_deletion_on": row.get("marked_for_deletion_on", "") or None,
                    "runner_token_expiration_interval": parse_int(row.get("runner_token_expiration_interval", "")),
                    "runners_token": row.get("runners_token", "") or "",
                    "description": row.get("description", "") or None,
                    "description_html": row.get("description_html", "") or "",
                    "merge_commit_template": row.get("merge_commit_template", "") or None,
                    "merge_requests_template": row.get("merge_requests_template", "") or None,
                    "squash_commit_template": row.get("squash_commit_template", "") or None,
                    "suggestion_commit_message": row.get("suggestion_commit_message", "") or None,
                    "security_and_compliance_enabled": parse_bool(row.get("security_and_compliance_enabled", "")),
                    "service_desk_address": row.get("service_desk_address", "") or None,
                    "warn_about_potentially_unwanted_characters": parse_bool(row.get("warn_about_potentially_unwanted_characters", "")),
                    "prevent_merge_without_jira_issue": parse_bool(row.get("prevent_merge_without_jira_issue", "")),
                    "resolve_outdated_diff_discussions": parse_bool(row.get("resolve_outdated_diff_discussions", "")),
                    "restrict_user_defined_variables": parse_bool(row.get("restrict_user_defined_variables", "")),
                    "keep_latest_artifact": parse_bool(row.get("keep_latest_artifact", "")),
                    # JSON columns
                    "namespace": json.loads(row.get("namespace_json", "") or "{}"),
                    "compliance_frameworks": json.loads(row.get("compliance_frameworks_json", "") or "[]"),
                    "members": json.loads(row.get("members_json", "") or "[]"),
                    "shared_with_groups": json.loads(row.get("shared_with_groups_json", "") or "[]"),
                    "tag_list": json.loads(row.get("tag_list_json", "") or "[]"),
                    "topics": json.loads(row.get("topics_json", "") or "[]"),
                    "groups": json.loads(row.get("groups_json", "") or "{}"), # "groups" only exists on bitbucket, should be empty on GitLab
                }

                projects_list.append(project)
                
    return projects_list


def parse_groups_csv(app_path, scm_source=None):
    """
    Reads data/groups.csv and rebuilds the full groups structure
    """
    csv_path = f"{app_path}/data/groups.csv"
    groups_list = []
    if scm_source:
        csv_path = f"{app_path}/data/groups-{scm_source}.csv"

    if os.path.exists(csv_path):
        with open(csv_path, "r", encoding="utf-8") as cf:
            reader = csv.DictReader(cf)
            for row in reader:
                group = {
                    "id": int(row.get("id", "")) if row.get("id", "").isdigit() else row.get("id", ""),
                    "organization_id": parse_int(row.get("organization_id", "")),
                    "parent_id": parse_int(row.get("parent_id", "")),
                    "two_factor_grace_period": parse_int(row.get("two_factor_grace_period", "")),
                    "default_branch_protection": parse_int(row.get("default_branch_protection", "")),
                    "emails_enabled": parse_bool(row.get("emails_enabled", "")),
                    "emails_disabled": parse_bool(row.get("emails_disabled", "")),
                    "lfs_enabled": parse_bool(row.get("lfs_enabled", "")),
                    "require_two_factor_authentication": parse_bool(row.get("require_two_factor_authentication", "")),
                    "share_with_group_lock": parse_bool(row.get("share_with_group_lock", "")),
                    "lock_duo_features_enabled": parse_bool(row.get("lock_duo_features_enabled", "")),
                    "lock_math_rendering_limits_enabled": parse_bool(row.get("lock_math_rendering_limits_enabled", "")),
                    "math_rendering_limits_enabled": parse_bool(row.get("math_rendering_limits_enabled", "")),
                    "duo_features_enabled": parse_bool(row.get("duo_features_enabled", "")),
                    "mentions_disabled": parse_bool(row.get("mentions_disabled", "")),
                    "empty_repo": parse_bool(row.get("empty_repo", "")),
                    "request_access_enabled": parse_bool(row.get("request_access_enabled", "")),
                    "name": row.get("name", "") or "",
                    "path": row.get("path", "") or "",
                    "full_path": row.get("full_path", "") or "",
                    "visibility": row.get("visibility", "") or "private",
                    "avatar_url": row.get("avatar_url", "") or None,
                    "description": row.get("description", "") or "",
                    "created_at": row.get("created_at", "") or None,
                    "wiki_access_level": row.get("wiki_access_level", "") or "enabled",
                    "project_creation_level": row.get("project_creation_level", "") or "developer",
                    "subgroup_creation_level": row.get("subgroup_creation_level", "") or "maintainer",
                    "shared_runners_setting": row.get("shared_runners_setting", "") or "enabled",
                    "marked_for_deletion_on": row.get("marked_for_deletion_on", "") or None,
                    "repository_storage": row.get("repository_storage", "") or None,
                    "default_branch": row.get("default_branch", "") or None,
                    # JSON columns
                    "default_branch_protection_defaults": json.loads(row.get("default_branch_protection_defaults_json", "") or "{}"),
                    "desc_groups": json.loads(row.get("desc_groups_json", "") or "[]"),
                    "members": json.loads(row.get("members_json", "") or "[]"),
                    "projects": json.loads(row.get("projects_json", "") or "[]"),
                    "groups": json.loads(row.get("groups_json", "") or "{}") # "groups" only exists on bitbucket, should be empty on GitLab
                }

                groups_list.append(group)

    return groups_list

def parse_users_csv(app_path, scm_source=None):
    """
    Reads data/users.csv and rebuilds the full users structure
    """
    csv_path = f"{app_path}/data/users.csv"
    users_list = []
    if scm_source:
        csv_path = f"{app_path}/data/users-{scm_source}.csv"

    if os.path.exists(csv_path):
        with open(csv_path, "r", encoding="utf-8") as cf:
            reader = csv.DictReader(cf)
            for row in reader:
                user = {
                    "id": int(row.get("id", "")) if row.get("id", "").isdigit() else row.get("id", ""),
                    "color_scheme_id": parse_int(row.get("color_scheme_id", "")),
                    "enterprise_group_id": parse_int(row.get("enterprise_group_id", "")),
                    "extra_shared_runners_minutes_limit": parse_int(row.get("extra_shared_runners_minutes_limit", "")),
                    "followers": parse_int(row.get("followers", "")) or 0,
                    "following": parse_int(row.get("following", "")) or 0,
                    "namespace_id": parse_int(row.get("namespace_id", "")),
                    "projects_limit": parse_int(row.get("projects_limit", "")),
                    "provisioned_by_group_id": parse_int(row.get("provisioned_by_group_id", "")),
                    "shared_runners_minutes_limit": parse_int(row.get("shared_runners_minutes_limit", "")),
                    "theme_id": parse_int(row.get("theme_id", "")),
                    "bot": parse_bool(row.get("bot", "")),
                    "can_create_group": parse_bool(row.get("can_create_group", "")),
                    "can_create_project": parse_bool(row.get("can_create_project", "")),
                    "external": parse_bool(row.get("external", "")),
                    "is_admin": parse_bool(row.get("is_admin", "")),
                    "is_auditor": parse_bool(row.get("is_auditor", "")),
                    "is_followed": parse_bool(row.get("is_followed", "")) or False,
                    "locked": parse_bool(row.get("locked", "")),
                    "private_profile": parse_bool(row.get("private_profile", "")),
                    "two_factor_enabled": parse_bool(row.get("two_factor_enabled", "")),
                    "using_license_seat": parse_bool(row.get("using_license_seat", "")),
                    "username": row.get("username", "") or None,
                    "email": row.get("email", "") or None,
                    "name": row.get("name", "") or None,
                    "avatar_url": row.get("avatar_url", "") or None,
                    "commit_email": row.get("commit_email", "") or None,
                    "discord": row.get("discord", "") or "",
                    "email_reset_offered_at": row.get("email_reset_offered_at", "") or None,
                    "enterprise_group_associated_at": row.get("enterprise_group_associated_at", "") or None,
                    "job_title": row.get("job_title", "") or "",
                    "linkedin": row.get("linkedin", "") or "",
                    "local_time": row.get("local_time", "") or None,
                    "location": row.get("location", "") or "",
                    "note": row.get("note", "") or None,
                    "organization": row.get("organization", "") or "",
                    "pronouns": row.get("pronouns", "") or None,
                    "public_email": row.get("public_email", "") or None,
                    "skype": row.get("skype", "") or "",
                    "state": row.get("state", "") or "",
                    "twitter": row.get("twitter", "") or "",
                    "website_url": row.get("website_url", "") or "",
                    "work_information": row.get("work_information", "") or None,
                    # JSON columns
                    "created_by": json.loads(row.get("created_by_json", "") or "{}"),
                    "identities": json.loads(row.get("identities_json", "") or "[]"),
                    "scim_identities": json.loads(row.get("scim_identities_json", "") or "[]"),
                }

                users_list.append(user)

    return users_list

def parse_bool(s):
    return s.lower() == "true" if s else False

def parse_int(s):
    return int(s) if s.isdigit() else None