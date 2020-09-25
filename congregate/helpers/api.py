from math import ceil as math_ceil
from time import sleep
from re import findall
import requests

from congregate.helpers.logger import myLogger
from congregate.helpers.audit_logger import audit_logger
from congregate.helpers.decorators import stable_retry
from congregate.helpers.misc_utils import generate_audit_log_message
from congregate.helpers.conf import Config

log = myLogger(__name__)
audit = audit_logger(__name__)
config = Config()

def generate_v4_request_url(host, api):
    return "%s/api/v4/%s" % (host, api)

def generate_graphql_request_url(host):
    return f"{host}/api/graphql"

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

        :param host: (str) GitLab host URL
        :param token: (str) Access token to GitLab instance
        :param api: (str) Specific GitLab API endpoint (ex: projects)
        :param url: (str) A URL to a location not part of the GitLab API. Defaults to None
        :param params:
        :return: The response object *not* the json() or text()

    """

    if url is None:
        url = generate_v4_request_url(host, api)

    headers = generate_v4_request_header(token)

    if params is None:
        params = {}

    return requests.get(url, params=params, headers=headers, verify=config.ssl_verify)


@stable_retry
def generate_post_request(host, token, api, data, graphql_query=False, headers=None, files=None, description=None):
    """
        Generates POST request to GitLab API.

        :param host: (str) GitLab host URL
        :param token: (str) Access token to GitLab instance
        :param api: (str) Specific GitLab API endpoint (ex: projects)
        :param data: (dict) Any data required for the API request

        :kwarg graphql_query: (bool) Sets the URL to use the GraphQL endpoint. Default False
        :kwarg headers: (dict) Any headers to be passed into the request. Default None
        :kwarg files: (dict) Any file content to be passed into the request. Default None
        :kwarg description: (str) A custom description message for the audit log. Default None

        :return: request object containing response
    """
    if graphql_query:
        url = generate_graphql_request_url(host)
    else:
        url = generate_v4_request_url(host, api)
    audit.info(generate_audit_log_message("POST", description, url))
    if headers is None:
        headers = generate_v4_request_header(token)

    return requests.post(url, data=data, headers=headers, files=files, verify=config.ssl_verify)


@stable_retry
def generate_put_request(host, token, api, data, headers=None, files=None, description=None):
    """
        Generates PUT request to GitLab API.

        :param host: (str) GitLab host URL
        :param token: (str) Access token to GitLab instance
        :param api: (str) Specific GitLab API endpoint (ex: projects)
        :param data: (dict) Any data required for the API request

        :return: request object containing response
    """
    url = generate_v4_request_url(host, api)
    audit.info(generate_audit_log_message("PUT", description, url))
    if headers is None:
        headers = generate_v4_request_header(token)

    return requests.put(url, headers=headers, data=data, files=files, verify=config.ssl_verify)


@stable_retry
def generate_delete_request(host, token, api, description=None):
    """
        Generates DELETE request to GitLab API.

        :param host: (str) GitLab host URL
        :param token: (str) Access token to GitLab instance
        :param api: (str) Specific GitLab API endpoint (ex: user/1234)

        :return: request object containing response
    """
    url = generate_v4_request_url(host, api)
    audit.info(generate_audit_log_message("DELETE", description, url))
    headers = generate_v4_request_header(token)

    return requests.delete(url, headers=headers, verify=config.ssl_verify)


@stable_retry
def get_count(host, token, api):
    """
        Retrieves total count of projects, users, and groups

        :param host: (str) GitLab host URL
        :param token: (str) Access token to GitLab instance
        :param api: (str) Specific GitLab API endpoint (ex: users)

        :return: long containing the data from the 'X-Total' header in the response OR None if the header doesn't exist in the response
    """
    url = generate_v4_request_url(host, api)

    response = requests.head(url, headers=generate_v4_request_header(token), verify=config.ssl_verify)

    if response.headers.get('X-Total', None) is not None:
        return int(response.headers['X-Total'])

    return None


@stable_retry
def get_total_pages(host, token, api):
    """
        Get total number of pages in API result

        :param host: (str) GitLab host URL
        :param token: (str) Access token to GitLab instance
        :param api: (str) Specific GitLab API endpoint (ex: users)

        :return: long containing the data from the 'X-Total-Pages' header in the response OR None if the header doesn't exist in the response
    """
    url = generate_v4_request_url(host, api)

    response = requests.head(url, headers=generate_v4_request_header(token), verify=config.ssl_verify)

    if response.headers.get('X-Total-Pages', None) is not None:
        return int(response.headers['X-Total-Pages'])

    return None


@stable_retry
def list_all(host, token, api, params=None, per_page=100, keyset=False):
    """
        Generates a list of all projects, groups, users, etc.

        :param host: (str) GitLab host URL
        :param token: (str) Access token to GitLab instance
        :param api: (str) Specific GitLab API endpoint (ex: users)
        :param api: (str) Specific GitLab API endpoint (ex: users)
        :param per_page: (int) Total results per request. Defaults to 100

        :yields: Individual objects from the presumed array of data
    """

    count = get_count(host, token, api)
    log.info("Total count for endpoint {0}: {1}".format(api, count))

    PER_PAGE = per_page
    start_at = 0
    end_at = count
    last_id = 0

    if count is not None:
        # total_work = end_at - start_at
        # total_pages = total_work / PER_PAGE
        start_page = (start_at / PER_PAGE) + 1  # pages are 1-indexed
        end_page = int(math_ceil(float(end_at) / float(PER_PAGE)))
        current_page = int(start_page)
        retried = False
        while current_page <= end_page:
            data = generate_get_request(host, token, api, params=get_params(
                params, PER_PAGE, current_page, keyset, last_id))
            try:
                log.info("Retrieved {0} {1}".format(
                    PER_PAGE * (current_page - 1) + len(data.json()), api))
                if keyset:
                    last_id = get_last_id(data.headers.get("Link", None))
                    if last_id is None:
                        break
                data = data.json()
                for project in data:
                    yield project
                if len(data) < PER_PAGE:
                    break
                current_page += 1
                retried = False
            except ValueError as e:
                log.error(e)
                log.error("API request didn't return JSON")
                log.info("Attempting to retry after 10 seconds")
                sleep(10)
                # Failure will only be retried once
                retried = True
            if retried:
                break
    else:
        start_page = (start_at / PER_PAGE) + 1  # pages are 1-indexed
        current_page = int(start_page)
        while True:
            data = generate_get_request(
                host, token, api, params=get_params(
                    params, PER_PAGE, current_page, keyset, last_id))
            try:
                log.info("Retrieved {0} {1}".format(
                    PER_PAGE * (current_page - 1) + len(data.json()), api))
                if keyset:
                    last_id = get_last_id(data.headers.get("Link", None))
                    if last_id is None:
                        break
                data = data.json()
                for project in data:
                    yield project
                if len(data) < PER_PAGE:
                    break
                current_page += 1
            except ValueError as e:
                log.error(e)
                log.error("API Request didn't return JSON")
                # Retry interval is smaller here because it will just retry
                # until it succeeds
                log.info("Attempting to retry after 3 seconds")
                sleep(3)


@stable_retry
def search(host, token, api, search_query):
    """
        Get total number of pages in API result

        :param host: (str) GitLab host URL
        :param token: (str) Access token to GitLab instance
        :param api: (str) Specific GitLab API endpoint (ex: users)
        :search_query: (str) Specific query to search

        :return: JSON object containing the request response
    """
    return generate_get_request(host, token, api, params={
                                'search': search_query}).json()


def get_params(params, per_page, current_page, keyset, last_id):
    if params:
        params["page"] = current_page
        params["per_page"] = per_page
    else:
        params = {
            "pagination": "keyset",
            "per_page": per_page,
            "order_by": "id",
            "sort": "asc",
            "id_after": last_id
        } if keyset else {
            "page": current_page,
            "per_page": per_page
        }
    return params


# Project only keyset-based pagination - https://docs.gitlab.com/ee/api/#keyset-based-pagination
def get_last_id(link):
    # Get id_after value. If the Link key is missing it's done, with an empty list response
    return findall(r"id_after=(.+?)&", link)[0] if link else None
