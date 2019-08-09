import unittest
import mock
import json
import responses
from congregate.tests.mockapi.version import MockVersionApi
from congregate.migration.gitlab.version import VersionClient

mock_version = MockVersionApi()
version = VersionClient()

# pylint: disable=no-member
@responses.activate
# pylint: enable=no-member
@mock.patch("congregate.helpers.api.generate_v4_request_url")
def test_is_older_than_true(url):
    url_value = "https://gitlabsource.com/api/v4/version"
    url.return_value = url_value
    # pylint: disable=no-member
    responses.add(responses.GET, url_value,
                  json=mock_version.get_11_10_version(), status=200)
    # pylint: enable=no-member
    source_version = version.get_version(None, None)
    url_value = "https://gitlabdestination.com/api/v4/version"
    url.return_value = url_value
    # pylint: disable=no-member
    responses.add(responses.GET, url_value,
                  json=mock_version.get_12_0_version(), status=200)
    # pylint: enable=no-member
    destination_version = version.get_version(None, None)

    assert version.is_older_than(source_version["version"], destination_version["version"]) == True

# pylint: disable=no-member
@responses.activate
# pylint: enable=no-member
@mock.patch("congregate.helpers.api.generate_v4_request_url")
def test_is_older_than_false(url):
    url_value = "https://gitlabsource.com/api/v4/version"
    url.return_value = url_value
    # pylint: disable=no-member
    responses.add(responses.GET, url_value,
                  json=mock_version.get_12_0_version(), status=200)
    # pylint: enable=no-member
    source_version = version.get_version(None, None)
    print source_version
    url_value = "https://gitlabdestination.com/api/v4/version"
    url.return_value = url_value
    # pylint: disable=no-member
    responses.add(responses.GET, url_value,
                  json=mock_version.get_11_10_version(), status=200)
    # pylint: enable=no-member
    destination_version = version.get_version(None, None)
    print destination_version

    assert version.is_older_than(source_version["version"], destination_version["version"]) == False
