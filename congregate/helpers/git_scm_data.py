import os
import requests
from congregate.helpers import conf
from congregate.migration.user_authorization.util.misc import stable_retry

# TODO
# 1. add pagination checks
# 2. add stable_retries decorator to things that talk remotely
# 3. add some basic error handling to things that talk remotely, i.e. check for requests return 200
# 4. Figure out some smart ways to store the data in a class, and
# programmatically add to that class.


'''
Python 2.7.15 (default, Jan 12 2019, 21:43:48)
[GCC 4.2.1 Compatible Apple LLVM 10.0.0 (clang-1000.11.45.5)] on darwin
Type "help", "copyright", "credits" or "license" for more information.
>>> import git_scm_data as g
>>> thing = g.SCM_Verifier(project='PROJ1')
>>> thing.projects
{'PROJ1': {'repos': [{'branch_count': 0, 'branches': [], 'name': u'badbranch'}, {'branch_count': 2, 'commits': [{u'authorTimestamp': 1551144056000, u'author': {u'displayName': u'admin', u'name': u'admin', u'links': {u'self': [{u'href': u'http://ec2-18-221-200-207.us-east-2.compute.amazonaws.com:7990/users/admin'}]}, u'id': 1, u'emailAddress': u'mlindsay@gitlab.com', u'active': True, u'type': u'NORMAL', u'slug': u'admin'}, u'parents': [{u'displayId': u'a0d2b60b8c4', u'id': u'a0d2b60b8c4041134eb23776d5713dcbaa01a584'}], u'displayId': u'76fdd32ae29', u'message': u'changed README', u'id': u'76fdd32ae29f8ecf1da7a2b2a3588306b4ad68e4'}, {u'authorTimestamp': 1551143709000, u'author': {u'displayName': u'admin', u'name': u'admin', u'links': {u'self': [{u'href': u'http://ec2-18-221-200-207.us-east-2.compute.amazonaws.com:7990/users/admin'}]}, u'id': 1, u'emailAddress': u'mlindsay@gitlab.com', u'active': True, u'type': u'NORMAL', u'slug': u'admin'}, u'parents': [], u'displayId': u'a0d2b60b8c4', u'message': u'initial commit of repo1', u'id': u'a0d2b60b8c4041134eb23776d5713dcbaa01a584'}], 'branches': [{'latestCommit': u'76fdd32ae29f8ecf1da7a2b2a3588306b4ad68e4', 'type': u'BRANCH', 'name': u'master', 'isDefault': True, 'id': u'refs/heads/master'}, {'latestCommit': u'804bc4172eb71a94e251e9d968d9606775eb8487', 'type': u'BRANCH', 'name': u'feature/branch2', 'isDefault': False, 'id': u'refs/heads/feature/branch2'}], 'name': u'proj1-repo1', 'commits_count': 2}, {'branch_count': 2, 'commits': [{u'authorTimestamp': 1551144532000, u'author': {u'displayName': u'admin', u'name': u'admin', u'links': {u'self': [{u'href': u'http://ec2-18-221-200-207.us-east-2.compute.amazonaws.com:7990/users/admin'}]}, u'id': 1, u'emailAddress': u'mlindsay@gitlab.com', u'active': True, u'type': u'NORMAL', u'slug': u'admin'}, u'parents': [{u'displayId': u'c8ff42b4c2d', u'id': u'c8ff42b4c2d855aa07e0d6c8074aa69638d03c12'}], u'displayId': u'd62d17c560e', u'message': u'corrected README', u'id': u'd62d17c560e9dc08f3dcaadef154e5ce9ea36517'}, {u'authorTimestamp': 1551144440000, u'author': {u'displayName': u'admin', u'name': u'admin', u'links': {u'self': [{u'href': u'http://ec2-18-221-200-207.us-east-2.compute.amazonaws.com:7990/users/admin'}]}, u'id': 1, u'emailAddress': u'mlindsay@gitlab.com', u'active': True, u'type': u'NORMAL', u'slug': u'admin'}, u'parents': [], u'displayId': u'c8ff42b4c2d', u'message': u'readme and test python file', u'id': u'c8ff42b4c2d855aa07e0d6c8074aa69638d03c12'}], 'branches': [{'latestCommit': u'cfe26f161d6d7e1c4e79e69ca79f67a85ba28b67', 'type': u'BRANCH', 'name': u'bugfix/testfiledelete', 'isDefault': False, 'id': u'refs/heads/bugfix/testfiledelete'}, {'latestCommit': u'd62d17c560e9dc08f3dcaadef154e5ce9ea36517', 'type': u'BRANCH', 'name': u'master', 'isDefault': True, 'id': u'refs/heads/master'}], 'name': u'proj1-repo2', 'commits_count': 2}], 'name': 'PROJ1', 'repo_count': 3}}
>>>
'''


