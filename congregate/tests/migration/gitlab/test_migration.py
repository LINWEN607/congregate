import pytest
import mock
import os
from uuid import uuid4
from congregate.helpers.misc_utils import input_generator
from congregate.cli import config
from congregate.helpers.seed.generate_token import token_generator
# from congregate.helpers.seed.generator import generate_seed_data

t = token_generator()

@pytest.mark.e2e
def test_gitlab_migration():
    print os.getenv("GITLAB_SRC")
    values = [
        "",  # Migration source
        os.getenv("destination_instance_host"),
        os.getenv("destination_instance_token"),
        "http://gitlab_source",
        t.generate_token("source_token", "2020-08-27", url="http://gitlab_source", username="root", pword=uuid4().hex),
        os.getenv("source_instance_registry"),
        os.getenv("destination_instance_registry"),
        "",  # Parent group id
        "",  # Mirroring yes/no
        "",  # Staging location (default filesystem)
        ""  # Staging location path
    ]
    g = input_generator(values)


    with mock.patch('__builtin__.raw_input', lambda x: next(g)):
        # config.update_config(config.generate_config())
        print config.generate_config()

    # generate_seed_data()

