from congregate.tests.mockapi.gitlab.environments import MockEnvironmentsApi
from congregate.migration.gitlab.environments import EnvironmentsClient

mock_environment = MockEnvironmentsApi()
environment = EnvironmentsClient()


def test_generate_environment_data():
    expected = {
        "name": "review/fix-foo",
        "external_url": "https://review-fix-foo-dfjre3.example.gitlab.com",
    }
    envs = list(mock_environment.get_all_environments_generator())
    actual = environment.generate_environment_data(envs[0][0])

    assert expected == actual
