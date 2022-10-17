class MockGroupsApi():
    @classmethod
    def get_all_groups(cls):
        return [
            {
                "name": "stash-users",
                "deletable": True
            },
            {
                "name": "test-group",
                "deletable": True
            }
        ]

    @classmethod
    def get_all_group_members(cls):
        return [
            {
                "name": "admin",
                "emailAddress": "sysadmin@yourcompany.com",
                "id": 1,
                "displayName": "John Doe",
                "active": True,
                "slug": "admin",
                "type": "NORMAL",
                "directoryName": "Bitbucket Internal Directory",
                "deletable": True,
                "lastAuthenticationTimestamp": 1597232275333,
                "mutableDetails": True,
                "mutableGroups": True,
                "links": {
                    "self": [
                        {
                            "href": "http://192.168.0.191:7990/users/admin"
                        }
                    ]
                }
            },
            {
                "name": "user1",
                "emailAddress": "user1@example.com",
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
                            "href": "http://192.168.0.191:7990/users/user1"
                        }
                    ]
                }
            },
            {
                "name": "user2",
                "emailAddress": "user2@example.com",
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
                            "href": "http://192.168.0.191:7990/users/user2"
                        }
                    ]
                }
            },
            {
                "name": "user3",
                "emailAddress": "user3@example.com",
                "id": 4,
                "displayName": "user3",
                "active": True,
                "slug": "user3",
                "type": "NORMAL",
                "directoryName": "Bitbucket Internal Directory",
                "deletable": True,
                "mutableDetails": True,
                "mutableGroups": True,
                "links": {
                    "self": [
                        {
                            "href": "http://192.168.0.191:7990/users/user3"
                        }
                    ]
                }
            },
            {
                "name": "user4",
                "emailAddress": "user4@example.com",
                "id": 5,
                "displayName": "user4",
                "active": True,
                "slug": "user4",
                "type": "NORMAL",
                "directoryName": "Bitbucket Internal Directory",
                "deletable": True,
                "mutableDetails": True,
                "mutableGroups": True,
                "links": {
                    "self": [
                        {
                            "href": "http://192.168.0.191:7990/users/user4"
                        }
                    ]
                }
            },
            {
                "name": "user5",
                "emailAddress": "user5@example.com",
                "id": 6,
                "displayName": "user5",
                "active": True,
                "slug": "user5",
                "type": "NORMAL",
                "directoryName": "Bitbucket Internal Directory",
                "deletable": True,
                "mutableDetails": True,
                "mutableGroups": True,
                "links": {
                    "self": [
                        {
                            "href": "http://192.168.0.191:7990/users/user5"
                        }
                    ]
                }
            }
        ]
