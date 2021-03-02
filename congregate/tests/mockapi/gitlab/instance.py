class MockInstanceApi():
    def get_license(self):
        return {
            "id": 3,
            "plan": "ultimate",
            "created_at": "2020-05-08T16:43:00.599Z",
            "starts_at": "2020-05-06",
            "expires_at": "2021-05-06",
            "historical_max": 47,
            "maximum_user_count": 47,
            "licensee": {
                "Name": "GitLab test license",
                "Email": "test@gitlab.com",
                "Company": "GitLab"
            },
            "add_ons": {},
            "expired": False,
            "overage": 0,
            "user_limit": 200,
            "active_users": 47
        }

    def get_license_403(self):
        return {
            "message": "403 Forbidden"
        }