class SCMVerifier:
    """
    import git_scm_data
    thing = git_scm_data.SCM_Verifier(project='PROJ1')
    thing.get_all_repos(thing.project, thing.credentials)
    thing.get_all_branches(thing.project, thing.credentials)
    """

    def __init__(self, scm_type='bitbucket', protocol='http',
                 host='ec2-18-221-200-207.us-east-2.compute.amazonaws.com', port='7990', repo=None, **kwargs):
        # Take care of any args that are not defined
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.config = conf.Config()
        # Make sure we have credentials via env_vars or command line
        # I'm not sure of any security ramifications by making it a instance
        # variable
        self.credentials = self.format_credentials(scm_type)
        # Project we are going to work on, convert this to a env var or
        # whatever.
        self.api_endpoints = ['projects', 'repos', 'branches', 'commits']
        # Start with a base URL, further methods will adjust it.
        self.url = self.construct_url(
            "{}://{}:{}".format(protocol, host, port), 'projects')
        # The following isn't DRY, need to find better ways to handle this
        self.projects = {}
        self.config = conf.Config()
        #print("Our self.conf looks like:\n{}\n".format(self.conf))
        self.build_data_structure(self.project)
        if repo is not None:
            self.get_single_repo(self.project, self.credentials, repo=repo)
        else:
            self.get_all_repos(self.project, self.credentials)
        self.get_all_branches(self.project, self.credentials)
        self.get_all_commits(self.project, self.credentials)

    def get_all_repos(self, project, credentials):
        # need to fix the URL, so we aren't setting the global var for every
        # one.
        '''
        For a given project string using the supplied credentials list get all repos attached to that project, and
        assign them to the class variables.
        '''

        url = '{}/{}/repos'.format(self.url, project)
        repos = []
        repos = self.get_json_from_endpoint(
            url, credentials['user'], credentials['password'])
        repo_count = 1  # This isn't actually used, as BB tracks it, leaving it here though in case GL doesn't
        for value in repos['values']:
            if self.projects[project]['repos'].get(
                    value['name'], None) is not None:
                self.projects[project]['repos'][value['name']].append(
                    {
                        'branches': [],
                        'metadata': self.constructJSONObject(value)
                    })
            else:
                self.projects[project]['repos'][value['name']] = {
                    'branches': [],
                    'metadata': self.constructJSONObject(value)
                }
            repo_count += 1
        self.projects[project]['repo_count'] = repos['size']

    def get_single_repo(self, project, credentials, repo=None):
        # need to fix the URL, so we aren't setting the global var for every
        # one.
        '''
        For a given project string using the supplied credentials list get all repos attached to that project, and
        assign them to the class variables.
        '''

        url = '{}/{}/repos/{}'.format(self.url, project, repo)
        repo = self.get_json_from_endpoint(
            url, credentials['user'], credentials['password'])
        if self.projects[project]['repos'].get(
                repo["name"], None) is not None:
            self.projects[project]['repos'][repo['name']].append(
                {
                    'branches': [],
                    'metadata': self.constructJSONObject(repo)
                })
        else:
            self.projects[project]['repos'][repo['name']] = {
                'branches': [],
                'metadata': self.constructJSONObject(repo)
            }
        self.projects[project]['repo_count'] = 1

    def get_all_branches(self, project, credentials):
        '''
        This function should get all details for a given repository
        '''
        for repo, data in self.projects[project]['repos'].iteritems():
            branch_url = '{}/{}/repos/{}/branches'.format(
                self.url, project, repo)
            branches = self.get_json_from_endpoint(
                branch_url, credentials['user'], credentials['password'])
            # Assign the size, this is probably unique to bit bucket
            for branch in branches['values']:
                data['branches'].append(
                    {
                        'name': branch['displayId'],
                        'latestCommit': branch['latestCommit'],
                        'isDefault': branch['isDefault'],
                        'id': branch['id'],
                        'type': branch['type'],
                    }
                )
            data['branch_count'] = branches['size']

    def get_all_commits(self, project, credentials):
        # I hate nested code like this.  Always feel like I'm doing something wrong and the people who aren't
        # faking it until they make it are going to come and get me :D
        for repo, data in self.projects[project]['repos'].iteritems():
            url = '{}/{}/repos/{}/commits'.format(self.url, project, repo)
            # print('\nOur url looks like: {}\n'.format(url))
            commits = self.get_json_from_endpoint(
                url, credentials['user'], credentials['password'])
            if commits:
                data['commits'] = []
                data['commits_count'] = commits['size']
                for commit in commits['values']:
                    data['commits'].append(commit)

                    # print('key: {}, value: {}'.format(thing, commit[thing]))
                    # for key, value in commit:
                    #     print(key, value)
            # if commits: # In case something came back as False
            #     for commit in commits['values']:
            #         for thing in commit:
            #             self.projects[project]['repos'][commits]
            #             print('\nIndividual thing:\n{}\n'.format(thing))
                # repo['branches'].append(
                #     {
                #     'name': branch['displayId'],
                #     'latestCommit': branch['latestCommit'],
                #     'isDefault': branch['isDefault'],
                #     'id': branch['id'],
                #     'type': branch['type'],
                #     }
                # )
            # repo['branch_count'] = branches['size']

    def format_credentials(self, scm_type):
        my_creds = {'user': '', 'password': ''}
        envcredentials = []

        # Set our credentials based on scm_type env vars
        if scm_type.lower() == 'bitbucket':
            envcredentials.append('BITBUCKET_USER')
            envcredentials.append('BITBUCKET_PASSWORD')
            if os.getenv(envcredentials[0]) is None:
                os.environ[envcredentials[0]] = self.config.source_username
            if os.getenv(envcredentials[1]) is None:
                os.environ[envcredentials[1]
                           ] = self.config.external_user_password
        elif scm_type.lower() == 'gitlab':
            envcredentials.append('GITLAB_USER')
            envcredentials.append('GITLAB_PASSWORD')

        # Now that scm_type vars are sorted, lets make sure they exist, and
        # assign them
        try:
            my_creds['user'] = self.config.source_username
            my_creds['password'] = self.config.external_user_password
        except BaseException:
            print("For scm_type: {} we couldn't find the {} or {} envvars".format(
                scm_type, envcredentials[0], envcredentials[1]))
        return my_creds

    def build_data_structure(self, project):
        '''
        This should initialize our basic data structure for a SCM system for any given project string.
        '''
        self.projects[project] = {'name': '{}'.format(project), 'repos': {}}

    def construct_url(self, url, api_endpoints):
        '''
        This function should fully construct a url with a given list api_endpoints
        '''
        # api_endpoints = '/'.join(api_endpoints)
        # This is unique to bitbucket server, should probably template out the
        # api_path based off type
        api_path = '/rest/api/1.0/'

        # Combine it all together
        return '{}{}{}'.format(url, api_path, api_endpoints)

    @stable_retry
    def get_json_from_endpoint(self, url, user, password):
        '''
        This function should return a json body for a given url
        '''
        # First stab at a pagination method
        isLastPage = False  # this is probably specific to bitbucket
        start = 0
        limit = 1000
        results = {"values": []}
        while isLastPage is False:
            r = requests.get('{}'.format(url), params={
                             "start": start, "limit": limit}, auth=(user, password))
            try:
                json_body = r.json()
            except:
                print('\nERROR: Could not decode json.\nHTTP Response was {}\n\nBody Text: {}\n'.format(
                    r.status_code, r.text))
            if r.status_code != 200:
                if r.status_code == 404 or r.status_code == 500:
                    print('\nERROR: HTTP Response was {}\n\nBody Text: {}\n'.format(
                        r.status_code, r.text))
                    return False  # While this is technically an error, in this case, means no records were found for the given resource
                raise ValueError('ERROR HTTP Response was NOT 200, which implies something wrong. The actual return code was {}\n{}\n'.format(
                    r.status_code, r.text))
            if json_body.get("values", None) is not None:
                for value in json_body["values"]:
                    results["values"].append(value)
                isLastPage = json_body['isLastPage']
                # Added the next 2 lines, because just changing start to previous record COULD have issues.
                if isLastPage == False:
                    print("Multipage JSON")
                    start = json_body['nextPageStart']
            elif json_body.get("slug", None) is not None:
                results = json_body
                isLastPage = True
            else:
                print "No values found"
                isLastPage = True
            print(json_body)

        if results.get("values", None) is not None:
            results["size"] = len(results["values"])
        return results

    # def create_repos_automagically(self, project, credentials, count = 50):
    #     '''
    #     Trying to create a bunch of repos automagically
    #     '''
    #     url = '{}/{}/repos'.format(self.url, project)
    #     # temp_repos = []
    #     for i in range(1, count):
    #         temp_repos.append({'name': 'Test Project {}'.format(i)})
    #     print(temp_repos)
        # payload = {[{'name': 'badbranch_list'}, {'name': 'badbranch_list2'}]}
        # user = credentials['user']
        # password = credentials['password']
        # r = requests.post(url, auth=(user, password) , json=payload)
        # print(r, r.text, r.status_code)
        # POST /rest/api/1.0/projects/{projectKey}/repos
        # { "name": "My Repository" }
    #    r = requests.post('{}'.format(url), auth=(user, password))

    def constructJSONObject(self, repoValues):
        repoObject = {
            "id": repoValues["id"],
            "name": repoValues["name"],
            "repo_url": repoValues["links"]["self"][0]["href"],
            "group": repoValues["project"]["name"],
            "type": self.get_project_type(repoValues['project']['key']),
            "project_id": repoValues["project"]["id"],
            "project_key": repoValues["project"]["key"],
            "slug": repoValues['slug'],
            "project_name": repoValues['project']['name'],
            "project_users": self.get_project_users(repoValues),
            "repo_users": self.get_repo_users(repoValues)
        }
        if repoObject['type'] == 'PERSONAL':
            repoObject['owner'] = repoValues.get(
                'project').get('owner').get('emailAddress')
        for URLItem in repoValues["links"]["clone"]:
            if URLItem["name"].lower() == "ssh".lower():
                repoObject["ssh_repo_url"] = URLItem["href"]
            if URLItem["name"].lower() == "http".lower():
                repoObject["web_repo_url"] = self.format_web_repo_url(
                    URLItem["href"])
        return repoObject

    def get_project_type(self, project_key):
        if len(project_key) > 0 and project_key[0] == '~':
            return 'PERSONAL'
        return 'NORMAL'

    def get_project_users(self, repo):
        credentials = self.format_credentials('bitbucket')
        project_key = repo["project"]["key"]
        url = "{}/{}/permissions/users".format(self.url, project_key)
        project_user_json = self.get_json_from_endpoint(
            url, credentials['user'], credentials['password'])
        new_project_users = []
        if project_user_json.get("values", None) is not None:
            for user in project_user_json["values"]:
                new_project_users.append(self.cleanupUsers(user))
        return new_project_users

    # Gets the repo level users of the bitbucket repo from the rest API and
    # returns them

    def get_repo_users(self, repo):
        credentials = self.format_credentials('bitbucket')
        project_key = repo["project"]["key"]
        repo_slug = repo['slug']
        url = "{}/{}/repos/{}/permissions/users".format(
            self.url, project_key, repo_slug)
        repo_user_json = self.get_json_from_endpoint(
            url, credentials['user'], credentials['password'])
        users = []
        if repo_user_json.get("values", None) is not None:
            for user in repo_user_json["values"]:
                users.append(self.cleanupUsers(user))
        return users

    def cleanupUsers(self, user):
        u = user["user"]
        email = u.get("emailAddress", None)
        return {
            "displayName": u["displayName"],
            "name": u["name"],
            "email": email,
            "permission": user["permission"]
        }

    def format_web_repo_url(self, raw_web_repo_url):
        # Remove svc account credentials if in the url
    ***REMOVED***
        return final_url
