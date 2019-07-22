from congregate.helpers.logger import myLogger
from math import ceil as math_ceil
from congregate.helpers.decorators import stable_retry
import requests

log = myLogger(__name__)


def generate_v4_request_url(host, api):
    return "%s/api/v4/%s" % (host, api)


def generate_v4_request_header(token):
    return {
        'Private-Token': token,
        'Content-Type': 'application/json'
    }


@stable_retry
def generate_get_request(host, token, api, url=None, params=None, stream=False):
    """
    Generates GET request to GitLab API.
    You will need to provide the GL host, access token, and specific api url.

    :param host:
    :param token:
    :param api:
    :param url:
    :param params:
    :param stream:
    :return: The response object *not* the json() or text()
    """

    if url is None:
        url = generate_v4_request_url(host, api)

    headers = generate_v4_request_header(token)

    if params is None:
        params = {}

    response = requests.get(url, params=params, headers=headers)
    return response


@stable_retry
def generate_post_request(host, token, api, data, headers=None):
    """
        Generates POST request to GitLab API.
        You will need to provide the GL host, access token, specific api url, and any data.
    """

    url = generate_v4_request_url(host, api)

    if headers is None:
        headers = generate_v4_request_header(token)

    response = requests.post(url, data=data, headers=headers)
    return response


@stable_retry
def generate_put_request(host, token, api, data, headers=None, files=None):
    """
        Generates PUT request to GitLab API.
        You will need to provide the GL host, access token, specific api url, and any data.
    """
    url = generate_v4_request_url(host, api)
    if headers is None:
        headers = generate_v4_request_header(token)

    return requests.put(url, headers=headers, data=data, files=files)


@stable_retry
def generate_delete_request(host, token, api):
    """
        Generates DELETE request to GitLab API.
        You will need to provide the GL host, access token, and specific api url.
    """
    url = generate_v4_request_url(host, api)
    headers = generate_v4_request_header(token)

    return requests.delete(url, headers=headers)


@stable_retry
def get_count(host, token, api):
    """
        Retrieves total count of projects, users, and groups and returns as a long
        You will need to provide the GL host, access token, and specific api url.
    """
    url = generate_v4_request_url(host, api)

    headers = generate_v4_request_header(token)

    response = requests.head(url, headers=headers)

    if response.headers.get('X-Total', None) is not None:
        return long(response.headers['X-Total'])

    return None


@stable_retry
def get_total_pages(host, token, api):
    """
    Return total number of pages in API result.

    :param host:
    :param token:
    :param api:
    :return:
    """

    url = generate_v4_request_url(host, api)

    headers = generate_v4_request_header(token)

    response = requests.head(url, headers=headers)

    if response.headers.get('X-Total-Pages', None) is not None:
        return long(response.headers['X-Total-Pages'])

    return None


@stable_retry
def list_all(host, token, api, params=None, per_page=100):
    """
        Returns a list of all projects, groups, users, etc. 
        You will need to provide the GL host, access token, and specific api url.
    """

    count = get_count(host, token, api)

    PER_PAGE = per_page
    start_at = 0
    end_at = count

    if count is not None:
        # total_work = end_at - start_at
        # total_pages = total_work / PER_PAGE
        start_page = (start_at / PER_PAGE) + 1  # pages are 1-indexed
        end_page = int(math_ceil(float(end_at) / float(PER_PAGE)))
        current_page = start_page

        while current_page <= end_page:
            log.info("Retrieving %d %s" % (PER_PAGE * current_page, api))

            if params is not None:
                params["page"] = current_page
                params["per_page"] = PER_PAGE
            else:
                params = {
                    "page": current_page,
                    "per_page": PER_PAGE
                }
            data = generate_get_request(host, token, api, params=params)
            
            try:
                data = data.json()
            except ValueError, e:
                log.error(e)
                log.error("API request didn't return JSON")
                break

            for project in data:
                yield project

            if len(data) < PER_PAGE:
                break

            current_page += 1
    else:
        start_page = (start_at / PER_PAGE) + 1  # pages are 1-indexed
        current_page = start_page
        while True:
            log.info("Retrieving %d %s" % (PER_PAGE * current_page, api))

            params = {
                "page": current_page,
                "per_page": PER_PAGE
            }
            data = generate_get_request(host, token, api, params=params).json()

            for project in data:
                yield project

            if len(data) < PER_PAGE:
                break

            current_page += 1


@stable_retry
def search(host, token, path, search_query):
    resp = generate_get_request(host, token, path, params={'search': search_query})
    return resp.json()
