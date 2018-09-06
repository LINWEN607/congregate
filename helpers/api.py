import urllib
import urllib2
import requests


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

def generate_delete_request(host, token, api):
    """
        Generates DELETE request to GitLab API.
        You will need to provide the GL host, access token, and specific api url.
    """
    url = "%s/api/v4/%s" % (host, api)
    headers = {
        'Private-Token': token
    }
    response = requests.delete(url, headers=headers)
    return response