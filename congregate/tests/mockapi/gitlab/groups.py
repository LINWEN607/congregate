class MockGroupsApi():
    '''
        Simulates a /users request with no additional parameters
    '''

    def get_group(self):
        return {
            "id": 4,
            "name": "Twitter",
            "path": "twitter",
            "description": "Aliquid qui quis dignissimos distinctio ut commodi voluptas est.",
            "visibility": "public",
            "avatar_url": None,
            "web_url": "https://gitlab.example.com/groups/twitter",
            "request_access_enabled": False,
            "full_name": "Twitter",
            "full_path": "twitter",
            "file_template_project_id": 1,
            "parent_id": None,
            "shared_runners_minutes_limit": 133,
            "extra_shared_runners_minutes_limit": 133,
            "projects": [
                {
                    "id": 7,
                    "description": "Voluptas veniam qui et beatae voluptas doloremque explicabo facilis.",
                    "default_branch": "master",
                    "tag_list": [],
                    "archived": False,
                    "visibility": "public",
                    "ssh_url_to_repo": "git@gitlab.example.com:twitter/typeahead-js.git",
                    "http_url_to_repo": "https://gitlab.example.com/twitter/typeahead-js.git",
                    "web_url": "https://gitlab.example.com/twitter/typeahead-js",
                    "name": "Typeahead.Js",
                    "name_with_namespace": "Twitter / Typeahead.Js",
                    "path": "typeahead-js",
                    "path_with_namespace": "twitter/typeahead-js",
                    "issues_enabled": True,
                    "merge_requests_enabled": True,
                    "wiki_enabled": True,
                    "jobs_enabled": True,
                    "snippets_enabled": False,
                    "container_registry_enabled": True,
                    "created_at": "2016-06-17T07:47:25.578Z",
                    "last_activity_at": "2016-06-17T07:47:25.881Z",
                    "shared_runners_enabled": True,
                    "creator_id": 1,
                    "namespace": {
                        "id": 4,
                        "name": "Twitter",
                        "path": "twitter",
                        "kind": "group"
                    },
                    "avatar_url": None,
                    "star_count": 0,
                    "forks_count": 0,
                    "open_issues_count": 3,
                    "public_jobs": True,
                    "shared_with_groups": [],
                    "request_access_enabled": False
                },
                {
                    "id": 6,
                    "description": "Aspernatur omnis repudiandae qui voluptatibus eaque.",
                    "default_branch": "master",
                    "tag_list": [],
                    "archived": False,
                    "visibility": "internal",
                    "ssh_url_to_repo": "git@gitlab.example.com:twitter/flight.git",
                    "http_url_to_repo": "https://gitlab.example.com/twitter/flight.git",
                    "web_url": "https://gitlab.example.com/twitter/flight",
                    "name": "Flight",
                    "name_with_namespace": "Twitter / Flight",
                    "path": "flight",
                    "path_with_namespace": "twitter/flight",
                    "issues_enabled": True,
                    "merge_requests_enabled": True,
                    "wiki_enabled": True,
                    "jobs_enabled": True,
                    "snippets_enabled": False,
                    "container_registry_enabled": True,
                    "created_at": "2016-06-17T07:47:24.661Z",
                    "last_activity_at": "2016-06-17T07:47:24.838Z",
                    "shared_runners_enabled": True,
                    "creator_id": 1,
                    "namespace": {
                        "id": 4,
                        "name": "Twitter",
                        "path": "twitter",
                        "kind": "group"
                    },
                    "avatar_url": None,
                    "star_count": 0,
                    "forks_count": 0,
                    "open_issues_count": 8,
                    "public_jobs": True,
                    "shared_with_groups": [],
                    "request_access_enabled": False
                }
            ],
            "shared_projects": [
                {
                    "id": 8,
                    "description": "Velit eveniet provident fugiat saepe eligendi autem.",
                    "default_branch": "master",
                    "tag_list": [],
                    "archived": False,
                    "visibility": "private",
                    "ssh_url_to_repo": "git@gitlab.example.com:h5bp/html5-boilerplate.git",
                    "http_url_to_repo": "https://gitlab.example.com/h5bp/html5-boilerplate.git",
                    "web_url": "https://gitlab.example.com/h5bp/html5-boilerplate",
                    "name": "Html5 Boilerplate",
                    "name_with_namespace": "H5bp / Html5 Boilerplate",
                    "path": "html5-boilerplate",
                    "path_with_namespace": "h5bp/html5-boilerplate",
                    "issues_enabled": True,
                    "merge_requests_enabled": True,
                    "wiki_enabled": True,
                    "jobs_enabled": True,
                    "snippets_enabled": False,
                    "container_registry_enabled": True,
                    "created_at": "2016-06-17T07:47:27.089Z",
                    "last_activity_at": "2016-06-17T07:47:27.310Z",
                    "shared_runners_enabled": True,
                    "creator_id": 1,
                    "namespace": {
                        "id": 5,
                        "name": "H5bp",
                        "path": "h5bp",
                        "kind": "group"
                    },
                    "avatar_url": None,
                    "star_count": 0,
                    "forks_count": 0,
                    "open_issues_count": 4,
                    "public_jobs": True,
                    "shared_with_groups": [
                        {
                            "group_id": 4,
                            "group_name": "Twitter",
                            "group_full_path": "twitter",
                            "group_access_level": 30,
                            "expires_at": None
                        },
                        {
                            "group_id": 3,
                            "group_name": "Gitlab Org",
                            "group_full_path": "gitlab-org",
                            "group_access_level": 10,
                            "expires_at": "2018-08-14"
                        }
                    ]
                }
            ]
        }

    def get_subgroup(self):
        return {
            "id": 4,
            "name": "Twitter",
            "path": "twitter",
            "description": "Aliquid qui quis dignissimos distinctio ut commodi voluptas est.",
            "visibility": "public",
            "avatar_url": None,
            "web_url": "https://gitlab.example.com/groups/twitter",
            "request_access_enabled": False,
            "full_name": "Twitter",
            "full_path": "twitter",
            "file_template_project_id": 1,
            "parent_id": 1,
            "shared_runners_minutes_limit": 133,
            "extra_shared_runners_minutes_limit": 133,
            "projects": [],
            "shared_projects": []
        }

    def get_all_groups_generator(self):
        groups_list = [
            {
                "id": 1,
                "name": "Foobar Group",
                "path": "foo-bar",
                "description": "An interesting group",
                "visibility": "public",
                "lfs_enabled": True,
                "avatar_url": "http://localhost:3000/uploads/group/avatar/1/foo.jpg",
                "web_url": "http://localhost:3000/groups/foo-bar",
                "request_access_enabled": False,
                "full_name": "Foobar Group",
                "full_path": "foo-bar",
                "file_template_project_id": 1,
                "parent_id": None
            },
            {
                "id": 2,
                "name": "Foobar Group2",
                "path": "foo-bar-2",
                "description": "An interesting group as well",
                "visibility": "public",
                "lfs_enabled": True,
                "avatar_url": "http://localhost:3000/uploads/group/avatar/1/foo.jpg",
                "web_url": "http://localhost:3000/groups/foo-bar-2",
                "request_access_enabled": False,
                "full_name": "Foobar Group 2",
                "full_path": "foo-bar-2",
                "file_template_project_id": 1,
                "parent_id": None
            }
        ]
        yield groups_list

    def get_all_groups_list(self):
        return [
            {
                "id": 1,
                "name": "Foobar Group",
                "path": "foo-bar",
                "description": "An interesting group",
                "visibility": "public",
                "lfs_enabled": True,
                "avatar_url": "http://localhost:3000/uploads/group/avatar/1/foo.jpg",
                "web_url": "http://localhost:3000/groups/foo-bar",
                "request_access_enabled": False,
                "full_name": "Foobar Group",
                "full_path": "foo-bar",
                "file_template_project_id": 1,
                "parent_id": None,
                "members": [
                    {
                        "username": "smart3",
                        "web_url": "http://demo.tanuki.cloud/smart3",
                        "name": "User smart3",
                        "expires_at": None,
                        "access_level": 50,
                        "state": "active",
                        "avatar_url": "https://secure.gravatar.com/avatar/d549ee47080f3512a835905895c46545?s=80&d=identicon",
                        "id": 285
                    },
                    {
                        "username": "smart4",
                        "web_url": "http://demo.tanuki.cloud/smart4",
                        "name": "User smart4",
                        "expires_at": None,
                        "access_level": 30,
                        "state": "active",
                        "avatar_url": "https://secure.gravatar.com/avatar/77b6da6e1b9aa2527600bc7727f5bad8?s=80&d=identicon",
                        "id": 286
                    }
                ],
                "projects": []
            },
            {
                "id": 2,
                "name": "Foobar Group2",
                "path": "foo-bar-2",
                "description": "An interesting group as well",
                "visibility": "public",
                "lfs_enabled": True,
                "avatar_url": "http://localhost:3000/uploads/group/avatar/1/foo.jpg",
                "web_url": "http://localhost:3000/groups/foo-bar-2",
                "request_access_enabled": False,
                "full_name": "Foobar Group 2",
                "full_path": "foo-bar-2",
                "file_template_project_id": 1,
                "parent_id": None,
                "members": [
                    {
                        "username": "smart3",
                        "web_url": "http://demo.tanuki.cloud/smart3",
                        "name": "User smart3",
                        "expires_at": None,
                        "access_level": 50,
                        "state": "active",
                        "avatar_url": "https://secure.gravatar.com/avatar/d549ee47080f3512a835905895c46545?s=80&d=identicon",
                        "id": 285
                    },
                    {
                        "username": "smart4",
                        "web_url": "http://demo.tanuki.cloud/smart4",
                        "name": "User smart4",
                        "expires_at": None,
                        "access_level": 30,
                        "state": "active",
                        "avatar_url": "https://secure.gravatar.com/avatar/77b6da6e1b9aa2527600bc7727f5bad8?s=80&d=identicon",
                        "id": 286
                    }
                ],
                "projects": []
            },
            {
                "id": 3,
                "name": "Foobar Group3",
                "path": "foo-bar-3",
                "description": "An interesting group as well",
                "visibility": "public",
                "lfs_enabled": True,
                "avatar_url": "http://localhost:3000/uploads/group/avatar/1/foo.jpg",
                "web_url": "http://localhost:3000/groups/foo-bar-2",
                "request_access_enabled": False,
                "full_name": "Foobar Group 3",
                "full_path": "foo-bar-3",
                "file_template_project_id": 1,
                "parent_id": None,
                "members": [
                    {
                        "username": "smart3",
                        "web_url": "http://demo.tanuki.cloud/smart3",
                        "name": "User smart3",
                        "expires_at": None,
                        "access_level": 50,
                        "state": "active",
                        "avatar_url": "https://secure.gravatar.com/avatar/d549ee47080f3512a835905895c46545?s=80&d=identicon",
                        "id": 285
                    },
                    {
                        "username": "smart4",
                        "web_url": "http://demo.tanuki.cloud/smart4",
                        "name": "User smart4",
                        "expires_at": None,
                        "access_level": 30,
                        "state": "active",
                        "avatar_url": "https://secure.gravatar.com/avatar/77b6da6e1b9aa2527600bc7727f5bad8?s=80&d=identicon",
                        "id": 286
                    }
                ],
                "projects": [
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
                    }
                ]
            },
            {
                "id": 4,
                "name": "Foobar Group3",
                "path": "foo-bar-3",
                "description": "An interesting group as well",
                "visibility": "public",
                "lfs_enabled": True,
                "avatar_url": "http://localhost:3000/uploads/group/avatar/1/foo.jpg",
                "web_url": "http://localhost:3000/groups/foo-bar-2",
                "request_access_enabled": False,
                "full_name": "Foobar Group 3",
                "full_path": "foo-bar-3",
                "file_template_project_id": 1,
                "parent_id": None,
                "members": [
                    {
                        "username": "smart3",
                        "web_url": "http://demo.tanuki.cloud/smart3",
                        "name": "User smart3",
                        "expires_at": None,
                        "access_level": 50,
                        "state": "active",
                        "avatar_url": "https://secure.gravatar.com/avatar/d549ee47080f3512a835905895c46545?s=80&d=identicon",
                        "id": 285
                    },
                    {
                        "username": "smart4",
                        "web_url": "http://demo.tanuki.cloud/smart4",
                        "name": "User smart4",
                        "expires_at": None,
                        "access_level": 30,
                        "state": "active",
                        "avatar_url": "https://secure.gravatar.com/avatar/77b6da6e1b9aa2527600bc7727f5bad8?s=80&d=identicon",
                        "id": 286
                    }
                ],
                "projects": [
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
                ]
            }
        ]

    def get_all_subgroups_list(self):
        return [
            {
                "id": 1,
                "name": "Foobar Group",
                "path": "foo-bar",
                "description": "An interesting group",
                "visibility": "public",
                "lfs_enabled": True,
                "avatar_url": "http://localhost:3000/uploads/group/avatar/1/foo.jpg",
                "web_url": "http://localhost:3000/groups/foo-bar",
                "request_access_enabled": False,
                "full_name": "Foobar Group",
                "full_path": "foo-bar",
                "file_template_project_id": 1,
                "parent_id": None,
            },
            {
                "id": 2,
                "name": "Foobar Group2",
                "path": "foo-bar-2",
                "description": "An interesting group as well",
                "visibility": "public",
                "lfs_enabled": True,
                "avatar_url": "http://localhost:3000/uploads/group/avatar/1/foo.jpg",
                "web_url": "http://localhost:3000/groups/foo-bar-2",
                "request_access_enabled": False,
                "full_name": "Foobar Group 2",
                "full_path": "foo-bar-2",
                "file_template_project_id": 1,
                "parent_id": None,
            },
            {
                "id": 3,
                "name": "Foobar Group3",
                "path": "foo-bar-3",
                "description": "An interesting group as well",
                "visibility": "public",
                "lfs_enabled": True,
                "avatar_url": "http://localhost:3000/uploads/group/avatar/1/foo.jpg",
                "web_url": "http://localhost:3000/groups/foo-bar-2",
                "request_access_enabled": False,
                "full_name": "Foobar Group 3",
                "full_path": "foo-bar-3",
                "file_template_project_id": 1,
                "parent_id": None,
            },
            {
                "id": 4,
                "name": "Foobar Group3",
                "path": "foo-bar-3",
                "description": "An interesting group as well",
                "visibility": "public",
                "lfs_enabled": True,
                "avatar_url": "http://localhost:3000/uploads/group/avatar/1/foo.jpg",
                "web_url": "http://localhost:3000/groups/foo-bar-2",
                "request_access_enabled": False,
                "full_name": "Foobar Group 3",
                "full_path": "foo-bar-3",
                "file_template_project_id": 1,
                "parent_id": None,
            }
        ]

    def get_group_404(self):
        return {
            "message": "404 Group Not Found"
        }

    def get_group_members(self):
        return [
            {
                "username": "smart1",
                "web_url": "http://demo.tanuki.cloud/smart1",
                "name": "User smart1",
                "expires_at": None,
                "access_level": 30,
                "state": "blocked",
                "avatar_url": "https://secure.gravatar.com/avatar/d549ee47080f3512a835905895c46545?s=80&d=identicon",
                "id": 284
            },
            {
                "username": "smart2",
                "web_url": "http://demo.tanuki.cloud/smart2",
                "name": "User smart2",
                "expires_at": None,
                "access_level": 40,
                "state": "blocked",
                "avatar_url": "https://secure.gravatar.com/avatar/d549ee47080f3512a835905895c46545?s=80&d=identicon",
                "id": 285
            },
            {
                "username": "smart3",
                "web_url": "http://demo.tanuki.cloud/smart3",
                "name": "User smart3",
                "expires_at": None,
                "access_level": 50,
                "state": "active",
                "avatar_url": "https://secure.gravatar.com/avatar/77b6da6e1b9aa2527600bc7727f5bad8?s=80&d=identicon",
                "id": 286
            }
        ]

    def get_staged_groups(self):
        return [
            {
                "lfs_enabled": True,
                "request_access_enabled": False,
                "project_creation_level": "developer",
                "subgroup_creation_level": "owner",
                "path": "pmm-demo-1",
                "id": 129,
                "parent_id": 814,
                "share_with_group_lock": False,
                "description": "PMM Demos",
                "two_factor_grace_period": 48,
                "visibility": "public",
                "members": [],
                "name": "pmm-demo-1",
                "require_two_factor_authentication": False,
                "full_path": "pmm-demo-1"
            },
            {
                "lfs_enabled": True,
                "request_access_enabled": False,
                "project_creation_level": "developer",
                "subgroup_creation_level": "owner",
                "path": "pmm-demo-2",
                "id": 129,
                "parent_id": 814,
                "share_with_group_lock": False,
                "description": "PMM Demos",
                "two_factor_grace_period": 48,
                "visibility": "public",
                "members": [],
                "name": "pmm-demo-2",
                "require_two_factor_authentication": False,
                "full_path": "pmm-demo-2"
            },
            {
                "lfs_enabled": True,
                "request_access_enabled": False,
                "project_creation_level": "developer",
                "subgroup_creation_level": "owner",
                "path": "pmm-demo-3",
                "id": 129,
                "parent_id": 814,
                "share_with_group_lock": False,
                "description": "PMM Demos",
                "two_factor_grace_period": 48,
                "visibility": "public",
                "members": [],
                "name": "pmm-demo-3",
                "require_two_factor_authentication": False,
                "full_path": "pmm-demo-3"
            }
        ]

    def get_dummy_group(self):
        return [
            {
                "avatar_url": None,
                "description": "",
                "file_template_project_id": None,
                "full_path": "jdoe-testing",
                "id": 279,
                "lfs_enabled": True,
                "members": [
                    {
                        "access_level": 50,
                        "avatar_url": "https://secure.gravatar.com/avatar/9fad1e062ce5cc63b1fbb5f9cc43e94c?s=80&d=identicon",
                        "expires_at": None,
                        "id": 86,
                        "name": "John Doe",
                        "state": "active",
                        "username": "jdoe",
                        "web_url": "https://gitlab.demo.i2p.online/jdoe"
                    },
                    {
                        "access_level": 50,
                        "avatar_url": "https://secure.gravatar.com/avatar/9fad1e062ce5cc63b1fbb5f9cc43e94c?s=80&d=identicon",
                        "expires_at": None,
                        "id": 87,
                        "name": "John Doe 2",
                        "state": "blocked",
                        "username": "jdoe2",
                        "web_url": "https://gitlab.demo.i2p.online/jdoe2"
                    },
                    {
                        "access_level": 50,
                        "avatar_url": "https://secure.gravatar.com/avatar/9fad1e062ce5cc63b1fbb5f9cc43e94c?s=80&d=identicon",
                        "expires_at": None,
                        "id": 88,
                        "name": "John Doe 3",
                        "state": "blocked",
                        "username": "jdoe3",
                        "web_url": "https://gitlab.demo.i2p.online/jdoe3"
                    }
                ],
                "name": "jdoe-testing",
                "parent_id": 244,
                "path": "jdoe-testing",
                "request_access_enabled": False,
                "visibility": "private"
            }
        ]

    def get_dummy_group_active_members(self):
        return [
            {
                "avatar_url": None,
                "description": "",
                "file_template_project_id": None,
                "full_path": "jdoe-testing",
                "id": 279,
                "lfs_enabled": True,
                "members": [
                    {
                        "access_level": 50,
                        "avatar_url": "https://secure.gravatar.com/avatar/9fad1e062ce5cc63b1fbb5f9cc43e94c?s=80&d=identicon",
                        "expires_at": None,
                        "id": 86,
                        "name": "John Doe",
                        "state": "active",
                        "username": "jdoe",
                        "web_url": "https://gitlab.demo.i2p.online/jdoe"
                    }
                ],
                "name": "jdoe-testing",
                "parent_id": 244,
                "path": "jdoe-testing",
                "request_access_enabled": False,
                "visibility": "private"
            }
        ]
