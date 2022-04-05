class MockProjectsApi():
    def get_all_projects(self):
        '''
            Simulates a /projects request with no additional parameters
        '''
        return [
            {
                "id": 4,
                "description": "Project that does stuff",
                "default_branch": "master",
                "visibility": "private",
                "ssh_url_to_repo": "git@example.com:diaspora/diaspora-client.git",
                "http_url_to_repo": "http://example.com/diaspora/diaspora-client.git",
                "readme_url": "http://example.com/diaspora/diaspora-client/blob/master/README.md",
                "tag_list": [
                    "example",
                    "disapora client"
                ],
                "owner": {
                    "id": 3,
                    "name": "Diaspora",
                            "created_at": "2013-09-30T13:46:02Z"
                },
                "name": "Diaspora Client",
                "name_with_namespace": "Diaspora / Diaspora Client",
                "path": "diaspora-client",
                "path_with_namespace": "diaspora/diaspora-client",
                "issues_access_level": "enabled",
                "builds_access_level": "enabled",
                "repository_access_level": "enabled",
                "open_issues_count": 1,
                "merge_requests_access_level": "enabled",
                "wiki_access_level": "enabled",
                "snippets_access_level": "disabled",
                "forking_access_level": "enabled",
                "pages_access_level": "private",
                "resolve_outdated_diff_discussions": False,
                "container_registry_enabled": False,
                "created_at": "2013-09-30T13:46:02Z",
                "last_activity_at": "2013-09-30T13:46:02Z",
                "creator_id": 3,
                "namespace": {
                    "id": 3,
                    "name": "Diaspora",
                    "path": "diaspora",
                    "kind": "group",
                    "full_path": "diaspora"
                },
                "import_status": "none",
                "archived": False,
                "avatar_url": "http://example.com/uploads/project/avatar/4/uploads/avatar.png",
                "shared_runners_enabled": True,
                "forks_count": 0,
                "star_count": 0,
                "runners_token": "b8547b1dc37721d05889db52fa2f02",
                "public_jobs": True,
                "shared_with_groups": [],
                "only_allow_merge_if_pipeline_succeeds": False,
                "only_allow_merge_if_all_discussions_are_resolved": False,
                "request_access_enabled": False,
                "merge_method": "merge",
                "approvals_before_merge": 0,
                "statistics": {
                    "commit_count": 37,
                    "storage_size": 1038090,
                    "repository_size": 1038090,
                    "lfs_objects_size": 0,
                    "job_artifacts_size": 0,
                    "packages_size": 0
                },
                "_links": {
                    "self": "http://example.com/api/v4/projects",
                            "issues": "http://example.com/api/v4/projects/1/issues",
                            "merge_requests": "http://example.com/api/v4/projects/1/merge_requests",
                            "repo_branches": "http://example.com/api/v4/projects/1/repository_branches",
                            "labels": "http://example.com/api/v4/projects/1/labels",
                            "events": "http://example.com/api/v4/projects/1/events",
                            "members": "http://example.com/api/v4/projects/1/members"
                },
                "members": [
                    {
                        "id": 2,
                        "username": "john_doe",
                        "name": "John Doe",
                        "state": "active",
                        "avatar_url": "https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon",
                        "expires_at": "2012-10-22T14:13:35Z",
                        "access_level": 30
                    }
                ]
            },
            {
                "id": 6,
                "description": None,
                "default_branch": "master",
                "visibility": "private",
                "ssh_url_to_repo": "git@example.com:brightbox/puppet.git",
                "http_url_to_repo": "http://example.com/brightbox/puppet.git",
                "readme_url": "http://example.com/brightbox/puppet/blob/master/README.md",
                "tag_list": [
                    "example",
                    "puppet"
                ],
                "owner": {
                    "id": 4,
                    "name": "Brightbox",
                            "created_at": "2013-09-30T13:46:02Z"
                },
                "name": "Puppet",
                "name_with_namespace": "Brightbox / Puppet",
                "path": "puppet",
                "path_with_namespace": "brightbox/puppet",
                "issues_access_level": "enabled",
                "builds_access_level": "enabled",
                "repository_access_level": "enabled",
                "open_issues_count": 1,
                "merge_requests_access_level": "enabled",
                "wiki_access_level": "enabled",
                "snippets_access_level": "disabled",
                "forking_access_level": "enabled",
                "pages_access_level": "private",
                "resolve_outdated_diff_discussions": False,
                "container_registry_enabled": False,
                "created_at": "2013-09-30T13:46:02Z",
                "last_activity_at": "2013-09-30T13:46:02Z",
                "creator_id": 3,
                "namespace": {
                    "id": 4,
                    "name": "Brightbox",
                    "path": "brightbox",
                    "kind": "group",
                    "full_path": "brightbox"
                },
                "import_status": "none",
                "import_error": None,
                "permissions": {
                    "project_access": {
                        "access_level": 10,
                        "notification_level": 3
                    },
                    "group_access": {
                        "access_level": 50,
                        "notification_level": 3
                    }
                },
                "archived": False,
                "avatar_url": None,
                "shared_runners_enabled": True,
                "forks_count": 0,
                "star_count": 0,
                "runners_token": "b8547b1dc37721d05889db52fa2f02",
                "public_jobs": True,
                "shared_with_groups": [],
                "only_allow_merge_if_pipeline_succeeds": False,
                "only_allow_merge_if_all_discussions_are_resolved": False,
                "request_access_enabled": False,
                "merge_method": "merge",
                "approvals_before_merge": 0,
                "statistics": {
                    "commit_count": 12,
                    "storage_size": 2066080,
                    "repository_size": 2066080,
                    "lfs_objects_size": 0,
                    "job_artifacts_size": 0,
                    "packages_size": 0
                },
                "_links": {
                    "self": "http://example.com/api/v4/projects",
                            "issues": "http://example.com/api/v4/projects/1/issues",
                            "merge_requests": "http://example.com/api/v4/projects/1/merge_requests",
                            "repo_branches": "http://example.com/api/v4/projects/1/repository_branches",
                            "labels": "http://example.com/api/v4/projects/1/labels",
                            "events": "http://example.com/api/v4/projects/1/events",
                            "members": "http://example.com/api/v4/projects/1/members"
                },
                "members": [
                    {
                        "id": 2,
                        "username": "john_doe",
                        "name": "John Doe",
                        "state": "active",
                        "avatar_url": "https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon",
                        "expires_at": "2012-10-22T14:13:35Z",
                        "access_level": 30
                    }
                ]
            },
            {
                "id": 80,
                "description": None,
                "default_branch": "master",
                "visibility": "private",
                "ssh_url_to_repo": "git@example.com:brightbox/puppet.git",
                "http_url_to_repo": "http://example.com/brightbox/puppet.git",
                "readme_url": "http://example.com/brightbox/puppet/blob/master/README.md",
                "tag_list": [
                    "example",
                    "puppet"
                ],
                "owner": {
                    "id": 4,
                    "name": "Brightbox",
                            "created_at": "2013-09-30T13:46:02Z"
                },
                "name": "Puppet",
                "name_with_namespace": "Brightbox / Puppet",
                "path": "puppet",
                "path_with_namespace": "brightbox/puppet",
                "issues_access_level": "enabled",
                "builds_access_level": "enabled",
                "repository_access_level": "enabled",
                "open_issues_count": 1,
                "merge_requests_access_level": "enabled",
                "wiki_access_level": "enabled",
                "snippets_access_level": "disabled",
                "forking_access_level": "enabled",
                "pages_access_level": "private",
                "resolve_outdated_diff_discussions": False,
                "container_registry_enabled": False,
                "created_at": "2013-09-30T13:46:02Z",
                "last_activity_at": "2013-09-30T13:46:02Z",
                "creator_id": 3,
                "namespace": {
                    "id": 4,
                    "name": "Brightbox",
                    "path": "brightbox",
                    "kind": "group",
                    "full_path": "brightbox"
                },
                "import_status": "none",
                "import_error": None,
                "permissions": {
                    "project_access": {
                        "access_level": 10,
                        "notification_level": 3
                    },
                    "group_access": {
                        "access_level": 50,
                        "notification_level": 3
                    }
                },
                "archived": False,
                "avatar_url": None,
                "shared_runners_enabled": True,
                "forks_count": 0,
                "star_count": 0,
                "runners_token": "b8547b1dc37721d05889db52fa2f02",
                "public_jobs": True,
                "shared_with_groups": [],
                "only_allow_merge_if_pipeline_succeeds": False,
                "only_allow_merge_if_all_discussions_are_resolved": False,
                "request_access_enabled": False,
                "merge_method": "merge",
                "approvals_before_merge": 0,
                "statistics": {
                    "commit_count": 12,
                    "storage_size": 2066080,
                    "repository_size": 2066080,
                    "lfs_objects_size": 0,
                    "job_artifacts_size": 0,
                    "packages_size": 0
                },
                "_links": {
                    "self": "http://example.com/api/v4/projects",
                            "issues": "http://example.com/api/v4/projects/1/issues",
                            "merge_requests": "http://example.com/api/v4/projects/1/merge_requests",
                            "repo_branches": "http://example.com/api/v4/projects/1/repository_branches",
                            "labels": "http://example.com/api/v4/projects/1/labels",
                            "events": "http://example.com/api/v4/projects/1/events",
                            "members": "http://example.com/api/v4/projects/1/members"
                },
                "members": [
                    {
                        "id": 2,
                        "username": "john_doe",
                        "name": "John Doe",
                        "state": "active",
                        "avatar_url": "https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon",
                        "expires_at": "2012-10-22T14:13:35Z",
                        "access_level": 30
                    }
                ]
            }
        ]

    def get_project(self):
        '''
            Simulates a /projects/:id request
        '''
        return {
            "id": 3,
            "description": None,
            "default_branch": "master",
            "visibility": "private",
            "ssh_url_to_repo": "git@example.com:diaspora/diaspora-project-site.git",
            "http_url_to_repo": "http://example.com/diaspora/diaspora-project-site.git",
            "readme_url": "http://example.com/diaspora/diaspora-project-site/blob/master/README.md",
            "tag_list": [
                "example",
                "disapora project"
            ],
            "owner": {
                "id": 3,
                "name": "Diaspora",
                "created_at": "2013-09-30T13:46:02Z"
            },
            "name": "Diaspora Project Site",
            "name_with_namespace": "Diaspora / Diaspora Project Site",
            "path": "diaspora-project-site",
            "path_with_namespace": "diaspora/diaspora-project-site",
            "issues_access_level": "enabled",
            "builds_access_level": "enabled",
            "repository_access_level": "enabled",
            "open_issues_count": 1,
            "merge_requests_access_level": "enabled",
            "wiki_access_level": "enabled",
            "snippets_access_level": "disabled",
            "forking_access_level": "enabled",
            "pages_access_level": "private",
            "resolve_outdated_diff_discussions": False,
            "container_registry_enabled": False,
            "created_at": "2013-09-30T13:46:02Z",
            "last_activity_at": "2013-09-30T13:46:02Z",
            "creator_id": 3,
            "namespace": {
                    "id": 3,
                    "name": "Diaspora",
                    "path": "diaspora",
                    "kind": "group",
                    "full_path": "diaspora",
                    "avatar_url": "http://localhost:3000/uploads/group/avatar/3/foo.jpg",
            },
            "import_status": "none",
            "import_error": None,
            "permissions": {
                "project_access": {
                    "access_level": 10,
                    "notification_level": 3
                },
                "group_access": {
                    "access_level": 50,
                    "notification_level": 3
                }
            },
            "archived": False,
            "avatar_url": "http://example.com/uploads/project/avatar/3/uploads/avatar.png",
            "license_url": "http://example.com/diaspora/diaspora-client/blob/master/LICENSE",
            "license": {
                "key": "lgpl-3.0",
                "name": "GNU Lesser General Public License v3.0",
                "nickname": "GNU LGPLv3",
                "html_url": "http://choosealicense.com/licenses/lgpl-3.0/",
                "source_url": "http://www.gnu.org/licenses/lgpl-3.0.txt"
            },
            "shared_runners_enabled": True,
            "forks_count": 0,
            "star_count": 0,
            "runners_token": "b8bc4a7a29eb76ea83cf79e4908c2b",
            "public_jobs": True,
            "shared_with_groups": [
                {
                    "group_id": 4,
                    "group_name": "Twitter",
                    "group_full_path": "twitter",
                    "group_access_level": 30
                },
                {
                    "group_id": 3,
                    "group_name": "Gitlab Org",
                    "group_full_path": "gitlab-org",
                    "group_access_level": 10
                }
            ],
            "repository_storage": "default",
            "only_allow_merge_if_pipeline_succeeds": False,
            "only_allow_merge_if_all_discussions_are_resolved": False,
            "printing_merge_requests_link_enabled": True,
            "request_access_enabled": False,
            "merge_method": "merge",
            "approvals_before_merge": 0,
            "statistics": {
                "commit_count": 37,
                "storage_size": 1038090,
                "repository_size": 1038090,
                "lfs_objects_size": 0,
                "job_artifacts_size": 0,
                "packages_size": 0
            },
            "_links": {
                "self": "http://example.com/api/v4/projects",
                "issues": "http://example.com/api/v4/projects/1/issues",
                "merge_requests": "http://example.com/api/v4/projects/1/merge_requests",
                "repo_branches": "http://example.com/api/v4/projects/1/repository_branches",
                "labels": "http://example.com/api/v4/projects/1/labels",
                "events": "http://example.com/api/v4/projects/1/events",
                "members": "http://example.com/api/v4/projects/1/members"
            },
            "members": [
                {
                    "id": 2,
                    "username": "john_doe",
                    "email": "jdoe@email.com",
                    "name": "John Doe",
                    "state": "active",
                    "avatar_url": "https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon",
                    "expires_at": "2012-10-22T14:13:35Z",
                    "access_level": 30
                }
            ]
        }

    def get_mr_approval_configuration(self):
        '''
            Simulates a /projects/:id/approvals request
        '''
        return {
            "approvers": [
                {
                    "user": {
                        "id": 5,
                        "name": "John Doe6",
                        "username": "user5",
                        "state": "active",
                        "avatar_url": "https://www.gravatar.com/avatar/4aea8cf834ed91844a2da4ff7ae6b491?s=80\u0026d=identicon"
                    }
                }
            ],
            "approver_groups": [
                {
                    "group": {
                        "id": 1,
                        "name": "group1",
                        "path": "group1",
                        "description": "",
                        "visibility": "public",
                        "lfs_enabled": False,
                        "avatar_url": None,
                        "request_access_enabled": False,
                        "full_name": "group1",
                        "full_path": "group1",
                        "parent_id": None,
                        "ldap_cn": None,
                        "ldap_access": None
                    }
                }
            ],
            "approvals_before_merge": 2,
            "reset_approvals_on_push": True,
            "disable_overriding_approvers_per_merge_request": False
        }

    def get_staged_group_project(self):
        return {
            "snippets_access_level": "enabled",
            "description": "",
            "default_branch": "patch-01",
            "visibility": "public",
            "http_url_to_repo": "https://pse.tanuki.cloud/pmm-demo/spring-app-secure-2.git",
            "shared_runners_enabled": False,
            "project_type": "group",
            "path": "spring-app-secure-2",
            "id": 287,
            "merge_requests_access_level": "enabled",
            "repository_access_level": "enabled",
            "builds_access_level": "enabled",
            "archived": False,
            "name": "spring-app-secure-2",
            "wiki_access_level": "enabled",
            "forking_access_level": "enabled",
            "pages_access_level": "private",
            "namespace": "pmm-demo",
            "members": [],
            "issues_access_level": "enabled",
            "path_with_namespace": "pmm-demo/spring-app-secure-2"
        }

    def get_staged_nested_group_project(self):
        return {
            "snippets_access_level": "enabled",
            "description": "",
            "default_branch": "patch-01",
            "visibility": "public",
            "http_url_to_repo": "https://pse.tanuki.cloud/pmm-demo/spring-app-secure-2.git",
            "shared_runners_enabled": False,
            "project_type": "group",
            "path": "spring-app-secure-2",
            "id": 287,
            "merge_requests_access_level": "enabled",
            "repository_access_level": "enabled",
            "builds_access_level": "enabled",
            "archived": False,
            "name": "spring-app-secure-2",
            "wiki_access_level": "enabled",
            "forking_access_level": "enabled",
            "pages_access_level": "private",
            "namespace": {
                "id": 287,
                "name": "pmm-demo",
                "path": "pmm-demo",
                "kind": "group",
                "full_path": "marketing/pmm/pmm-demo",
                "parent_id": 1
            },
            "members": [],
            "issues_access_level": "enabled",
            "path_with_namespace": "marketing/pmm/pmm-demo/spring-app-secure-2"
        }

    def get_staged_double_nested_group_project(self):
        return {
            "snippets_access_level": "enabled",
            "description": "",
            "default_branch": "patch-01",
            "visibility": "public",
            "http_url_to_repo": "https://pse.tanuki.cloud/marketing/pmm/pmm/pmm-demo/spring-app-secure-2.git",
            "shared_runners_enabled": False,
            "project_type": "group",
            "path": "spring-app-secure-2",
            "id": 287,
            "merge_requests_access_level": "enabled",
            "repository_access_level": "enabled",
            "builds_access_level": "enabled",
            "archived": False,
            "name": "spring-app-secure-2",
            "wiki_access_level": "enabled",
            "forking_access_level": "enabled",
            "pages_access_level": "private",
            "namespace": {
                "id": 287,
                "name": "pmm-demo",
                "path": "pmm-demo",
                "kind": "group",
                "full_path": "marketing/pmm/pmm/pmm-demo",
                "parent_id": 1
            },
            "members": [],
            "issues_access_level": "enabled",
            "path_with_namespace": "marketing/pmm/pmm/pmm-demo/spring-app-secure-2"
        }

    def get_staged_user_project(self):
        return {
            "snippets_access_level": "enabled",
            "description": "",
            "default_branch": "patch-01",
            "visibility": "public",
            "http_url_to_repo": "https://pse.tanuki.cloud/pmm-demo/spring-app-secure-2.git",
            "shared_runners_enabled": False,
            "project_type": "user",
            "path": "spring-app-secure-2",
            "id": 287,
            "merge_requests_access_level": "enabled",
            "repository_access_level": "enabled",
            "builds_access_level": "enabled",
            "archived": False,
            "name": "spring-app-secure-2",
            "wiki_access_level": "enabled",
            "forking_access_level": "enabled",
            "pages_access_level": "private",
            "namespace": "pmm-demo",
            "members": [],
            "issues_access_level": "enabled",
            "path_with_namespace": "pmm-demo/spring-app-secure-2"
        }

    def get_staged_root_project(self):
        return {
            "snippets_access_level": "enabled",
            "description": "",
            "default_branch": "patch-01",
            "visibility": "public",
            "http_url_to_repo": "https://pse.tanuki.cloud/pmm-demo/spring-app-secure-2.git",
            "shared_runners_enabled": False,
            "project_type": "user",
            "path": "spring-app-secure-2",
            "id": 287,
            "merge_requests_access_level": "enabled",
            "repository_access_level": "enabled",
            "builds_access_level": "enabled",
            "archived": False,
            "name": "spring-app-secure-2",
            "wiki_access_level": "enabled",
            "forking_access_level": "enabled",
            "pages_access_level": "private",
            "namespace": "root",
            "members": [],
            "issues_access_level": "enabled",
            "path_with_namespace": "pmm-demo/spring-app-secure-2"
        }

    def get_staged_projects(self):
        return [
            {
                "archived": False,
                "builds_access_level": "enabled",
                "default_branch": "master",
                "description": "",
                "http_url_to_repo": "https://dictionary.githost.io/dictionary-web/darci.git",
                "id": 132,
                "issues_access_level": "enabled",
                "members": [],
                "merge_requests_access_level": "enabled",
                "name": "darci1",
                "namespace": "dictionary-web",
                "project_type": "group",
                "repository_access_level": "enabled",
                "shared_runners_enabled": False,
                "snippets_access_level": "disabled",
                "visibility": "private",
                "wiki_access_level": "enabled",
                "forking_access_level": "enabled",
                "pages_access_level": "private"
            },
            {
                "archived": False,
                "builds_access_level": "enabled",
                "default_branch": "master",
                "description": "",
                "http_url_to_repo": "https://dictionary.githost.io/dictionary-web/darci.git",
                "id": 133,
                "issues_access_level": "enabled",
                "members": [],
                "merge_requests_access_level": "enabled",
                "name": "darci2",
                "namespace": "dictionary-web",
                "project_type": "group",
                "repository_access_level": "enabled",
                "shared_runners_enabled": False,
                "snippets_access_level": "disabled",
                "visibility": "private",
                "wiki_access_level": "enabled",
                "forking_access_level": "enabled",
                "pages_access_level": "private"
            },
            {
                "archived": True,
                "builds_access_level": "enabled",
                "default_branch": "master",
                "description": "",
                "http_url_to_repo": "https://dictionary.githost.io/dictionary-web/darci.git",
                "id": 134,
                "issues_access_level": "enabled",
                "members": [],
                "merge_requests_access_level": "enabled",
                "name": "darci3",
                "namespace": "dictionary-web",
                "project_type": "group",
                "repository_access_level": "enabled",
                "shared_runners_enabled": False,
                "snippets_access_level": "disabled",
                "visibility": "private",
                "wiki_access_level": "enabled",
                "forking_access_level": "enabled",
                "pages_access_level": "private"
            }
        ]

    def get_staged_project_no_default_branch(self):
        return [
            {
                "archived": False,
                "builds_access_level": "enabled",
                "description": "",
                "http_url_to_repo": "https://dictionary.githost.io/dictionary-web/darci.git",
                "id": 132,
                "issues_access_level": "enabled",
                "members": [],
                "merge_requests_access_level": "enabled",
                "name": "darci1",
                "namespace": "dictionary-web",
                "project_type": "group",
                "repository_access_level": "enabled",
                "shared_runners_enabled": False,
                "snippets_access_level": "disabled",
                "visibility": "private",
                "wiki_access_level": "enabled",
                "forking_access_level": "enabled",
                "pages_access_level": "private"
            }
        ]

    def get_mix_staged_projects(self):
        return [
            {
                "snippets_access_level": "enabled",
                "description": "",
                "default_branch": "patch-01",
                "visibility": "public",
                "http_url_to_repo": "https://pse.tanuki.cloud/pmm-demo/spring-app-secure-1.git",
                "shared_runners_enabled": False,
                "project_type": "group",
                "path": "spring-app-secure-1",
                "id": 287,
                "merge_requests_access_level": "enabled",
                "repository_access_level": "enabled",
                "builds_access_level": "enabled",
                "archived": False,
                "name": "spring-app-secure-1",
                "wiki_access_level": "enabled",
                "forking_access_level": "enabled",
                "pages_access_level": "private",
                "namespace": "pmm-demo",
                "members": [],
                "issues_access_level": "enabled",
                "path_with_namespace": "pmm-demo/spring-app-secure-1"
            },
            {
                "snippets_access_level": "enabled",
                "description": "",
                "default_branch": "patch-01",
                "visibility": "public",
                "http_url_to_repo": "https://pse.tanuki.cloud/pmm-demo/spring-app-secure-2.git",
                "shared_runners_enabled": False,
                "project_type": "user",
                "path": "spring-app-secure-2",
                "id": 287,
                "merge_requests_access_level": "enabled",
                "repository_access_level": "enabled",
                "builds_access_level": "enabled",
                "archived": False,
                "name": "spring-app-secure-2",
                "wiki_access_level": "enabled",
                "forking_access_level": "enabled",
                "pages_access_level": "private",
                "namespace": "root",
                "members": [],
                "issues_access_level": "enabled",
                "path_with_namespace": "pmm-demo/spring-app-secure-2"
            },
            {
                "snippets_access_level": "enabled",
                "description": "",
                "default_branch": "patch-01",
                "visibility": "public",
                "http_url_to_repo": "https://pse.tanuki.cloud/pmm-demo/spring-app-secure-3.git",
                "shared_runners_enabled": False,
                "project_type": "user",
                "path": "spring-app-secure-3",
                "id": 287,
                "merge_requests_access_level": "enabled",
                "repository_access_level": "enabled",
                "builds_access_level": "enabled",
                "archived": False,
                "name": "spring-app-secure-3",
                "wiki_access_level": "enabled",
                "forking_access_level": "enabled",
                "pages_access_level": "private",
                "namespace": "pmm-demo",
                "members": [],
                "issues_access_level": "enabled",
                "path_with_namespace": "pmm-demo/spring-app-secure-3"
            }
        ]

    def get_staged_forked_projects(self):
        return [
            {
                "id": 851,
                "name": "security-reports-fork",
                "namespace": "top-level-group",
                "path": "security-reports-fork",
                "path_with_namespace": "top-level-group/security-reports-fork",
                "visibility": "private",
                "description": "",
                "jobs_enabled": True,
                "project_type": "group",
                "members": [],
                "http_url_to_repo": "https://pse.tanuki.cloud/top-level-group/security-reports-fork.git",
                "shared_runners_enabled": False,
                "archived": False,
                "shared_with_groups": [],
                "forked_from_project": {
                    "avatar_url": None,
                    "created_at": "2019-10-23T15:16:32.391Z",
                    "default_branch": "master",
                    "description": "",
                    "forks_count": 1,
                    "http_url_to_repo": "https://pse.tanuki.cloud/pmm-demo/security-reports.git",
                    "id": 286,
                    "last_activity_at": "2019-10-23T15:16:32.391Z",
                    "name": "security-reports",
                    "name_with_namespace": "pmm-demo / security-reports",
                    "namespace": {
                        "avatar_url": None,
                        "full_path": "pmm-demo",
                        "id": 129,
                        "kind": "group",
                        "name": "pmm-demo",
                        "parent_id": None,
                        "path": "pmm-demo",
                        "web_url": "https://pse.tanuki.cloud/groups/pmm-demo"
                    },
                    "path": "security-reports",
                    "path_with_namespace": "pmm-demo/security-reports",
                    "readme_url": "https://pse.tanuki.cloud/pmm-demo/security-reports/-/blob/master/README.md",
                    "ssh_url_to_repo": "git@pse.tanuki.cloud:pmm-demo/security-reports.git",
                    "star_count": 0,
                    "tag_list": [],
                    "topics": [],
                    "web_url": "https://pse.tanuki.cloud/pmm-demo/security-reports"
                },
                "default_branch": "master"
            },
            {
                "id": 286,
                "name": "security-reports",
                "namespace": "pmm-demo",
                "path": "security-reports",
                "path_with_namespace": "pmm-demo/security-reports",
                "visibility": "public",
                "description": "",
                "jobs_enabled": True,
                "project_type": "group",
                "members": [],
                "http_url_to_repo": "https://pse.tanuki.cloud/pmm-demo/security-reports.git",
                "shared_runners_enabled": False,
                "archived": False,
                "shared_with_groups": [],
                "default_branch": "master"
            }
        ]

    def get_staged_projects_mirrors(self):
        return [
            {
                "enabled": True,
                "id": 101486,
                "last_error": None,
                "last_successful_update_at": "2020-01-06T17:32:02.823Z",
                "last_update_at": "2020-01-06T17:32:02.823Z",
                "last_update_started_at": "2020-01-06T17:31:55.864Z",
                "only_protected_branches": True,
                "keep_divergent_refs": True,
                "update_status": "finished",
                "url": "https://gitlab.example.com/gitlab-org/security/gitlab.git"
            },
            {
                "enabled": True,
                "id": 101487,
                "last_error": "2020-01-08T17:32:02.823Z",
                "last_successful_update_at": "2020-01-06T17:32:02.823Z",
                "last_update_at": "2020-01-06T17:32:02.823Z",
                "last_update_started_at": "2020-01-06T17:31:55.864Z",
                "only_protected_branches": True,
                "keep_divergent_refs": True,
                "update_status": "failed",
                "url": "https://gitlab.example.com/gitlab-org/security/gitlab.git"
            }
        ]

    def get_staged_projects_mirrors_failed(self):
        return [
            {
                "enabled": True,
                "id": 101486,
                "last_error": "2020-01-08T17:32:02.823Z",
                "last_successful_update_at": "2020-01-06T17:32:02.823Z",
                "last_update_at": "2020-01-06T17:32:02.823Z",
                "last_update_started_at": "2020-01-06T17:31:55.864Z",
                "only_protected_branches": True,
                "keep_divergent_refs": True,
                "update_status": "failed",
                "url": "https://gitlab.example.com/gitlab-org/security/gitlab.git"
            },
            {
                "enabled": True,
                "id": 101487,
                "last_error": "2020-01-08T17:32:02.823Z",
                "last_successful_update_at": "2020-01-06T17:32:02.823Z",
                "last_update_at": "2020-01-06T17:32:02.823Z",
                "last_update_started_at": "2020-01-06T17:31:55.864Z",
                "only_protected_branches": True,
                "keep_divergent_refs": True,
                "update_status": "failed",
                "url": "https://gitlab.example.com/gitlab-org/security/gitlab.git"
            }
        ]
