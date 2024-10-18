class MockUsersApi():

    def get_connection_data(self):
        return {
        "authenticatedUser": {
            "id": "ad7ddcd2-0562-665d-84ce-f024d9266741",
            "descriptor": "Microsoft.IdentityModel.Claims.ClaimsIdentity;7cfe4c9f-829b-4857-89f9-dfa21e53e1d9\\john.doe@example.com",
            "subjectDescriptor": "aad.YWQ3ZGRjZDItMDU2Mi03NjVkLTg0Y2UtZjAyNGQ5MjY2NzQx",
            "providerDisplayName": "John Doe",
            "isActive": True,
            "properties": {
                "Account": {
                    "$type": "System.String",
                    "$value": "john.doe@example.com"
                }
            },
            "resourceVersion": 2,
            "metaTypeId": 0
        },
        "authorizedUser": {
            "id": "ad7ddcd2-0562-665d-84ce-f024d9266741",
            "descriptor": "Microsoft.IdentityModel.Claims.ClaimsIdentity;7cfe4c9f-829b-4857-89f9-dfa21e53e1d9\\john.doe@example.com",
            "subjectDescriptor": "aad.YWQ3ZGRjZDItMDU2Mi03NjVkLTg0Y2UtZjAyNGQ5MjY2NzQx",
            "providerDisplayName": "John Doe",
            "isActive": True,
            "properties": {
                "Account": {
                    "$type": "System.String",
                    "$value": "john.doe@example.com"
                }
            },
            "resourceVersion": 2,
            "metaTypeId": 0
        },
        "instanceId": "62d5db69-917f-405d-973d-fc20e7ecd3de",
        "deploymentId": "1f18445b-609a-73c1-2ae2-521b74b4c11d",
        "deploymentType": "hosted",
        "locationServiceData": {
            "serviceOwner": "00025394-6065-48ca-87d9-7f5672854ef7",
            "defaultAccessMappingMoniker": "PublicAccessMapping",
            "lastChangeId": 62693399,
            "lastChangeId64": 62693399
        }}

    def get_all_users(self):
        return {
            "count": 2,
            "value": [
                {
                    "subjectKind": "user",
                    "metaType": "member",
                    "directoryAlias": "gitlab-ps_outlook.com#EXT#",
                    "domain": "7cfe4c9f-829b-4857-89f9-dfa21e53e1d9",
                    "principalName": "gitlab-ps@outlook.com",
                    "mailAddress": "gitlab-ps@outlook.com",
                    "origin": "aad",
                    "originId": "4be0943c-7844-411c-8e0c-ebb447215f67",
                    "displayName": "GitLab PS",
                    "_links": {
                        "self": {
                            "href": "https://vssps.dev.azure.com/gitlab-ps/_apis/Graph/Users/aad.NzE0YzVlNTItMmU1OC03ODgwLWEzMGQtMmZiYjE2ODdjZTk1"
                        },
                        "memberships": {
                            "href": "https://vssps.dev.azure.com/gitlab-ps/_apis/Graph/Memberships/aad.NzE0YzVlNTItMmU1OC03ODgwLWEzMGQtMmZiYjE2ODdjZTk1"
                        },
                        "membershipState": {
                            "href": "https://vssps.dev.azure.com/gitlab-ps/_apis/Graph/MembershipStates/aad.NzE0YzVlNTItMmU1OC03ODgwLWEzMGQtMmZiYjE2ODdjZTk1"
                        },
                        "storageKey": {
                            "href": "https://vssps.dev.azure.com/gitlab-ps/_apis/Graph/StorageKeys/aad.NzE0YzVlNTItMmU1OC03ODgwLWEzMGQtMmZiYjE2ODdjZTk1"
                        },
                        "avatar": {
                            "href": "https://dev.azure.com/gitlab-ps/_apis/GraphProfile/MemberAvatars/aad.NzE0YzVlNTItMmU1OC03ODgwLWEzMGQtMmZiYjE2ODdjZTk1"
                        }
                    },
                    "url": "https://vssps.dev.azure.com/gitlab-ps/_apis/Graph/Users/aad.NzE0YzVlNTItMmU1OC03ODgwLWEzMGQtMmZiYjE2ODdjZTk1",
                    "descriptor": "aad.NzE0YzVlNTItMmU1OC03ODgwLWEzMGQtMmZiYjE2ODdjZTk1"
                },
                {
                    "subjectKind": "user",
                    "metaType": "member",
                    "directoryAlias": "john_doe.com#EXT#",
                    "domain": "7cfe4c9f-829b-4857-89f9-dfa21e53e1d9",
                    "principalName": "jdoe@gitlab.com",
                    "mailAddress": "jdoe@gitlab.com",
                    "origin": "aad",
                    "originId": "51c27999-1fc7-4736-a31f-228209162a8d",
                    "displayName": "John V. Doe",
                    "_links": {
                        "self": {
                            "href": "https://vssps.dev.azure.com/gitlab-ps/_apis/Graph/Users/aad.YWQ3ZGRjZDItMDU2Mi03NjVkLTg0Y2UtZjAyNGQ5MjY2NzQx"
                        },
                        "memberships": {
                            "href": "https://vssps.dev.azure.com/gitlab-ps/_apis/Graph/Memberships/aad.YWQ3ZGRjZDItMDU2Mi03NjVkLTg0Y2UtZjAyNGQ5MjY2NzQx"
                        },
                        "membershipState": {
                            "href": "https://vssps.dev.azure.com/gitlab-ps/_apis/Graph/MembershipStates/aad.YWQ3ZGRjZDItMDU2Mi03NjVkLTg0Y2UtZjAyNGQ5MjY2NzQx"
                        },
                        "storageKey": {
                            "href": "https://vssps.dev.azure.com/gitlab-ps/_apis/Graph/StorageKeys/aad.YWQ3ZGRjZDItMDU2Mi03NjVkLTg0Y2UtZjAyNGQ5MjY2NzQx"
                        },
                        "avatar": {
                            "href": "https://dev.azure.com/gitlab-ps/_apis/GraphProfile/MemberAvatars/aad.YWQ3ZGRjZDItMDU2Mi03NjVkLTg0Y2UtZjAyNGQ5MjY2NzQx"
                        }
                    },
                    "url": "https://vssps.dev.azure.com/gitlab-ps/_apis/Graph/Users/aad.YWQ3ZGRjZDItMDU2Mi03NjVkLTg0Y2UtZjAyNGQ5MjY2NzQx",
                    "descriptor": "aad.YWQ3ZGRjZDItMDU2Mi03NjVkLTg0Y2UtZjAyNGQ5MjY2NzQx"
                }
            ]
        }