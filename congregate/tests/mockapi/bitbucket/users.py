class MockUsersApi():
    def get_all_users(self):
        return [
            {
                "name": "admin",
                "emailAddress": "SYsadmin@yourcompany.com",
                "id": 1,
                "displayName": "John Doe",
                "active": True,
                "slug": "admin",
                "type": "NORMAL",
                "directoryName": "Bitbucket Internal Directory",
                "deletable": True,
                "lastAuthenticationTimestamp": 1592567259410,
                "mutableDetails": True,
                "mutableGroups": True,
                "links": {
                    "self": [
                        {
                            "href": "http://localhost:7990/users/admin"
                        }
                    ]
                }
            },
            {
                "name": "user1",
                "emailAddress": "USer1@example.com",
                "id": 2,
                "displayName": "user1",
                "active": True,
                "slug": "user1",
                "type": "NORMAL",
                "directoryName": "Bitbucket Internal Directory",
                "deletable": True,
                "mutableDetails": True,
                "mutableGroups": True,
                "links": {
                    "self": [
                        {
                            "href": "http://localhost:7990/users/user1"
                        }
                    ]
                }
            },
            {
                "name": "user2",
                "emailAddress": "USer2@example.com",
                "id": 3,
                "displayName": "user2",
                "active": True,
                "slug": "user2",
                "type": "NORMAL",
                "directoryName": "Bitbucket Internal Directory",
                "deletable": True,
                "mutableDetails": True,
                "mutableGroups": True,
                "links": {
                    "self": [
                        {
                            "href": "http://localhost:7990/users/user2"
                        }
                    ]
                }
            }
        ]

    def get_sys_admin_user(self):
        return {
            "size": 1,
            "limit": 25,
            "isLastPage": True,
            "values": [
                {
                    "user": {
                        "name": "admin",
                        "emailAddress": "sysadmin@yourcompany.com",
                        "id": 1,
                        "displayName": "John Doe",
                        "active": True,
                        "slug": "admin",
                        "type": "NORMAL",
                        "links": {
                            "self": [
                                {
                                    "href": "http://localhost:7990/users/admin"
                                }
                            ]
                        }
                    },
                    "permission": "SYS_ADMIN"
                }
            ],
            "start": 0
        }

    def get_user_group(self):
        return {
            "size": 1,
            "limit": 25,
            "isLastPage": True,
            "values": [
                {
                    "name": "admin-group",
                    "deletable": True
                }
            ],
            "start": 0
        }

    def get_admin_group(self):
        return {
            "size": 1,
            "limit": 25,
            "isLastPage": True,
            "values": [
                {
                    "group": {
                        "name": "admin-group"
                    },
                    "permission": "ADMIN"
                }
            ],
            "start": 0
        }

    def get_non_admin_user(self):
        return {
            "size": 1,
            "limit": 25,
            "isLastPage": True,
            "values": [
                {
                    "user": {
                        "name": "test",
                        "emailAddress": "test@tester.com",
                        "id": 52,
                        "displayName": "tester",
                        "active": True,
                        "slug": "test",
                        "type": "NORMAL",
                        "links": {
                            "self": [
                                {
                                    "href": "http://localhost:7990/users/test"
                                }
                            ]
                        }
                    },
                    "permission": "PROJECT_CREATE"
                }
            ],
            "start": 0
        }

    def get_user_invalid(self):
        return {
            "size": 0,
            "limit": 25,
            "isLastPage": True,
            "values": [],
            "start": 0
        }

    def get_user_401(self):
        return {
            "errors": [
                {
                    "context": None,
                    "message": "You are not permitted to access this resource",
                    "exceptionName": "com.atlassian.bitbucket.AuthorisationException"
                }
            ]
        }
