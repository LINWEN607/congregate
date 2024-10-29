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
        return [
            {
                "subjectKind": "user",
                "directoryAlias": "john.doe",
                "domain": "7cfe4c9f-829b-4857-89f9-dfa21e53e1d9",
                "principalName": "john.doe@gitlabpsoutlook.onmicrosoft.com",
                "mailAddress": "john.doe@gitlabpsoutlook.onmicrosoft.com",
                "origin": "aad",
                "originId": "e7bae9bf-aa87-4d3b-a2dd-55e501620050",
                "displayName": "John Doe",
                "_links": {
                    "self": {
                        "href": "https://vssps.dev.azure.com/gitlab-ps/_apis/Graph/Users/aad.ZTlkMzM1NjgtZTZmMi03ZGVhLWI4ZmQtMzA4MzlmYjA2ODhm"
                    },
                    "memberships": {
                        "href": "https://vssps.dev.azure.com/gitlab-ps/_apis/Graph/Memberships/aad.ZTlkMzM1NjgtZTZmMi03ZGVhLWI4ZmQtMzA4MzlmYjA2ODhm"
                    },
                    "membershipState": {
                        "href": "https://vssps.dev.azure.com/gitlab-ps/_apis/Graph/MembershipStates/aad.ZTlkMzM1NjgtZTZmMi03ZGVhLWI4ZmQtMzA4MzlmYjA2ODhm"
                    },
                    "storageKey": {
                        "href": "https://vssps.dev.azure.com/gitlab-ps/_apis/Graph/StorageKeys/aad.ZTlkMzM1NjgtZTZmMi03ZGVhLWI4ZmQtMzA4MzlmYjA2ODhm"
                    },
                    "avatar": {
                        "href": "https://dev.azure.com/gitlab-ps/_apis/GraphProfile/MemberAvatars/aad.ZTlkMzM1NjgtZTZmMi03ZGVhLWI4ZmQtMzA4MzlmYjA2ODhm"
                    }
                },
                "url": "https://vssps.dev.azure.com/gitlab-ps/_apis/Graph/Users/aad.ZTlkMzM1NjgtZTZmMi03ZGVhLWI4ZmQtMzA4MzlmYjA2ODhm",
                "descriptor": "aad.ZTlkMzM1NjgtZTZmMi03ZGVhLWI4ZmQtMzA4MzlmYjA2ODhm"
            },
            {
                "subjectKind": "user",
                "directoryAlias": "paul.van.windmill",
                "domain": "7cfe4c9f-829b-4857-89f9-dfa21e53e1d9",
                "principalName": "paul.van.windmill@gitlabpsoutlook.onmicrosoft.com",
                "mailAddress": "paul.van.windmill@gitlabpsoutlook.onmicrosoft.com",
                "origin": "aad",
                "originId": "1df98d80-d190-4371-ae1c-79d45da1106d",
                "displayName": "Paul van Windmill",
                "_links": {
                    "self": {
                        "href": "https://vssps.dev.azure.com/gitlab-ps/_apis/Graph/Users/aad.OTcwYTMwODktNTZjMC03ZmRiLWI1MDItYzIwZWVjM2Y1ZTM4"
                    },
                    "memberships": {
                        "href": "https://vssps.dev.azure.com/gitlab-ps/_apis/Graph/Memberships/aad.OTcwYTMwODktNTZjMC03ZmRiLWI1MDItYzIwZWVjM2Y1ZTM4"
                    },
                    "membershipState": {
                        "href": "https://vssps.dev.azure.com/gitlab-ps/_apis/Graph/MembershipStates/aad.OTcwYTMwODktNTZjMC03ZmRiLWI1MDItYzIwZWVjM2Y1ZTM4"
                    },
                    "storageKey": {
                        "href": "https://vssps.dev.azure.com/gitlab-ps/_apis/Graph/StorageKeys/aad.OTcwYTMwODktNTZjMC03ZmRiLWI1MDItYzIwZWVjM2Y1ZTM4"
                    },
                    "avatar": {
                        "href": "https://dev.azure.com/gitlab-ps/_apis/GraphProfile/MemberAvatars/aad.OTcwYTMwODktNTZjMC03ZmRiLWI1MDItYzIwZWVjM2Y1ZTM4"
                    }
                },
                "url": "https://vssps.dev.azure.com/gitlab-ps/_apis/Graph/Users/aad.OTcwYTMwODktNTZjMC03ZmRiLWI1MDItYzIwZWVjM2Y1ZTM4",
                "descriptor": "aad.OTcwYTMwODktNTZjMC03ZmRiLWI1MDItYzIwZWVjM2Y1ZTM4"
            },
            {
                "subjectKind": "user",
                "directoryAlias": "adam.bijman",
                "domain": "7cfe4c9f-829b-4857-89f9-dfa21e53e1d9",
                "principalName": "adam.bijman@gitlabpsoutlook.onmicrosoft.com",
                "mailAddress": "adam.bijman@gitlabpsoutlook.onmicrosoft.com",
                "origin": "aad",
                "originId": "b30f8a40-419c-40d4-91ba-dfa19fcc45ec",
                "displayName": "Adam Bijman",
                "_links": {
                    "self": {
                        "href": "https://vssps.dev.azure.com/gitlab-ps/_apis/Graph/Users/aad.NmEwOTg0ZWItYjI4Yy03YjVjLWJjZWItZTMwOTU3ZWQ2YTg4"
                    },
                    "memberships": {
                        "href": "https://vssps.dev.azure.com/gitlab-ps/_apis/Graph/Memberships/aad.NmEwOTg0ZWItYjI4Yy03YjVjLWJjZWItZTMwOTU3ZWQ2YTg4"
                    },
                    "membershipState": {
                        "href": "https://vssps.dev.azure.com/gitlab-ps/_apis/Graph/MembershipStates/aad.NmEwOTg0ZWItYjI4Yy03YjVjLWJjZWItZTMwOTU3ZWQ2YTg4"
                    },
                    "storageKey": {
                        "href": "https://vssps.dev.azure.com/gitlab-ps/_apis/Graph/StorageKeys/aad.NmEwOTg0ZWItYjI4Yy03YjVjLWJjZWItZTMwOTU3ZWQ2YTg4"
                    },
                    "avatar": {
                        "href": "https://dev.azure.com/gitlab-ps/_apis/GraphProfile/MemberAvatars/aad.NmEwOTg0ZWItYjI4Yy03YjVjLWJjZWItZTMwOTU3ZWQ2YTg4"
                    }
                },
                "url": "https://vssps.dev.azure.com/gitlab-ps/_apis/Graph/Users/aad.NmEwOTg0ZWItYjI4Yy03YjVjLWJjZWItZTMwOTU3ZWQ2YTg4",
                "descriptor": "aad.NmEwOTg0ZWItYjI4Yy03YjVjLWJjZWItZTMwOTU3ZWQ2YTg4"
            }
        ]
