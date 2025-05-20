
class MockRepositoriesApi():

    def get_single_repository(self):
        return {
                    "repositoryMetadata": {
                        "creationDate": 1429203623.625,
                        "defaultBranch": "main",
                        "repositoryName": "eShopOnWeb",
                        "cloneUrlSsh": "ssh://git-codecommit.us-east-1.amazonaws.com/v1/repos/v1/repos/eShopOnWeb",
                        "lastModifiedDate": 1430783812.0869999,
                        "repositoryDescription": "eShopOnWeb",
                        "cloneUrlHttp": "https://codecommit.us-east-1.amazonaws.com/v1/repos/eShopOnWeb",
                        "repositoryId": "f7579e13-b83e-4027-aaef-650c0EXAMPLE",
                        "Arn": "arn:aws:codecommit:us-east-1:80398EXAMPLE:eShopOnWeb",
                        "accountId": "111111111111"
                    }
               }

    def get_all_repositories(self):
        return {
                    "repositories": [ 
                        {
                            "repositoryName": "eShopOnWeb",
                            "repositoryId": "f7579e13-b83e-4027-aaef-650c0EXAMPLE",
                        }
                    ]
               }