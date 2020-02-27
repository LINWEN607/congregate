# This creates a json file, "project_repos.json", which contains json data
# for all the repositories in the specified project.

# Arguments:
# 1. Project or Repository
# 2. Write file key
# If project:
#   3. Project browse URL
# If repository:
#   3. Repo name
#   4. HTTPS clone URL

import os
import requests
import json
import re
import sys

from congregate.helpers import conf

config = conf.Config()
main_url = config.external_source_url


# main_url = os.getenv("bb_url")

PROXY_LIST = {
    'http': '',
    'https': ''
}
'''
username = os.getenv('Username')
password = os.getenv('Password')
page_size = int(os.getenv('Page_Size'))
start_index = int(os.getenv('Start_Index'))
s3_bucket_name = os.getenv('S3_Bucket_Name')
file_key = os.getenv('File_Key')
'''
page_size = 100
start_index = 0
# username = os.getenv('mirror_username')
# password = os.getenv('mirror_password')
username = config.external_user_name
password = config.external_user_password


def get_project_key_from_project_browse_url(project_browse_url):
    project_key = project_browse_url.split('/')[-1]
    return project_key

# Returns a list of repo objects in the final format. This is the same
# format that will be stored in the final json file


def get_response(api_url, project_key):
    limit = page_size
    start = 0 if start_index is None else start_index
    is_last_page = False
    # The list which will store the json objects containing useful repo
    # information
    catApiResponse = []
    counter = 0
    while not is_last_page:
        counter += 1
        # print('%s iteration %d' % (project_key.replace('\n', ''), counter))
        response = requests.get(
            api_url,
            params={
                "start": start,
                "limit": limit},
            auth=(
                username,
                password),
            proxies=PROXY_LIST)
        if response.status_code != 200:
            if response.status_code == 404:
                raise ValueError(
                    "Check your URL, it was not found. The URL we attempted was:\n{}\n".format(
                        response.url))
            else:
                raise ValueError(
                    "We encountered an error trying to access the following URL:\n{}\n The actual return code was: \n{}\nOur return data looks like:\n{}\n".format(
                        response.url, response.text))

        response_json = response.json()
        repo_list = response_json.get("values", None)
        if repo_list is not None:
            for repo in repo_list:
                catApiResponse.append(constructJSONObject(repo))
        if response_json.get("isLastPage", None) is not None:
            try:
                is_last_page = response_json["isLastPage"]
            except BaseException:
                print('An error occurred')
                return catApiResponse
        else:
            print("isLastPage is showing as None")
            is_last_page = True
        if not is_last_page:
            start += limit
        else:
            start += len(response_json["values"])
    return catApiResponse


def get_repo_data(api_url, repo_name, project_key):
    response = requests.get(api_url, params={"name": repo_name}, auth=(username, password),
                            proxies=PROXY_LIST).json()
    # if(len(response['values'])) == 0:
    #     raise RuntimeError("No repos matching the name: %s" % repo_name)
    # for repo in response['values']:
    if response['project']['key'].lower() == project_key.lower():
        return constructJSONObject(response)
    raise RuntimeError("No repo match found")


def format_web_repo_url(raw_web_repo_url):
    # Remove svc account credentials if in the url
***REMOVED***
    return final_url


def get_project_name(write_file_key):
    with open(write_file_key) as f:
        data = json.load(f)
    project_name = data[0]['project_name']
    return project_name

# Returns NORMAL or PERSONAL


def get_project_type(project_key):
    if len(project_key) > 0 and project_key[0] == '~':
        return 'PERSONAL'
    return 'NORMAL'

# Method that constructs the JSON representation of a repo that will be
# used to query the repo scan API


def constructJSONObject(repoValues):
    repoObject = {}
    repoObject["id"] = repoValues["id"]
    repoObject["name"] = repoValues["name"]
    # Add the ssh and http URLs:
    for URLItem in repoValues["links"]["clone"]:
        if URLItem["name"].lower() == "ssh".lower():
            repoObject["ssh_repo_url"] = URLItem["href"]
        if URLItem["name"].lower() == "http".lower():
            repoObject["web_repo_url"] = format_web_repo_url(URLItem["href"])
    repoObject["repo_url"] = repoValues["links"]["self"][0]["href"]
    repoObject["group"] = repoValues["project"]["name"]
    repoObject['type'] = get_project_type(repoValues['project']['key'])
    repoObject['project_id'] = repoValues["project"]["id"]
    repoObject['project_key'] = repoValues["project"]["key"]
    repoObject['slug'] = repoValues['slug']
    repoObject['project_name'] = repoValues['project']['name']
    repoObject["project_users"] = get_project_users(repoValues)
    repoObject["repo_users"] = get_repo_users(repoValues)
    if repoObject['type'] == 'PERSONAL':
        repoObject['owner'] = repoValues.get(
            'project').get('owner').get('emailAddress')
    return repoObject


