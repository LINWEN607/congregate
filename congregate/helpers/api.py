from helpers.logger import myLogger
from math import ceil as math_ceil
from helpers.decorators import stable_retry
import requests

log = myLogger(__name__)


@stable_retry
def generate_get_request(host, token, api, params=None):
    """
        Generates GET request to GitLab API.
        You will need to provide the GL host, access token, and specific api url.
    """
    url = "%s/api/v4/%s" % (host, api)
    headers = {
        'Private-Token': token,
        'Content-Type': 'application/json'
    }

    if params is None:
        params = {}

    return requests.get(url, params=params, headers=headers)


@stable_retry
def generate_post_request(host, token, api, data, headers=None):
    """
        Generates POST request to GitLab API.
        You will need to provide the GL host, access token, specific api url, and any data.
    """
    url = "%s/api/v4/%s" % (host, api)

    if headers is None:
        headers = {
            'Private-Token': token,
            'Content-Type': 'application/json'
        }

    return requests.post(url, data=data, headers=headers)


@stable_retry
def generate_put_request(host, token, api, data, headers=None):
    """
        Generates PUT request to GitLab API.
        You will need to provide the GL host, access token, specific api url, and any data.
    """
    url = "%s/api/v4/%s" % (host, api)
    if headers is None:
        headers = {
            'Private-Token': token,
            'Content-Type': 'application/json'
        }

    return requests.put(url, headers=headers, data=data)


@stable_retry
def generate_delete_request(host, token, api):
    """
        Generates DELETE request to GitLab API.
        You will need to provide the GL host, access token, and specific api url.
    """
    url = "%s/api/v4/%s" % (host, api)
    headers = {
        'Private-Token': token
    }

    return requests.delete(url, headers=headers)


@stable_retry
def get_count(host, token, api):
    """
        Retrieves total count of projects, users, and groups and returns as a long
        You will need to provide the GL host, access token, and specific api url.
    """
    url = "%s/api/v4/%s" % (host, api)

    response = requests.head(url, headers={
        'Private-Token': token,
        'Content-Type': 'application/json'
    })

    if response.headers.get('X-Total', None) is not None:
        return long(response.headers['X-Total'])

    return None


@stable_retry
def get_total_pages(host, token, api):
    '''
    Return total number of pages in API result.
    '''
    url = '%s/api/v4/%s' % (host, api)

    response = requests.head(url, headers={
        'Private-Token': token,
        'Content-Type': 'application/json'
    })

    if response.headers.get('X-Total-Pages', None) is not None:
        return long(response.headers['X-Total-Pages'])

    return None


@stable_retry
def list_all(host, token, api, params=None):
    """
        Returns a list of all projects, groups, users, etc. 
        You will need to provide the GL host, access token, and specific api url.
    """

    count = get_count(host, token, api)

    PER_PAGE = 100
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
            data = generate_get_request(host, token, api, params=params).json()

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
    return generate_get_request(host, token, path, params={'search': search_query}).json()
