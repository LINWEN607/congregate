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

    def get_admin_user(self):
        return {
            "name": "admin",
            "emailAddress": "SYsadmin@yourcompany.com",
            "id": 1,
            "displayName": "John Doe",
            "active": True,
            "slug": "admin",
            "type": "ADMINISTRATOR",
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
        }

    def get_non_admin_user(self):
        return {
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
        }

    def get_user_404(self):
        return {
            "message": "404 User Not Found"
        }
