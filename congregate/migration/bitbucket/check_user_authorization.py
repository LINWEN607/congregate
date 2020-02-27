import os
import json
import requests
import re
import subprocess
import sys

# Script that authorizes the executor of the on-demand migration Jenkins
# job for migration by confirming appropriate admin status of the user.
***REMOVED***
if os.getenv('FirstName') is None:
    first_name_env = re.sub('[^a-zA-Z]+', '', os.getenv('BUILD_USER_FIRST_NAME', ''))
else:
    first_name_env = os.getenv('FirstName')
if os.getenv('LastName') is None:
    last_name_env = re.sub('[^a-zA-Z]+', '', os.getenv('BUILD_USER_LAST_NAME', ''))
else:
    last_name_env = os.getenv('LastName')
username = os.getenv('mirror_username')
password = os.getenv('mirror_password')
repo_name = os.getenv('REPO_NAME')
project_name = os.getenv('Project Name')
input_https_url = os.getenv('HTTPS_Clone_URL')
migration_option = os.getenv('Migration_Option')
project_key = None


def get_repo_slug_from_clone_url(https_url):
    assert len(https_url) > 0 and 'https' in https_url and '.git' in https_url, 'The clone url provided is not formatted correctly: %s' % https_url
    str = https_url.split('/')[-1]
    repo_slug = str.split('.git')[-2]
    return repo_slug


def get_project_key_from_clone_url(https_url):
    return https_url.split('/')[-2]

# Function that checks if the Jenkins and Bitbucket names match


def name_match(bitbucket_name, jenkins_first_name, jenkins_last_name):
    if len(bitbucket_name) <= 0 or len(
            jenkins_first_name) <= 0 or len(jenkins_last_name) <= 0:
        try:
            raise ValueError("One of the names entered is an empty string.")
        except ValueError:
            print(ValueError)
            print('Bitbucket name: ', bitbucket_name)
            print('Jenkins first name: ', jenkins_first_name)
            print('Jenkins last name: ', jenkins_last_name)
    if jenkins_first_name.lower() in bitbucket_name.lower(
    ) and jenkins_last_name.lower() in bitbucket_name.lower():
        return True
    else:
        return False

# Function that returns the correct repo values based on an exact match of
# the repo name and project key


def get_repo_values(api_response, repo_name, https_url):
    assert api_response['name'] is not None

    '''
    matches = []
    values_arr = api_response['values']
    for i in range(len(values_arr)):
        # print('values_arr[%d]: %s' % (i, values_arr[i]))
        print('values_arr repo name: ', values_arr[i]['name'])
        print('repo name: ', repo_name)
        print('project key: ', values_arr[i]['project']['key'])
        print('project key from clone url: ', get_project_key_from_clone_url(https_url))
        if values_arr[i]['name'].lower() == repo_name.lower() and values_arr[i]['project']['key'].lower() == get_project_key_from_clone_url(https_url).lower():
            matches.append(i)
    if len(matches) == 0:
        raise RuntimeError("The repository name provided isn't an exact match for any Bitbucket repositories.")
    elif len(matches) > 1:
        raise RuntimeError("The repository name provided matches multiple Bitbucket repositories.")
    return values_arr[matches[0]]'''

# Check if user who triggered the Jenkins job is an admin of the repo


def is_repo_admin():
    global project_key
    global https_url
    # From repo name, get project key and repo slug
    # url1 = '%s/repos' % url_base

    project_key = get_project_key_from_clone_url(input_https_url)
    repo_slug = get_repo_slug_from_clone_url(input_https_url)
    url1 = '%s/projects/%s/repos/%s' % (url_base, project_key, repo_slug)
    # response_json = requests.get(url1, params={"name": repo_name}, auth=(username, password)).json()
    response_json = requests.get(url1, auth=(username, password)).json()
    # if len(response_json["values"]) == 0:
    #     raise RuntimeError("The repository name provided doesn't match any Bitbucket repositories.")
    # repo_values = get_repo_values(response_json, repo_name, input_https_url)
    # repo_slug = repo_values["slug"]
    repo_slug = response_json["slug"]
    # write_to_file(repo_slug, 'repo_slug.txt')
    project_key = response_json["project"]["key"]
    # write_to_file(project_key, 'project_key.txt')
    project_id = response_json["project"]["id"]
    # write_to_file(str(project_id), 'project_id.txt')
    # Get https url of repo
    for URLItem in response_json["links"]["clone"]:
        if URLItem["name"].lower() == "http".lower():
            https_url = URLItem["href"]
    # Write https URL to file:
    # write_to_file(https_url, 'https_url.txt')
    # From project key and repo slug, get repo users/permissions
    url2 = '%s/projects/%s/repos/%s/permissions/users' % (
        url_base, project_key, repo_slug)
    repo_users = requests.get(url2, auth=(username, password)).json()
    for repo_user in repo_users['values']:
        is_name_match = name_match(
            repo_user['user']['displayName'],
            first_name_env,
            last_name_env)
        if repo_user['permission'].lower() == 'repo_admin':
            is_admin = True
        else:
            is_admin = False
        if is_name_match and is_admin:
            return True
    return False


def get_project_key_from_project_browse_url(project_browse_url):
    project_key = project_browse_url.split('/')[-1]
    return project_key

# Check if user who triggered the Jenkins job is an admin of the project
# to which the repo belongs


def is_project_admin(project_key):
    if project_key is None:
        raise RuntimeError("Cannot access project_key.")
    url = '%s/projects/%s/permissions/users' % (url_base, project_key.lower())
    project_json = requests.get(url, auth=(username, password)).json()
    assert project_json.get(
        'values') is not None, 'There was a problem retrieving project-level permissions for this project. Please try again.'
    for project_user in project_json['values']:
        is_name_match = name_match(
            project_user['user']['displayName'],
            first_name_env,
            last_name_env)
        if project_user['permission'].lower() == 'project_admin':
            is_admin = True
        else:
            is_admin = False
        if is_name_match and is_admin:
            return True
    return False

# Function that determines if the migration should be allowed. Will return
# true if the executor is a repo or project admin


def allow_migration(migration_option, https_url):
    if 'Repository' in migration_option:
        repo_admin_status = is_repo_admin()
        project_key = get_project_key_from_clone_url(https_url)
        project_admin_status = is_project_admin(project_key)
        print('Repository admin status: %s' % repo_admin_status)
        print('Project admin status: %s' % project_admin_status)
        if repo_admin_status or project_admin_status:
            return True
        else:
            return False
    elif 'Project' in migration_option:
        project_browse_url = os.getenv('PROJECT_BROWSE_URL')
        project_key = get_project_key_from_project_browse_url(
            project_browse_url)
        project_admin_status = is_project_admin(project_key)
        print('Project admin status: %s' % project_admin_status)
        if project_admin_status:
            return True
        else:
            return False


def main():
    # Check if migration should be allowed
    print('\nName: %s %s' % (first_name_env, last_name_env))
    allow_migration_status = allow_migration(migration_option, input_https_url)
    # print('First Name: %s' % first_name_env)
    # print('Last Name: %s' % last_name_env)
    print('Allow migration: %s' % allow_migration_status)
    if not allow_migration_status:
        if 'Repository' in migration_option:
            raise RuntimeError(
                "Admin status could not be confirmed for the executor. Please confirm that you are a repository admin or project admin and try again.")
        elif 'Project' in migration_option:
            raise RuntimeError(
                "Admin status could not be confirmed for the executor. Please confirm that you are an admin of this project and try again.")


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('\nThere was a problem confirming user authorization for migration.')
        print('%s\n' % str(error))
        sys.exit(1)
