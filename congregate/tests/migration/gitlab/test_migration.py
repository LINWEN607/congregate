import pytest
import mock
import os
from uuid import uuid4
from congregate.helpers.misc_utils import input_generator
from congregate.cli import config
from congregate.helpers.seed import generate_token

@pytest.mark.e2e
def test_gitlab_migration():
    values = [
        "",  # Migration source
        os.getenv("destination_instance_host"),
        os.getenv("destination_instance_token"),
        "http://gitlab_source",
        generate_token.generate_token("source_token", "2020-08-27", url="gitlab_source", username="root", pword=uuid4().hex),
        os.getenv("source_instance_registry"),
        os.getenv("destination_instance_registry"),
        "",  # Parent group id
        "",  # Mirroring yes/no
        "",  # Staging location (default filesystem)
        ""  # Staging location path
    ]
    g = input_generator(values)

    with mock.patch('__builtin__.raw_input', lambda x: next(g)):
        print config.generate_config()

