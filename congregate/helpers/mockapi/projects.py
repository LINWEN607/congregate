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
                "web_url": "http://example.com/diaspora/diaspora-client",
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
                        "issues_enabled": True,
                        "open_issues_count": 1,
                        "merge_requests_enabled": True,
                        "jobs_enabled": True,
                        "wiki_enabled": True,
                        "snippets_enabled": False,
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
            },
            {
                "id": 6,
                "description": None,
                "default_branch": "master",
                "visibility": "private",
                "ssh_url_to_repo": "git@example.com:brightbox/puppet.git",
                "http_url_to_repo": "http://example.com/brightbox/puppet.git",
                "web_url": "http://example.com/brightbox/puppet",
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
                        "issues_enabled": True,
                        "open_issues_count": 1,
                        "merge_requests_enabled": True,
                        "jobs_enabled": True,
                        "wiki_enabled": True,
                        "snippets_enabled": False,
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
                }
            },
            {
                "id": 80,
                "description": None,
                "default_branch": "master",
                "visibility": "private",
                "ssh_url_to_repo": "git@example.com:brightbox/puppet.git",
                "http_url_to_repo": "http://example.com/brightbox/puppet.git",
                "web_url": "http://example.com/brightbox/puppet",
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
                        "issues_enabled": True,
                        "open_issues_count": 1,
                        "merge_requests_enabled": True,
                        "jobs_enabled": True,
                        "wiki_enabled": True,
                        "snippets_enabled": False,
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
                }
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
            "web_url": "http://example.com/diaspora/diaspora-project-site",
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
            "issues_enabled": True,
            "open_issues_count": 1,
            "merge_requests_enabled": True,
            "jobs_enabled": True,
            "wiki_enabled": True,
            "snippets_enabled": False,
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
                    "web_url": "http://localhost:3000/groups/diaspora"
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
            }
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
                        "state": "active", "avatar_url": "https://www.gravatar.com/avatar/4aea8cf834ed91844a2da4ff7ae6b491?s=80\u0026d=identicon", "web_url": "http://localhost/user5"
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
                        "web_url": "http://localhost/groups/group1",
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
