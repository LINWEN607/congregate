# TODO:
    # 1. Communicate with GHE
    # 2. Import the manage_repos
    # 3. Create an ORG if it doesn't exist
    # 4. Push Repos to the org.
    # 5. Update variables based on existing names

"""
Relevant environment variables:
    GHE_SOURCE_URL : The URL for the GHE source instance. Eg: "https://github.example.net"
    GHE_SOURCE_PASSWORD : Admin password for the GHE source. Only needed if doing token generation via the authorizations endpoint
    GHE_SOURCE_USERNAME : Admin username for the GHE source. Only needed if doing token generation via the authorizations endpoint
    GHE_SOURCE_TOKEN : (Admin) Token for doing auth against the GHE instance
    
    GITLAB_DESTINATION_URL : The URL for the destination GitLab instance. Eg: "http://gitlab.example.com"
    GITLAB_DESTINATION_TOKEN : (Admin) Token for doing auth against the destination GitLab instance

Setting up for local
    You will need a GitLab instance for the GITLAB_DESTINATION_URL and GITLAB_DESTIATION_TOKEN. Use docker-compose, or setup an instance in AWS via Proliferate (AWS_SingleNode_TF_Omnibus works)
    Get your GHE tokens from our https://github.gitlab-proserv.net instance. Login info is in 1Password
    Run this test using the below methods to generate the CONF file
    After that, you should be able to congregate list, etc
    Don't forget to start mongo on your localhost:27017 (via docker run, compose, whatever)
    Don't forget to explicitly set ssl_verify = False, if needed, in the [APP] section of config. There is currently no prompt for this in the config questions.

Notes for making calls:
    GHE authorizations endpoint can only be used with basic auth
        curl -u "$GHE_USERNAME:$GHE_PASSWORD" -X POST -H "Accept: application/vnd.github.v3+json" https://api.github.com/authorizations -d '{"scopes":["read"], "note": "mine"}'
        curl -u "$GHE_USERNAME:$GHE_PASSWORD" -H "Accept: application/vnd.github.v3+json" https://github.gitlab-proserv.net/api/v3/authorizations
    Other calls can be made using tokens:
        curl -H "Accept: application/vnd.github.v3+json" -H "Authorization: token ${GHE_SRC_TOKEN}" https://github.gitlab-proserv.net/api/v3/users/gitlab
    To test this module in isolation, in a poetry shell, run
        poetry run pytest --cov-report html --cov-config=.coveragerc --cov=congregate congregate/tests/migration/github/test_GHE_migration_setup.py
    To see console output, turn off capture by appending a "-s" to the end of the poetry run command
        poetry run pytest --cov-report html --cov-config=.coveragerc --cov=congregate congregate/tests/migration/github/test_GHE_migration_setup.py -s
"""

import mock
import os
import pytest
import unittest
from uuid import uuid4
from base64 import b64encode

from congregate.helpers.misc_utils import input_generator
from congregate.cli import config
from congregate.helpers.seed.generate_token import token_generator
from congregate.helpers.seed.generator import SeedDataGenerator
from congregate.helpers.seed.git import Manage_Repos
from congregate.migration.github.api.orgs import OrgsApi
from congregate.migration.github.api.base import GitHubApi

