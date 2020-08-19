class MockReposApi():
    def get_all_repos(self):
        return [
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
            },
            {
                "slug": "another-test-repo",
                "id": 13,
                "name": "Another-Test-Repo",
                "description": "Just another test repo",
                "hierarchyId": "ad0c01c46b70e551c1af",
                "scmId": "git",
                "state": "AVAILABLE",
                "statusMessage": "Available",
                "forkable": True,
                "project": {
                    "key": "ATP",
                    "id": 22,
                    "name": "Another-Test-Project",
                    "description": "Just a another random test project",
                    "public": False,
                    "type": "NORMAL",
                    "links": {
                        "self": [
                            {
                                "href": "http://localhost:7990/projects/ATP"
                            }
                        ]
                    }
                },
                "public": False,
                "links": {
                    "clone": [
                        {
                            "href": "http://localhost:7990/scm/atp/another-test-repo.git",
                            "name": "http"
                        },
                        {
                            "href": "ssh://git@localhost:7999/atp/another-test-repo.git",
                            "name": "ssh"
                        }
                    ],
                    "self": [
                        {
                            "href": "http://localhost:7990/projects/ATP/repos/another-test-repo/browse"
                        }
                    ]
                }
            }
        ]

    def get_all_repo_users(self):
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
                "permission": "REPO_READ"
            },
            {
                "user": {
                    "name": "user4",
                    "emailAddress": "user4@example.com",
                    "id": 5,
                    "displayName": "user4",
                    "active": True,
                    "slug": "user4",
                    "type": "NORMAL",
                    "links": {
                        "self": [
                            {
                                "href": "http://localhost:7990/users/user4"
                            }
                        ]
                    }
                },
                "permission": "REPO_READ"
            }
        ]

    def get_all_repo_groups(self):
        return [
            {
                "group": {
                    "name": "stash-users"
                },
                "permission": "REPO_READ"
            },
            {
                "group": {
                    "name": "test-group"
                },
                "permission": "REPO_READ"
            }
        ]