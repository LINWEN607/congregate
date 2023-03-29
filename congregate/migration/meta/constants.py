"""
    Congregate - GitLab instance migration utility

    Copyright (c) 2023 - GitLab
"""

from congregate.migration.meta.ext_ci_class import ExternalCiSourceLookup

EXT_CI_SOURCE_CLASSES = [
    ExternalCiSourceLookup(
        source='jenkins',
        module='congregate.migration.jenkins.base',
        class_name='JenkinsClient'
    ),
    ExternalCiSourceLookup(
        source='teamcity',
        module='congregate.migration.teamcity.base',
        class_name='TeamCityClient'
    )
]
