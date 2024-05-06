class MockProjectFeatureFlagApi():
    def get_all_project_feature_flags(self):
        return [
            {
                "name":"merge_train",
                "description":"This feature is about merge train",
                "active": True,
                "version": "new_version_flag",
                "created_at":"2019-11-04T08:13:51.423Z",
                "updated_at":"2019-11-04T08:13:51.423Z",
                "scopes":[],
                "strategies": [
                    {
                        "id": 1,
                        "name": "userWithId",
                        "parameters": {
                            "userIds": "user1"
                        },
                        "scopes": [
                            {
                            "id": 1,
                            "environment_scope": "production"
                            }
                        ],
                        "user_list": None
                    }
                ]
            },
            {
                "name":"new_live_trace",
                "description":"This is a new live trace feature",
                "active": True,
                "version": "new_version_flag",
                "created_at":"2019-11-04T08:13:10.507Z",
                "updated_at":"2019-11-04T08:13:10.507Z",
                "scopes":[],
                "strategies": [
                    {
                        "id": 2,
                        "name": "default",
                        "parameters": {},
                        "scopes": [
                            {
                            "id": 2,
                            "environment_scope": "staging"
                            }
                        ],
                        "user_list": None
                    }
                ]
            },
            {
                "name":"user_list",
                "description":"This feature is about user list",
                "active": True,
                "version": "new_version_flag",
                "created_at":"2019-11-04T08:13:10.507Z",
                "updated_at":"2019-11-04T08:13:10.507Z",
                "scopes":[],
                "strategies": [
                    {
                        "id": 2,
                        "name": "gitlabUserList",
                        "parameters": {},
                        "scopes": [
                            {
                            "id": 2,
                            "environment_scope": "staging"
                            }
                        ],
                        "user_list": {
                            "id": 1,
                            "iid": 1,
                            "name": "My user list",
                            "user_xids": "user1,user2,user3"
                        }
                    }
                ]
            }
        ]
