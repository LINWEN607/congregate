class MockTeamsApi():

    def get_teams(self):
        return {
                "value": [
                    {
                        "id": "423b774a-a2b1-4f13-81d3-d30a7705d103",
                        "name": "MyShuttle Team",
                        "url": "https://dev.azure.com/gitlab-ps/_apis/projects/ac4f77cb-966f-49ae-b942-13471223719e/teams/423b774a-a2b1-4f13-81d3-d30a7705d103",
                        "description": "The default project team.",
                        "identityUrl": "https://spsprodneu1.vssps.visualstudio.com/A10bdc256-f6d8-4a84-8adf-b4ba24b3ce22/_apis/Identities/423b774a-a2b1-4f13-81d3-d30a7705d103",
                        "projectName": "MyShuttle",
                        "projectId": "ac4f77cb-966f-49ae-b942-13471223719e"
                    },
                    {
                        "id": "96180f59-f197-41a3-9f34-cdbfcf7151e5",
                        "name": "Tailwind Traders Team",
                        "url": "https://dev.azure.com/gitlab-ps/_apis/projects/08285df8-615e-450b-8651-509c072a013e/teams/96180f59-f197-41a3-9f34-cdbfcf7151e5",
                        "description": "The default project team.",
                        "identityUrl": "https://spsprodneu1.vssps.visualstudio.com/A10bdc256-f6d8-4a84-8adf-b4ba24b3ce22/_apis/Identities/96180f59-f197-41a3-9f34-cdbfcf7151e5",
                        "projectName": "Tailwind Traders",
                        "projectId": "08285df8-615e-450b-8651-509c072a013e"
                    },
                    {
                        "id": "3b66f663-9820-4840-9ed9-3904ab5eb5c8",
                        "name": "eShopOnWeb Team",
                        "url": "https://dev.azure.com/gitlab-ps/_apis/projects/fab6c524-9c20-4564-8f38-3a90f188d651/teams/3b66f663-9820-4840-9ed9-3904ab5eb5c8",
                        "description": "The default project team.",
                        "identityUrl": "https://spsprodneu1.vssps.visualstudio.com/A10bdc256-f6d8-4a84-8adf-b4ba24b3ce22/_apis/Identities/3b66f663-9820-4840-9ed9-3904ab5eb5c8",
                        "projectName": "eShopOnWeb",
                        "projectId": "fab6c524-9c20-4564-8f38-3a90f188d651"
                    },
                ],
                "count": 3
            }

    def get_team(self):
        return {
                "value": [
                    {
                        "id": "d1f4fc97-c9c6-4c6f-a772-1a4725390777",
                        "name": "App Development Team",
                        "url": "https://dev.azure.com/gitlab-ps/_apis/projects/fab6c524-9c20-4564-8f38-3a90f188d651/teams/d1f4fc97-c9c6-4c6f-a772-1a4725390777",
                        "description": "",
                        "identityUrl": "https://spsprodneu1.vssps.visualstudio.com/A10bdc256-f6d8-4a84-8adf-b4ba24b3ce22/_apis/Identities/d1f4fc97-c9c6-4c6f-a772-1a4725390777",
                        "projectName": "eShopOnWeb",
                        "projectId": "fab6c524-9c20-4564-8f38-3a90f188d651"
                    },
                    {
                        "id": "623c0500-56e8-4940-84b0-462d1d5d31f3",
                        "name": "DBA Team",
                        "url": "https://dev.azure.com/gitlab-ps/_apis/projects/fab6c524-9c20-4564-8f38-3a90f188d651/teams/623c0500-56e8-4940-84b0-462d1d5d31f3",
                        "description": "",
                        "identityUrl": "https://spsprodneu1.vssps.visualstudio.com/A10bdc256-f6d8-4a84-8adf-b4ba24b3ce22/_apis/Identities/623c0500-56e8-4940-84b0-462d1d5d31f3",
                        "projectName": "eShopOnWeb",
                        "projectId": "fab6c524-9c20-4564-8f38-3a90f188d651"
                    },
                    {
                        "id": "3b66f663-9820-4840-9ed9-3904ab5eb5c8",
                        "name": "eShopOnWeb Team",
                        "url": "https://dev.azure.com/gitlab-ps/_apis/projects/fab6c524-9c20-4564-8f38-3a90f188d651/teams/3b66f663-9820-4840-9ed9-3904ab5eb5c8",
                        "description": "The default project team.",
                        "identityUrl": "https://spsprodneu1.vssps.visualstudio.com/A10bdc256-f6d8-4a84-8adf-b4ba24b3ce22/_apis/Identities/3b66f663-9820-4840-9ed9-3904ab5eb5c8",
                        "projectName": "eShopOnWeb",
                        "projectId": "fab6c524-9c20-4564-8f38-3a90f188d651"
                    }
                ],
                "count": 3
            }

    def get_team_members(self):
        return {
            "value": [
                {
                    "identity": {
                        "displayName": "John Doe",
                        "url": "https://spsprodneu1.vssps.visualstudio.com/A10bdc256-f6d8-4a84-8adf-b4ba24b3ce22/_apis/Identities/e9d33568-e6f2-6dea-b8fd-30839fb0688f",
                        "_links": {
                            "avatar": {
                                "href": "https://dev.azure.com/gitlab-ps/_apis/GraphProfile/MemberAvatars/aad.ZTlkMzM1NjgtZTZmMi03ZGVhLWI4ZmQtMzA4MzlmYjA2ODhm"
                            }
                        },
                        "id": "e9d33568-e6f2-6dea-b8fd-30839fb0688f",
                        "uniqueName": "john.doe@gitlabpsoutlook.onmicrosoft.com",
                        "imageUrl": "https://dev.azure.com/gitlab-ps/_api/_common/identityImage?id=e9d33568-e6f2-6dea-b8fd-30839fb0688f",
                        "descriptor": "aad.ZTlkMzM1NjgtZTZmMi03ZGVhLWI4ZmQtMzA4MzlmYjA2ODhm"
                    }
                },
                {
                    "identity": {
                        "displayName": "Paul van Windmill",
                        "url": "https://spsprodneu1.vssps.visualstudio.com/A10bdc256-f6d8-4a84-8adf-b4ba24b3ce22/_apis/Identities/970a3089-56c0-6fdb-b502-c20eec3f5e38",
                        "_links": {
                            "avatar": {
                                "href": "https://dev.azure.com/gitlab-ps/_apis/GraphProfile/MemberAvatars/aad.OTcwYTMwODktNTZjMC03ZmRiLWI1MDItYzIwZWVjM2Y1ZTM4"
                            }
                        },
                        "id": "970a3089-56c0-6fdb-b502-c20eec3f5e38",
                        "uniqueName": "paul.van.windmill@gitlabpsoutlook.onmicrosoft.com",
                        "imageUrl": "https://dev.azure.com/gitlab-ps/_api/_common/identityImage?id=970a3089-56c0-6fdb-b502-c20eec3f5e38",
                        "descriptor": "aad.OTcwYTMwODktNTZjMC03ZmRiLWI1MDItYzIwZWVjM2Y1ZTM4"
                    }
                },
                {
                    "identity": {
                        "displayName": "Adam Bijman",
                        "url": "https://spsprodneu1.vssps.visualstudio.com/A10bdc256-f6d8-4a84-8adf-b4ba24b3ce22/_apis/Identities/6a0984eb-b28c-6b5c-bceb-e30957ed6a88",
                        "_links": {
                            "avatar": {
                                "href": "https://dev.azure.com/gitlab-ps/_apis/GraphProfile/MemberAvatars/aad.NmEwOTg0ZWItYjI4Yy03YjVjLWJjZWItZTMwOTU3ZWQ2YTg4"
                            }
                        },
                        "id": "6a0984eb-b28c-6b5c-bceb-e30957ed6a88",
                        "uniqueName": "adam.bijman@gitlabpsoutlook.onmicrosoft.com",
                        "imageUrl": "https://dev.azure.com/gitlab-ps/_api/_common/identityImage?id=6a0984eb-b28c-6b5c-bceb-e30957ed6a88",
                        "descriptor": "aad.NmEwOTg0ZWItYjI4Yy03YjVjLWJjZWItZTMwOTU3ZWQ2YTg4"
                    }
                }
            ],
            "count": 3
        }
