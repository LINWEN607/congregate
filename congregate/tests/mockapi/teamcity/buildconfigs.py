from collections import OrderedDict


class TeamcityJobsApi():
    def get_job_config_dict(self):
        return {
            OrderedDict(
                [
                    (
                        'buildTypes',
                        OrderedDict(
                            [
                                (
                                    '@count',
                                    '4'
                                ),
                                (
                                    '@href',
                                    '/app/rest/buildTypes'
                                ),
                                (
                                    'buildType',
                                    [
                                        OrderedDict(
                                            [
                                                (
                                                    '@id',
                                                    'TestProject1_BuildConfig1'
                                                ),
                                                (
                                                    '@name',
                                                    'Build Config 1'
                                                ),
                                                (
                                                    '@description',
                                                    'Add a single, unmasked build parameter to one job'
                                                ),
                                                (
                                                    '@projectName',
                                                    'Test Project 1'
                                                ),
                                                (
                                                    '@projectId',
                                                    'TestProject1'
                                                ),
                                                (
                                                    '@href',
                                                    '/app/rest/buildTypes/id:TestProject1_BuildConfig1'
                                                ),
                                                (
                                                    '@webUrl',
                                                    'http://13.92.25.192/viewType.html?buildTypeId=TestProject1_BuildConfig1'
                                                )
                                            ]
                                        ),
                                        OrderedDict(
                                            [
                                                (
                                                    '@id',
                                                    'TestProject1_BuildConfig2'
                                                ),
                                                (
                                                    '@name',
                                                    'Build Config 2'
                                                ),
                                                (
                                                    '@description',
                                                    'Add a single, masked build parameter the second job'
                                                ),
                                                (
                                                    '@projectName',
                                                    'Test Project 1'
                                                ),
                                                (
                                                    '@projectId',
                                                    'TestProject1'
                                                ),
                                                (
                                                    '@href',
                                                    '/app/rest/buildTypes/id:TestProject1_BuildConfig2'
                                                ),
                                                (
                                                    '@webUrl',
                                                    'http://13.92.25.192/viewType.html?buildTypeId=TestProject1_BuildConfig2'
                                                )
                                            ]
                                        ),
                                        OrderedDict(
                                            [
                                                (
                                                    '@id',
                                                    'TestProject1_BuildConfig3'
                                                ),
                                                (
                                                    '@name',
                                                    'Build Config 3'
                                                ),
                                                (
                                                    '@description',
                                                    'Add mulitple build parameters (both masked and unmasked to the third job'
                                                ),
                                                (
                                                    '@projectName',
                                                    'Test Project 1'
                                                ),
                                                (
                                                    '@projectId',
                                                    'TestProject1'
                                                ),
                                                (
                                                    '@href',
                                                    '/app/rest/buildTypes/id:TestProject1_BuildConfig3'
                                                ),
                                                (
                                                    '@webUrl',
                                                    'http://13.92.25.192/viewType.html?buildTypeId=TestProject1_BuildConfig3'
                                                )
                                            ]
                                        ),
                                        OrderedDict(
                                            [
                                                (
                                                    '@id',
                                                    'SliaquatTestGithubTeamcityIntegration_ShlBuildConfi'
                                                ),
                                                (
                                                    '@name',
                                                    'SHL Build Confi'
                                                ),
                                                (
                                                    '@projectName',
                                                    'sliaquat - Test Github Teamcity Integration'
                                                ),
                                                (
                                                    '@projectId',
                                                    'SliaquatTestGithubTeamcityIntegration'
                                                ),
                                                (
                                                    '@href',
                                                    '/app/rest/buildTypes/id:SliaquatTestGithubTeamcityIntegration_ShlBuildConfi'
                                                ),
                                                (
                                                    '@webUrl',
                                                    'http://13.92.25.192/viewType.html?buildTypeId=SliaquatTestGithubTeamcityIntegration_ShlBuildConfi'
                                                )
                                            ]
                                        )
                                    ]
                                )
                            ]
                        )
                    )
                ]
            )
        }
