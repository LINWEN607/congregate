from helpers import logger
from math import ceil as math_ceil
import requests

l = logger.congregate_logger(__name__)


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
    
    return  requests.post(url, data=data, headers=headers)


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

    return long(response.headers['X-Total'])


def get_total_pages(host, token, api):
    '''
    Return total number of pages in API result.
    '''
    url = '%s/api/v4/%s' % (host, api)

    response = requests.head(url, headers={
        'Private-Token': token,
        'Content-Type': 'application/json'
    })

    return long(response.headers['X-Total-Pages'])


def list_all(host, token, api):
    """
        Returns a list of all projects, groups, users, etc. 
        You will need to provide the GL host, access token, and specific api url.
    """

    count = get_count(host, token, api)

    PER_PAGE = 20
    start_at = 0
    end_at = count

    total_work = end_at - start_at
    total_pages = total_work / PER_PAGE
    start_page = (start_at / PER_PAGE) + 1 # pages are 1-indexed
    end_page = int(math_ceil(float(end_at) / float(PER_PAGE)))


    current_page = start_page

    while current_page <= end_page:
        l.logger.info("Retrieving %d %s" % (PER_PAGE * current_page, api))

        params = {
            "page": current_page,
            "per_page": PER_PAGE
        }
        data = generate_get_request(host, token, api, params=params)
        
        try:
            data = data.json()
            for project in data:
                yield project
            if len(data) < PER_PAGE:
                break
        except Exception, e:
            print e

        if current_page > end_page:
            break


        current_page += 1
        

def search(host, token, path, search_query):
    return generate_get_request(host, token, path, params={'search': search_query}).json()