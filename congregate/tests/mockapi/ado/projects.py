class MockProjectsApi():

    def get_single_project(self):
        return {
            "id": "20671faf-e1bd-4226-8172-0cdf0fdb7128",
            "name": "Azure Bicep Workshop",
            "url": "https://dev.azure.com/gitlab-ps/_apis/projects/20671faf-e1bd-4226-8172-0cdf0fdb7128",
            "state": "wellFormed",
            "revision": 29,
            "visibility": "private",
            "lastUpdateTime": "2024-04-11T21:11:29.787Z",
        }
    
    def get_all_repositories(self):
            return [ 
                {
                    "id": "5febef5a-833d-4e14-b9c0-14cb638f91e6",
                    "name": "AnotherRepository",
                    "url": "https://dev.azure.com/fabrikam/_apis/git/repositories/5febef5a-833d-4e14-b9c0-14cb638f91e6",
                    "sshUrl": "git@dev.azure.com:gitlab-ps/AnotherRepository.git",
                    "project": {
                        "id": "20671faf-e1bd-4226-8172-0cdf0fdb7128",
                        "name": "Azure Bicep Workshop",
                        "url": "https://dev.azure.com/gitlab-ps/_apis/projects/20671faf-e1bd-4226-8172-0cdf0fdb7128",
                        "state": "wellFormed"
                    },
                    "remoteUrl": "https://dev.azure.com/gitlab-ps/_apis/repositories/AnotherRepository"
                }
            ]