@pytest.mark.e2e_ghe_setup
class MigrationE2EGHETestSetup(unittest.TestCase):
    def setUp(self):
        self.t = token_generator()        
        self.generate_default_config_with_tokens()

    def generate_default_config_with_tokens(self):
        # Assumption here is pre-baked GHE Ami with admin token already onboard
        ghe_src_token = os.getenv("GHE_SOURCE_TOKEN")
        
        print("Generating Destination Token")
        # destination_token = self.t.generate_token(
        #     "source_token",
        #     "2020-08-27",
        #     url=os.getenv("GITLAB_SRC"),
        #     username="root",
        #     pword="5iveL!fe"
        # )          

        # Can we assume that the container will always be the old system of 5iveL!fe? Current EE containers default to forcing a root password set
        # at first login
        destination_token = os.getenv("GITLAB_DESTINATION_TOKEN", "FAKETOKEN")

        print("Prepping config data")
        values = [
            os.getenv(
                "GITLAB_DESTINATION_URL"
            ),                                      # Destination hostname/url
            # self.t.generate_token("destination_token", "2020-08-27", url=os.getenv("GITLAB_DEST"), username="root", pword=uuid4().hex), # Destination access token
            # "0",                                  # Destination import user id
            "yes",                                  # shared runners enabled
            "no",                                   # append project suffix (retry)
            "3",                                    # max_import_retries,
            "no",                                   # destination parent group
            "_gtest",                               # username suffix
            "no",                                   # mirror
            "yes",                                  # external source?
            "GitHub",                               # Src type
            os.getenv("GHE_SOURCE_URL", os.getenv("GH_TEST_INSTANCE_URL", "HOST_ENV_VAR_NOT_FOUND")),           # source host external_src_url
            "repo_path",                            # Repo path
            "no",                                   # CI Source
            "no",                                   # keep_blocked_users
            "yes",                                  # password reset email
            "no",                                   # randomized password
            "300",                                  # max_export_wait_time
            "yes",                                  # spreadsheet?
            os.getenv("CONGREGATE_PATH", "FAKE_CONGREGATE_PATH") + "/congregate/tests/data/example_wave.csv",   # absolute spreadsheet path                                                    
            "Wave name, Wave date, Source Url, Parent Path",                                                    # spreadsheet columns
            "no"                                    # Use Slack?
        ]
        tokens = [
            destination_token,
            ghe_src_token
        ]

        print("Tokens are: {}", tokens)
        print("Setting generators")
        g = input_generator(values)
        t = input_generator(tokens)
        
        print("Looping on mocks")
        config.ssl_verify = False
        with mock.patch('congregate.cli.config.test_registries', lambda x, y, z: None):
            with mock.patch('builtins.input', lambda x: next(g)):
                with mock.patch('congregate.cli.config.obfuscate', lambda x: b64encode(next(t).encode("ascii")).decode("ascii")):
                    config.generate_config()
   
    def test_to_trigger(self):
        assert True is True

    def generate_admin_ghe_token(self):
        """
        Tossed this in in case we ever *do* need to generate the token
        rather than have it backed into the test VM
        """
        print("Generating Source Token")
        # Only way to call the GHE authorization endpoint is with basic auth
        ghe_host = os.getenv("GHE_SOURCE_URL")
        ghe_username = os.getenv("GHE_SOURCE_USERNAME")
        ghe_password = os.getenv("GHE_SOURCE_PASSWORD")        
        pipeline_id = os.getenv("CI_PIPELINE_ID", os.getenv("HOSTNAME", "NoPipelineOrHost"))
        gh_api = GitHubApi(ghe_host, token=None, api="authorization")                
        
        # TODO: For testing during dev. Leave alone 
        # self.resp = gh_api.generate_v3_basic_auth_get_request(ghe_host, "authorizations", ghe_username, ghe_password)
        # print(self.resp)
        
        # Set scopes for the token we will request. Basically, everything
        scopes = [
            "admin:enterprise",
            "admin:gpg_key",
            "admin:org",
            "admin:org_hook",
            "admin:pre_receive_hook",
            "admin:public_key",
            "admin:repo_hook",
            "delete_repo",
            "gist",
            "notifications",
            "repo",
            "site_admin",
            "user",
            "write:discussion"
        ]
        note = f"For {pipeline_id}"
        
        json_data = {
            "scopes": scopes, 
            "note": note
        }

        self.resp = gh_api.generate_v3_basic_auth_post_request(ghe_host, "authorizations", ghe_username, ghe_password, json_data)
        
        json = self.resp.json()
        if json.keys() and "token" in json.keys():
            return json["token"]
