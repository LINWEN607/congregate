from time import sleep
import requests

from congregate.helpers.logger import myLogger
from congregate.helpers.audit_logger import audit_logger
from congregate.helpers.decorators import stable_retry

log = myLogger(__name__)
audit = audit_logger(__name__)


def generate_bb_v1_request_url(host, api):
    return "%s/rest/api/1.0/%s" % (host, api)


def generate_v4_request_header(token):
    return {
        'Authorization': 'Basic {}'.format(token),
        'Content-Type': 'application/json'
    }


@stable_retry
def generate_get_request(host, token, api, url=None, params=None):
    """
    Generates GET request to BitBucket API.
    You will need to provide the BB host, access token, and specific api url.

        :param host: (str) BitBucket host URL
        :param token: (str) Access token to BitBucket instance
        :param api: (str) Specific BitBucket API endpoint (ex: projects)
        :param url: (str) A URL to a location not part of the BitBucket API. Defaults to None
        :param params:
        :return: The response object *not* the json() or text()

    """

    if url is None:
        url = generate_bb_v1_request_url(host, api)

    headers = generate_v4_request_header(token)

    if params is None:
        params = {}

    return requests.get(url, params=params, headers=headers)


def list_all(host, token, api, params=None, limit=1000):
    isLastPage = False
    start = 0
    log.info("Listing endpoint: {}".format(api))
    while isLastPage is False:
        if not params:
            params = {
                "start": start,
                "limit": limit
            }
        else:
            params["start"] = start
            params["limit"] = limit
        r = generate_get_request(host, token, api, params=params)
        try:
            data = r.json()
            log.info("Retrieved {0} {1}".format(data.get("size", None), api))
            if r.status_code != 200:
                if r.status_code == 404 or r.status_code == 500:
                    log.error('\nERROR: HTTP Response was {}\n\nBody Text: {}\n'.format(
                        r.status_code, r.text))
                    break
                raise ValueError('ERROR HTTP Response was NOT 200, which implies something wrong. The actual return code was {}\n{}\n'.format(
                    r.status_code, r.text))
            if data.get("values", None) is not None:
                for value in data["values"]:
                    yield value
                isLastPage = data['isLastPage']
                if isLastPage is False:
                    start = data['nextPageStart']
            else:
                isLastPage = True
        except ValueError as e:
            log.error(e)
            log.error("API Request didn't return JSON")
            # Retry interval is smaller here because it will just retry
            # until it succeeds
            log.info("Attempting to retry after 3 seconds")
            sleep(3)
