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
                ]
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
                ]
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
                ]
            }
        ]

    def get_group_404(self):
        return {
            "message": "404 Group Not Found"
        }
