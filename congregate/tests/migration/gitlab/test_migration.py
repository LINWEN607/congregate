import os
import unittest
from uuid import uuid4

import pytest
import mock
from congregate.helpers.misc_utils import input_generator
from congregate.cli import config
from congregate.helpers.seed.generate_token import token_generator
from congregate.helpers.seed.generator import SeedDataGenerator


@pytest.mark.e2e
class MigrationEndToEndTest(unittest.TestCase):
    def setUp(self):
        self.t = token_generator()
        self.generate_default_config_with_tokens()
        self.s = SeedDataGenerator()

    def test_seed_data(self):
        self.s.generate_seed_data(dry_run=False)

    def generate_default_config_with_tokens(self):
        values = [
            "",  # Migration source
            os.getenv("GITLAB_DEST"),
            self.t.generate_token("destination_token", "2020-08-27", url=os.getenv("GITLAB_DEST"), username="root", pword=uuid4().hex),
            os.getenv("GITLAB_SRC"),
            self.t.generate_token("source_token", "2020-08-27", url=os.getenv("GITLAB_SRC"), username="root", pword=uuid4().hex),
            os.getenv("source_instance_registry"),
            os.getenv("destination_instance_registry"),
            "",  # Parent group id
            "",  # Mirroring yes/no
            "",  # Staging location (default filesystem)
            "",  # Staging location path
            "",     # reset_password
            ""      # force_random_password
        ]

        g = input_generator(values)

        with mock.patch('__builtin__.raw_input', lambda x: next(g)):
            config.config()


