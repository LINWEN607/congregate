# When complete, save this file as <script name>.py and zip it into <script name>.zip. The handler is typically <script name>.lambda_handler
# Add imports here
import time
import json
import boto3
# from botocore.vendored import requests
import requests
print('Loading function')


def get_username():
***REMOVED***


def get_password():
    return 'kW20gD2fkW20gD2fkW20gD2kW20g'


def format_web_repo_url(raw_web_repo_url):
    # Remove svc account credentials if in the url
***REMOVED***
    return final_url


def cleanupUsers(user):
    u = user["user"]
    email = u.get("emailAddress", None)
    return {
        "displayName": u["displayName"],
        "name": u["name"],
        "email": email,
        "permission": user["permission"]
    }


def get_project_users(repo, base_url, limit, users_limit,
                      proxy_list, username, password):
    project_key = repo["project"]["key"]
    project_user_url = "%s/rest/api/1.0/projects/%s/permissions/users" % (
        base_url, project_key)
    project_user_response = requests.get(
        project_user_url, params={
            "start": 0, "limit": users_limit}, auth=(
            username, password), proxies=proxy_list)
    new_project_users = []
    project_user_json = project_user_response.json()
    if project_user_json.get("values", None) is not None:
        for user in project_user_json["values"]:
            new_project_users.append(cleanupUsers(user))
    return new_project_users

# Gets the repo level users of the bitbucket repo from the rest API and
# returns them


def get_repo_users(repo, base_url, limit, users_limit,
                   proxy_list, username, password):
    project_key = repo["project"]["key"]
    repo_slug = repo['slug']
    url = '%s/rest/api/1.0/projects/%s/repos/%s/permissions/users' % (
        base_url, project_key, repo_slug)
    repo_user_response = requests.get(
        url,
        params={
            "start": 0,
            "limit": users_limit},
        auth=(
            username,
            password),
        proxies=proxy_list)
    users = []
    repo_user_json = repo_user_response.json()
    if repo_user_json.get("values", None) is not None:
        for user in repo_user_json["values"]:
            users.append(cleanupUsers(user))
    return users

# Returns NORMAL or PERSONAL


def get_project_type(project_key):
    if len(project_key) > 0 and project_key[0] == '~':
        return 'PERSONAL'
    return 'NORMAL'


def construct_repo_object(repoValues, proxy_list, limit,
                          users_limit, base_url, username, password):
    repoObject = {}
    # print('repoValues')
    # print(repoValues)
    repoObject["id"] = repoValues["id"]
    repoObject["name"] = repoValues["name"]
    # print(repoObject["name"])
    #repoObject["description"] = repoValues["project"]["description"]
    # Add the ssh and http URLs:
    for URLItem in repoValues["links"]["clone"]:
        if URLItem["name"].lower() == "ssh".lower():
            repoObject["ssh_repo_url"] = URLItem["href"]
        if URLItem["name"].lower() == "http".lower():
            repoObject["web_repo_url"] = format_web_repo_url(URLItem["href"])
    repoObject["repo_url"] = repoValues["links"]["self"][0]["href"]
    repoObject["group"] = repoValues["project"]["name"]
    repoObject['project_users'] = get_project_users(
        repoValues, base_url, limit, users_limit, proxy_list, username, password)
    repoObject["repo_users"] = get_repo_users(
        repoValues,
        base_url,
        limit,
        users_limit,
        proxy_list,
        username,
        password)
    repoObject['type'] = get_project_type(repoValues['project']['key'])
    if repoObject['type'] == 'PERSONAL':
        repoObject['owner'] = repoValues.get(
            'project').get('owner').get('emailAddress')
    return repoObject


def get_page_from_api(api_url, start_index, limit,
                      proxy_list, username, password):
    response = requests.get(
        api_url,
        params={
            "start": int(start_index),
            "limit": int(limit)},
        auth=(
            username,
            password),
        proxies=proxy_list)
    response_json = response.json()
    # response = requests.get(api_url, params={"start": start_index, "limit": limit}, auth=(username, password), proxies=proxy_list)
    return response_json


def write_data_to_file(write_file_key, data):
    with open(write_file_key, "w") as f:
        json.dump(data, f, indent=4)


def upload_file_to_s3(from_file_key, s3_bucket_name, s3_write_file_key):
    s3 = boto3.client('s3')
    s3.upload_file(from_file_key, s3_bucket_name, s3_write_file_key)


def get_lambda_write_file_key(write_file_key):
    return '/tmp/' + write_file_key


def get_s3_write_file_key(write_file_key, s3_directory):
    return '/%s/%s' % (s3_directory, write_file_key)


def get_write_file_key(start_index, limit):
    end_index = start_index + limit - 1
    write_file_key = 'bitbucket_repos_%d-%d.json' % (start_index, end_index)
    return write_file_key


def get_data_page(api_url, start_index, limit, users_limit,
                  username, password, proxy_list, base_url):
    final_data = []
    print('Getting data for start_index %d.' % start_index)
    page = get_page_from_api(
        api_url,
        start_index,
        limit,
        proxy_list,
        username,
        password)
    if page.get('values', None) is not None:
        for repo in page['values']:
            repo_object = construct_repo_object(
                repo, proxy_list, limit, users_limit, base_url, username, password)
            final_data.append(repo_object)
    is_last_page = page.get('isLastPage')
    # print('isLastPage: %s' % is_last_page)
    if not is_last_page:
        start_index += limit
    return final_data


def lambda_handler(event, context):
    proxy_list = {
        'http': '',
        'https': ''
    }
    limit = int(event['limit'])
    users_limit = int(event['users_limit'])
    start_index = int(event['start_index'])
    username = event['username']
    password = event['password']
    s3_directory = event['s3_directory']
***REMOVED***
    s3_bucket_name = 'vz-app-gts-celv-non-prod-gitlab-migration-s3bucket'
    api_url = "%s/rest/api/1.0/repos" % base_url
    final_data = get_data_page(
        api_url,
        start_index,
        limit,
        users_limit,
        username,
        password,
        proxy_list,
        base_url)
    write_file_key = get_write_file_key(start_index, limit)
    lambda_write_file_key = get_lambda_write_file_key(write_file_key)
    write_data_to_file(lambda_write_file_key, final_data)
    s3_write_file_key = get_s3_write_file_key(write_file_key, s3_directory)
    upload_file_to_s3(lambda_write_file_key, s3_bucket_name, s3_write_file_key)
    # print('Index: %d' % event['start_index'])
    # return 'Index: %d' % event['start_index']
    return 'File %s written to s3.' % s3_write_file_key
    # something new