def write_json_to_file(write_file_key, data):
    with open(write_file_key, "w") as f:
        json.dump(data, f, indent=4)


def create_project_objects(project_browse_url, main_url):
    project_key = get_project_key_from_project_browse_url(project_browse_url)
    # Add the repos from the project to final_data
    final_data = []
    url = re.sub(
        '\n', '', "%s/rest/api/1.0/projects/%s/repos" %
        (main_url, project_key))
    project_repo_data = get_response(url, project_key)
    print('%d repos in project.' % len(project_repo_data))
    for repo in project_repo_data:
        final_data.append(repo)
    return final_data


def get_project_key_from_clone_url(clone_url):
    project_key = clone_url.split('/')[-2]
    return project_key


def get_repo_slug_from_clone_url(https_url):
    assert '.git' in https_url, "The https clone url is invalid: %s" % https_url
    str = https_url.split('/')[-1]
    repo_slug = str.split('.git')[-2]
    return repo_slug


def create_repository_objects(repo_name, project_key, repo_slug):
    final_data = []
    url = re.sub(
        '\n', '', '%s/rest/api/1.0/projects/%s/repos/%s' %
        (main_url, project_key, repo_slug))
    repo_data = get_repo_data(url, repo_name, project_key)
    final_data.append(repo_data)
    return final_data


def generate_json(migration_type, url, repo_name=None, write_file_key=None):
    print('\nGathering bitbucket data.')
    data = None
    if migration_type == 'Project' and url is not None:
        data = create_project_objects(url, main_url)
        if write_file_key is not None:
            write_json_to_file(write_file_key, data)
            print('\nData for the %d repositories in %s has been written to %s.' % (
                len(data), get_project_name(write_file_key), write_file_key))
    elif migration_type == 'Repository' and url is not None:
        # assert url[:8] == 'https://' or 'http://'
        repo_slug = get_repo_slug_from_clone_url(url)
        project_key = get_project_key_from_clone_url(url)
        data = create_repository_objects(repo_name, project_key, repo_slug)
        if write_file_key is not None:
            write_json_to_file(write_file_key, data)
            print(
                'Data for repository %s has been written to %s.' %
                (repo_name, write_file_key))

    return data


def get_project_users(repo):
    project_key = repo["project"]["key"]
    project_user_url = "%s/rest/api/1.0/projects/%s/permissions/users" % (
        main_url, project_key)
    project_user_response = requests.get(
        project_user_url, params={
            "start": 0, "limit": 1000}, auth=(
            username, password), proxies=PROXY_LIST)
    new_project_users = []
    project_user_json = project_user_response.json()
    if project_user_json.get("values", None) is not None:
        for user in project_user_json["values"]:
            new_project_users.append(cleanupUsers(user))
    return new_project_users

# Gets the repo level users of the bitbucket repo from the rest API and
# returns them


def get_repo_users(repo):
    project_key = repo["project"]["key"]
    repo_slug = repo['slug']
    url = '%s/rest/api/1.0/projects/%s/repos/%s/permissions/users' % (
        main_url, project_key, repo_slug)
    repo_user_response = requests.get(
        url,
        params={
            "start": 0,
            "limit": 1000},
        auth=(
            username,
            password),
        proxies=PROXY_LIST)
    users = []
    repo_user_json = repo_user_response.json()
    if repo_user_json.get("values", None) is not None:
        for user in repo_user_json["values"]:
            users.append(cleanupUsers(user))
    return users


def cleanupUsers(user):
    u = user["user"]
    email = u.get("emailAddress", None)
    return {
        "displayName": u["displayName"],
        "name": u["name"],
        "email": email,
        "permission": user["permission"]
    }


def main():
    print('\nGathering bitbucket data.')
    migration_type = sys.argv[1].replace('\"', '')
    write_file_key = sys.argv[2].replace('\"', '')
    if migration_type == 'Project':
        project_browse_url = sys.argv[3].replace('\"', '')
        data = create_project_objects(project_browse_url, main_url)
        write_json_to_file(write_file_key, data)
        # print('\nData for the %d repositories in %s has been written to %s.' % (len(data), get_project_name(write_file_key), write_file_key))
    elif migration_type == 'Repository':
        repo_name = sys.argv[3].replace('\"', '')
        clone_url = sys.argv[4].replace('\"', '')
        assert clone_url[:8] == 'https://'
        repo_slug = get_repo_slug_from_clone_url(clone_url)
        project_key = get_project_key_from_clone_url(clone_url)
        data = create_repository_objects(repo_name, project_key, repo_slug)
        write_json_to_file(write_file_key, data)
        # print('Data for repository %s has been written to %s.' % (repo_name, write_file_key))
    print('\nGathering of Bitbucket data is complete.\n')


if __name__ == '__main__':
    main()
    # Uncomment the below block when moving back into the real job
    '''
    try:
        main()
    except Exception as e:
        print('\n%s\n' % str(e))
        sys.exit(1)
    '''
