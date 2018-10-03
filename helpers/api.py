import urllib
import urllib2
from requests import delete, put
from math import ceil as math_ceil
from json import loads as json_loads


def generate_get_request(host, token, api):
    """
        Generates GET request to GitLab API.
        You will need to provide the GL host, access token, and specific api url.
    """
    url = "%s/api/v4/%s" % (host, api)
    headers = {
        'Private-Token': token,
        'Content-Type': 'application/json'
    }
    req = urllib2.Request(url, headers=headers)
    response = urllib2.urlopen(req)
    return response

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
    req = urllib2.Request(url, headers=headers, data=data)
    response = urllib2.urlopen(req)
    return response

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
    print url
    response = put(url, headers=headers, data=data)
    return response

def generate_delete_request(host, token, api):
    """
        Generates DELETE request to GitLab API.
        You will need to provide the GL host, access token, and specific api url.
    """
    url = "%s/api/v4/%s" % (host, api)
    headers = {
        'Private-Token': token
    }
    response = delete(url, headers=headers)
    return response

def get_count(host, token, api):
    """
        Retrieves total count of projects, users, and groups and returns as a long
        You will need to provide the GL host, access token, and specific api url.
    """
    url = "%s/api/v4/%s" % (host, api)
    headers = {
        'Private-Token': token,
        'Content-Type': 'application/json'
    }
    req = urllib2.Request(url, headers=headers)
    req.get_method = lambda: 'HEAD'
    response = urllib2.urlopen(req)

    return long(response.info().getheader('X-Total'))

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

    #logging.info("List projects from page %d to page %d.", start_page, end_page)

    current_page = start_page

    while current_page <= end_page:
        #logging.info("Listing page %d" % current_page)
        print "Retrieving %d %s" % (PER_PAGE * current_page, api)
        query = {
            "page": current_page,
            "per_page": PER_PAGE
        }

        query_params = urllib.urlencode(query)

        response = generate_get_request(host, token, "%s?%s" % (api, query_params))
        
        data = json_loads(response.read())

        for project in data:
            # Do something with this project
            #logging.info("I have found project %s" % project["name_with_namespace"])
            yield project

        if len(data) < PER_PAGE:
            break

        current_page += 1