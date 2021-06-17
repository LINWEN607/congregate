class MockProjectsApi():
    def get_all_projects(self):
        return [
            {
                "key": "TGP",
                "id": 1,
                "name": "test-group",
                "description": "test",
                "public": False,
                "type": "NORMAL",
                "links": {
                    "self": [
                        {
                            "href": "http://localhost:7990/projects/TGP"
                        }
                    ]
                }
            },
            {
                "key": "ATP",
                "id": 2,
                "name": "another-test-group",
                "description": "test",
                "public": False,
                "type": "NORMAL",
                "links": {
                    "self": [
                        {
                            "href": "http://localhost:7990/projects/ATP"
                        }
                    ]
                }
            }
        ]

    def get_all_project_repos(self):
        return [
            {
                "slug": "node",
                "id": 3,
                "name": "node",
                "hierarchyId": "2f6a47e5575f1a97a76d",
                "scmId": "git",
                "state": "AVAILABLE",
                "statusMessage": "Available",
                "forkable": True,
                "project": {
                    "key": "TGP",
                    "id": 1,
                    "name": "test-group",
                    "description": "test",
                    "public": "false",
                    "type": "NORMAL",
                    "links": {
                        "self": [
                            {
                                "href": "http://localhost:7990/projects/TGP"
                            }
                        ]
                    }
                },
                "public": False,
                "links": {
                    "clone": [
                        {
                            "href": "http://localhost:7990/scm/tgp/node.git",
                            "name": "http"
                        },
                        {
                            "href": "ssh://git@localhost:7999/tgp/node.git",
                            "name": "ssh"
                        }
                    ],
                    "self": [
                        {
                            "href": "http://localhost:7990/projects/TGP/repos/node/browse"
                        }
                    ]
                }
            },
            {
                "slug": "android",
                "id": 6,
                "name": "android",
                "hierarchyId": "fc1fa95eae6089bd9987",
                "scmId": "git",
                "state": "AVAILABLE",
                "statusMessage": "Available",
                "forkable": True,
                "project": {
                    "key": "TGP",
                    "id": 1,
                    "name": "test-group",
                    "description": "test",
                    "public": False,
                    "type": "NORMAL",
                    "links": {
                        "self": [
                            {
                                "href": "http://localhost:7990/projects/TGP"
                            }
                        ]
                    }
                },
                "public": False,
                "description": "Android project",
                "links": {
                    "clone": [
                        {
                            "href": "http://localhost:7990/scm/tgp/android.git",
                            "name": "http"
                        },
                        {
                            "href": "ssh://git@localhost:7999/tgp/android.git",
                            "name": "ssh"
                        }
                    ],
                    "self": [
                        {
                            "href": "http://localhost:7990/projects/TGP/repos/android/browse"
                        }
                    ]
                }
            }
        ]

    def get_all_project_users(self):
        return [
            {
                "user": {
                    "name": "user2",
                    "emailAddress": "user2@example.com",
                    "id": 3,
                    "displayName": "user2",
                    "active": True,
                    "slug": "user2",
                    "type": "NORMAL",
                    "links": {
                        "self": [
                            {
                                "href": "http://localhost:7990/users/user2"
                            }
                        ]
                    }
                },
                "permission": "PROJECT_READ"
            },
            {
                "user": {
                    "name": "user1",
                    "emailAddress": "user1@example.com",
                    "id": 1,
                    "displayName": "user1",
                    "active": True,
                    "slug": "user1",
                    "type": "NORMAL",
                    "links": {
                        "self": [
                            {
                                "href": "http://localhost:7990/users/user1"
                            }
                        ]
                    }
                },
                "permission": "PROJECT_READ"
            }
        ]

    def get_all_project_groups(self):
        return [
            {
                "group": {
                    "name": "stash-users"
                },
                "permission": "PROJECT_READ"
            },
            {
                "group": {
                    "name": "test-group"
                },
                "permission": "PROJECT_WRITE"
            }
        ]
