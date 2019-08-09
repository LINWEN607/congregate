class MockUsersApi():
    '''
        Simulates a /users request with no additional parameters
    '''

    def get_current_user(self):
        return {
            "id": 1,
            "username": "root",
            "name": "John Smith",
            "state": "active",
            "avatar_url": "http://localhost:3000/uploads/user/avatar/1/cd8.jpeg",
            "web_url": "http://localhost:3000/john_smith"
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
                "web_url": "http://localhost:3000/john_smith"
            },
            {
                "id": 2,
                "username": "jack_smith",
                "name": "Jack Smith",
                "state": "blocked",
                "avatar_url": "http://gravatar.com/../e32131cd8.jpeg",
                "web_url": "http://localhost:3000/jack_smith"
            }
        ]
        yield users

    def get_all_users_list(self):
        return [
            {
                "id": 1,
                "username": "raymond_smith",
                "name": "Raymond Smith",
                "state": "active",
                "avatar_url": "https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon",
                "web_url": "http://192.168.1.8:3000/root",
                "expires_at": "2012-10-22T14:13:35Z",
                "access_level": 30
            },
            {
                "id": 2,
                "username": "john_doe",
                "name": "John Doe",
                "state": "active",
                "avatar_url": "https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon",
                "web_url": "http://192.168.1.8:3000/root",
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
                "id": 1,
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

    def get_dummy_new_users(self):
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