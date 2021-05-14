class MockUsersApi():
    '''
        Simulates a /users request with no additional parameters
    '''

    def get_user_gen(self):
        return {
            'name': 'John Doe',
            'username': 'jdoe',
            'state': 'active',
            'avatar_url': '',
            'web_url': 'https://dummy.gitlab.io/jdoe',
            'created_at': '2017-06-07T20:29:25.345Z',
            'bio': None,
            'location': None,
            'public_email': '',
            'skype': '',
            'linkedin': '',
            'twitter': '',
            'website_url': '',
            'organization': None,
            'email': 'jdoe@email.com',
            'theme_id': None,
            'color_scheme_id': 5,
            'projects_limit': 10,
            'can_create_group': True,
            'can_create_project': True,
            'two_factor_enabled': False,
            'external': False,
            'private_profile': None,
            'is_admin': False,
            'highest_role': 50,
            'shared_runners_minutes_limit': None,
            'extra_shared_runners_minutes_limit': None,
            'skip_confirmation': True,
            'reset_password': False,
            'force_random_password': True
        }

    def get_current_user(self):
        return {
            "id": 1,
            "username": "root",
            "name": "John Smith",
            "state": "active",
            "avatar_url": "http://localhost:3000/uploads/user/avatar/1/cd8.jpeg"
        }

    def get_admin_user(self):
        return {
            "id": 1,
            "username": "root",
            "name": "John Smith",
            "state": "active",
            "avatar_url": "http://localhost:3000/uploads/user/avatar/1/cd8.jpeg",
            "is_admin": True
        }

    def get_user_401(self):
        return {
            "message": "401 Unauthorized"
        }

    def get_user_400(self):
        return {
            "message": {
                "identities.name_id": [
                    "can't be blank"
                ]
            }
        }

    def get_user_404(self):
        return {
            "message": "404 User Not Found"
        }

    def get_all_users_generator(self):
        users = [
            {
                "id": 1,
                "username": "john_smith",
                "name": "John Smith",
                "state": "active",
                "avatar_url": "http://localhost:3000/uploads/user/avatar/1/cd8.jpeg",
            },
            {
                "id": 2,
                "username": "jack_smith",
                "name": "Jack Smith",
                "state": "blocked",
                "avatar_url": "http://gravatar.com/../e32131cd8.jpeg",
            }
        ]
        yield users

    def get_all_users_list(self):
        return [
            {
                "id": 2,
                "username": "john_doe",
                "name": "John Doe",
                "state": "active",
                "avatar_url": "https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon",
                "expires_at": "2012-10-22T14:13:35Z",
                "access_level": 30,
                "email": "jdoe@email.com"
            },
            {
                "username": "smart3",
                "name": "User smart3",
                "expires_at": None,
                "access_level": 50,
                "state": "active",
                "avatar_url": "https://secure.gravatar.com/avatar/d549ee47080f3512a835905895c46545?s=80&d=identicon",
                "id": 285,
                "email": "jdoe2@email.com"
            },
            {
                "username": "smart4",
                "name": "User smart4",
                "expires_at": None,
                "access_level": 30,
                "state": "active",
                "avatar_url": "https://secure.gravatar.com/avatar/77b6da6e1b9aa2527600bc7727f5bad8?s=80&d=identicon",
                "id": 286,
                "email": "jdoe3@email.com"
            }
        ]

    def get_project_members(self):
        return [
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

    def get_dummy_user(self):
        return {
            "id": 27,
            "name": "John Doe",
            "username": "jdoe",
            "state": "active",
            "avatar_url": "",
            "web_url": "https://dummy.gitlab.io/jdoe",
            "created_at": "2017-06-07T20:29:25.345Z",
            "bio": None,
            "location": None,
            "public_email": "",
            "skype": "",
            "linkedin": "",
            "twitter": "",
            "website_url": "",
            "organization": None,
            "last_sign_in_at": "2019-06-24T19:56:28.486Z",
            "confirmed_at": "2017-06-07T20:29:24.795Z",
            "last_activity_on": "2019-07-17",
            "email": "jdoe@email.com",
            "theme_id": None,
            "color_scheme_id": 5,
            "projects_limit": 10,
            "current_sign_in_at": "2019-07-17T16:49:12.936Z",
            "identities": [
                {
                    "provider": "okta",
                    "extern_uid": "jdoe|someCompany|okta",
                    "saml_provider_id": 1111
                }
            ],
            "can_create_group": True,
            "can_create_project": True,
            "two_factor_enabled": False,
            "external": False,
            "private_profile": None,
            "is_admin": False,
            "highest_role": 50,
            "shared_runners_minutes_limit": None,
            "extra_shared_runners_minutes_limit": None
        }

    def get_dummy_user_blocked(self):
        return {
            "id": 27,
            "name": "John Doe",
            "username": "jdoe",
            "state": "blocked",
            "avatar_url": "",
            "web_url": "https://dummy.gitlab.io/jdoe",
            "created_at": "2017-06-07T20:29:25.345Z",
            "bio": None,
            "location": None,
            "public_email": "",
            "skype": "",
            "linkedin": "",
            "twitter": "",
            "website_url": "",
            "organization": None,
            "last_sign_in_at": "2019-06-24T19:56:28.486Z",
            "confirmed_at": "2017-06-07T20:29:24.795Z",
            "last_activity_on": "2019-07-17",
            "email": "jdoe@email.com",
            "theme_id": None,
            "color_scheme_id": 5,
            "projects_limit": 10,
            "current_sign_in_at": "2019-07-17T16:49:12.936Z",
            "identities": [],
            "can_create_group": True,
            "can_create_project": True,
            "two_factor_enabled": False,
            "external": False,
            "private_profile": None,
            "is_admin": False,
            "highest_role": 50,
            "shared_runners_minutes_limit": None,
            "extra_shared_runners_minutes_limit": None
        }

    def get_dummy_old_users(self):
        return [
            {
                "id": 3,
                "username": "raymond_smith",
                "name": "Raymond Smith",
                "state": "active",
                "avatar_url": "",
                "web_url": "https://dummy.gitlab.io/jdoe",
                "created_at": "2017-06-07T20:29:25.345Z",
                "bio": None,
                "location": None,
                "public_email": "",
                "skype": "",
                "linkedin": "",
                "twitter": "",
                "website_url": "",
                "organization": None,
                "last_sign_in_at": "2019-06-24T19:56:28.486Z",
                "confirmed_at": "2017-06-07T20:29:24.795Z",
                "last_activity_on": "2019-07-17",
                "email": "rsmith@email.com",
                "theme_id": None,
                "color_scheme_id": 5,
                "projects_limit": 10,
                "current_sign_in_at": "2019-07-17T16:49:12.936Z",
                "identities": [],
                "can_create_group": True,
                "can_create_project": True,
                "two_factor_enabled": False,
                "external": False,
                "private_profile": None,
                "is_admin": False,
                "highest_role": 50,
                "shared_runners_minutes_limit": None,
                "extra_shared_runners_minutes_limit": None
            }, {
                "id": 2,
                "name": "John Doe",
                "username": "jdoe",
                "state": "active",
                "avatar_url": "",
                "web_url": "https://dummy.gitlab.io/jdoe",
                "created_at": "2017-06-07T20:29:25.345Z",
                "bio": None,
                "location": None,
                "public_email": "",
                "skype": "",
                "linkedin": "",
                "twitter": "",
                "website_url": "",
                "organization": None,
                "last_sign_in_at": "2019-06-24T19:56:28.486Z",
                "confirmed_at": "2017-06-07T20:29:24.795Z",
                "last_activity_on": "2019-07-17",
                "email": "jdoe@email.com",
                "theme_id": None,
                "color_scheme_id": 5,
                "projects_limit": 10,
                "current_sign_in_at": "2019-07-17T16:49:12.936Z",
                "identities": [],
                "can_create_group": True,
                "can_create_project": True,
                "two_factor_enabled": False,
                "external": False,
                "private_profile": None,
                "is_admin": False,
                "highest_role": 50,
                "shared_runners_minutes_limit": None,
                "extra_shared_runners_minutes_limit": None
            }
        ]

    def get_test_new_destination_users(self):
        return [
            {
                "id": 28,
                "username": "raymond_smith",
                "name": "Raymond Smith",
                "state": "active",
                "avatar_url": "",
                "web_url": "https://dummy.gitlab.io/jdoe",
                "created_at": "2017-06-07T20:29:25.345Z",
                "bio": None,
                "location": None,
                "public_email": "",
                "skype": "",
                "linkedin": "",
                "twitter": "",
                "website_url": "",
                "organization": None,
                "last_sign_in_at": "2019-06-24T19:56:28.486Z",
                "confirmed_at": "2017-06-07T20:29:24.795Z",
                "last_activity_on": "2019-07-17",
                "email": "rsmith@email.com",
                "theme_id": None,
                "color_scheme_id": 5,
                "projects_limit": 10,
                "current_sign_in_at": "2019-07-17T16:49:12.936Z",
                "identities": [],
                "can_create_group": True,
                "can_create_project": True,
                "two_factor_enabled": False,
                "external": False,
                "private_profile": None,
                "is_admin": False,
                "highest_role": 50,
                "shared_runners_minutes_limit": None,
                "extra_shared_runners_minutes_limit": None
            }, {
                "id": 27,
                "name": "John Doe",
                "username": "jdoe",
                "state": "blocked",
                "avatar_url": "",
                "web_url": "https://dummy.gitlab.io/jdoe",
                "created_at": "2017-06-07T20:29:25.345Z",
                "bio": None,
                "location": None,
                "public_email": "",
                "skype": "",
                "linkedin": "",
                "twitter": "",
                "website_url": "",
                "organization": None,
                "last_sign_in_at": "2019-06-24T19:56:28.486Z",
                "confirmed_at": "2017-06-07T20:29:24.795Z",
                "last_activity_on": "2019-07-17",
                "email": "jdoe@email.com",
                "theme_id": None,
                "color_scheme_id": 5,
                "projects_limit": 10,
                "current_sign_in_at": "2019-07-17T16:49:12.936Z",
                "identities": [],
                "can_create_group": True,
                "can_create_project": True,
                "two_factor_enabled": False,
                "external": False,
                "private_profile": None,
                "is_admin": False,
                "highest_role": 50,
                "shared_runners_minutes_limit": None,
                "extra_shared_runners_minutes_limit": None
            }
        ]

    def get_dummy_new_users_active(self):
        return [
            {
                "id": 28,
                "username": "raymond_smith",
                "name": "Raymond Smith",
                "state": "active",
                "avatar_url": "",
                "web_url": "https://dummy.gitlab.io/jdoe",
                "created_at": "2017-06-07T20:29:25.345Z",
                "bio": None,
                "location": None,
                "public_email": "",
                "skype": "",
                "linkedin": "",
                "twitter": "",
                "website_url": "",
                "organization": None,
                "last_sign_in_at": "2019-06-24T19:56:28.486Z",
                "confirmed_at": "2017-06-07T20:29:24.795Z",
                "last_activity_on": "2019-07-17",
                "email": "rsmith@email.com",
                "theme_id": None,
                "color_scheme_id": 5,
                "projects_limit": 10,
                "current_sign_in_at": "2019-07-17T16:49:12.936Z",
                "identities": [],
                "can_create_group": True,
                "can_create_project": True,
                "two_factor_enabled": False,
                "external": False,
                "private_profile": None,
                "is_admin": False,
                "highest_role": 50,
                "shared_runners_minutes_limit": None,
                "extra_shared_runners_minutes_limit": None
            }
        ]

    def get_dummy_project(self):
        return [
            {
                "archived": False,
                "builds_access_level": "enabled",
                "default_branch": "master",
                "description": "",
                "http_url_to_repo": "https://gitlab.demo.i2p.online/jdoe-testing/hello-world-spring-boot.git",
                "id": 348,
                "issues_access_level": "enabled",
                "members": [
                    {
                        "access_level": 40,
                        "avatar_url": "https://secure.gravatar.com/avatar/9fad1e062ce5cc63b1fbb5f9cc43e94c?s=80&d=identicon",
                        "expires_at": None,
                        "id": 86,
                        "name": "John Doe",
                        "state": "active",
                        "username": "jdoe",
                        "web_url": "https://gitlab.demo.i2p.online/jdoe"
                    },
                    {
                        "access_level": 40,
                        "avatar_url": "https://secure.gravatar.com/avatar/9fad1e062ce5cc63b1fbb5f9cc43e94c?s=80&d=identicon",
                        "expires_at": None,
                        "id": 87,
                        "name": "John Doe 2",
                        "state": "blocked",
                        "username": "jdoe2",
                        "web_url": "https://gitlab.demo.i2p.online/jdoe2"
                    },
                    {
                        "access_level": 40,
                        "avatar_url": "https://secure.gravatar.com/avatar/9fad1e062ce5cc63b1fbb5f9cc43e94c?s=80&d=identicon",
                        "expires_at": None,
                        "id": 88,
                        "name": "John Doe 3",
                        "state": "blocked",
                        "username": "jdoe3",
                        "web_url": "https://gitlab.demo.i2p.online/jdoe3"
                    }
                ],
                "merge_requests_access_level": "enabled",
                "path_with_namespace": "jdoe-testing/hello-world-spring-boot",
                "name": "hello-world-spring-boot",
                "namespace": "jdoe-testing",
                "project_type": "group",
                "repository_access_level": "enabled",
                "shared_runners_enabled": True,
                "snippets_access_level": "enabled",
                "visibility": "private",
                "wiki_access_level": "enabled"
            }
        ]

    def get_dummy_project_active_members(self):
        return [
            {
                "archived": False,
                "builds_access_level": "enabled",
                "default_branch": "master",
                "description": "",
                "http_url_to_repo": "https://gitlab.demo.i2p.online/jdoe-testing/hello-world-spring-boot.git",
                "id": 348,
                "issues_access_level": "enabled",
                "members": [
                    {
                        "access_level": 40,
                        "avatar_url": "https://secure.gravatar.com/avatar/9fad1e062ce5cc63b1fbb5f9cc43e94c?s=80&d=identicon",
                        "expires_at": None,
                        "id": 86,
                        "name": "John Doe",
                        "state": "active",
                        "username": "jdoe",
                        "web_url": "https://gitlab.demo.i2p.online/jdoe"
                    }
                ],
                "merge_requests_access_level": "enabled",
                "path_with_namespace": "jdoe-testing/hello-world-spring-boot",
                "name": "hello-world-spring-boot",
                "namespace": "jdoe-testing",
                "project_type": "group",
                "repository_access_level": "enabled",
                "shared_runners_enabled": True,
                "snippets_access_level": "enabled",
                "visibility": "private",
                "wiki_access_level": "enabled"
            }
        ]

    def get_dummy_staged_user(self):
        return {
            "two_factor_enabled": False,
            "can_create_project": True,
            "twitter": "",
            "shared_runners_minutes_limit": None,
            "linkedin": "",
            "color_scheme_id": 1,
            "skype": "",
            "is_admin": False,
            "identities": [],
            "id": 2,
            "projects_limit": 100000,
            "note": None,
            "state": "active",
            "location": None,
            "email": "iwdewfsfdyyazqnpkwga@examplegitlab.com",
            "website_url": "",
            "job_title": "",
            "username": "RzKciDiyEzvtSqEicsvW",
            "bio": None,
            "work_information": None,
            "private_profile": False,
            "external": False,
            "organization": None,
            "public_email": "",
            "extra_shared_runners_minutes_limit": None,
            "name": "FrhUbyTGMoXQUTeaMgFW",
            "can_create_group": True,
            "avatar_url": "https://www.gravatar.com/avatar/a0290f87758efba7e7be1ed96b2e5ac1?s=80&d=identicon",
            "theme_id": 1
        }

    def get_test_source_users(self):
        return [
            {
                "id": 28,
                "username": "raymond_smith",
                "name": "Raymond Smith",
                "state": "active",
                "avatar_url": "",
                "web_url": "https://dummy.gitlab.io/jdoe",
                "created_at": "2017-06-07T20:29:25.345Z",
                "bio": None,
                "location": None,
                "public_email": "",
                "skype": "",
                "linkedin": "",
                "twitter": "",
                "website_url": "",
                "organization": None,
                "last_sign_in_at": "2019-06-24T19:56:28.486Z",
                "confirmed_at": "2017-06-07T20:29:24.795Z",
                "last_activity_on": "2019-07-17",
                "email": "RSmith@email.com",
                "theme_id": None,
                "color_scheme_id": 5,
                "projects_limit": 10,
                "current_sign_in_at": "2019-07-17T16:49:12.936Z",
                "identities": [],
                "can_create_group": True,
                "can_create_project": True,
                "two_factor_enabled": False,
                "external": False,
                "private_profile": None,
                "is_admin": False,
                "highest_role": 50,
                "shared_runners_minutes_limit": None,
                "extra_shared_runners_minutes_limit": None
            }, {
                "id": 27,
                "name": "John Doe",
                "username": "jdoe",
                "state": "blocked",
                "avatar_url": "",
                "web_url": "https://dummy.gitlab.io/jdoe",
                "created_at": "2017-06-07T20:29:25.345Z",
                "bio": None,
                "location": None,
                "public_email": "",
                "skype": "",
                "linkedin": "",
                "twitter": "",
                "website_url": "",
                "organization": None,
                "last_sign_in_at": "2019-06-24T19:56:28.486Z",
                "confirmed_at": "2017-06-07T20:29:24.795Z",
                "last_activity_on": "2019-07-17",
                "email": "JDoe@email.com",
                "theme_id": None,
                "color_scheme_id": 5,
                "projects_limit": 10,
                "current_sign_in_at": "2019-07-17T16:49:12.936Z",
                "identities": [],
                "can_create_group": True,
                "can_create_project": True,
                "two_factor_enabled": False,
                "external": False,
                "private_profile": None,
                "is_admin": False,
                "highest_role": 50,
                "shared_runners_minutes_limit": None,
                "extra_shared_runners_minutes_limit": None
            }
        ]
