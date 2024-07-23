import json

from congregate.migration.github.api.base import GitHubApi
from congregate.helpers.conf import Config
from gitlab_ps_utils.misc_utils import safe_json_response


class ReposApi():
    def __init__(self, host, token):
        self.host = host
        self.token = token
        self.api = GitHubApi(self.host, self.token)
        self.config = Config()

    def get_repo(self, owner, repo):
        """
        Get a repository

        GitHub API v3 Doc: https://docs.github.com/en/rest/reference/repos#get-a-repository
        """
        return self.api.generate_v3_get_request(
            self.host,
            f"repos/{owner}/{repo}"
        )

    def get_repo_commits(self, owner, repo):
        """
        List repository commits.

        GitHub API v3 Doc: https://docs.github.com/en/free-pro-team@latest/rest/reference/repos#list-commits
        """
        return self.api.list_all(self.host, f"repos/{owner}/{repo}/commits")

    def get_repo_branches(self, owner, repo):
        """
        List repository branches.

        GitHub API v3 Doc: https://docs.github.com/en/free-pro-team@latest/rest/reference/repos#list-branches
        """
        return self.api.list_all(self.host, f"repos/{owner}/{repo}/branches")

    def get_repo_pulls(self, owner, repo, state="all"):
        """
        List repository pull requests.
        Default behavior returns all pull requests.

        GitHub API v3 Doc: https://docs.github.com/en/free-pro-team@latest/rest/reference/pulls#list-pull-requests
        """
        return self.api.list_all(self.host, f"repos/{owner}/{repo}/pulls?state={state}")

    def get_repo_tags(self, owner, repo):
        """
        List repository tags.

        GitHub API v3 Doc: https://docs.github.com/en/free-pro-team@latest/rest/reference/repos#list-repository-tags
        """
        return self.api.list_all(self.host, f"repos/{owner}/{repo}/tags")

    def get_repo_milestones(self, owner, repo, state="all"):
        """
        List repository milestones.
        Default behavior returns all milestones.

        GitHub API v3 Doc: https://docs.github.com/en/free-pro-team@latest/rest/reference/issues#list-milestones
        """
        return self.api.list_all(self.host, f"repos/{owner}/{repo}/milestones?state={state}")

    def get_repo_issues(self, owner, repo, state="all"):
        """
        List repository issues.
        Default behavior returns all issues.

        GitHub API v3 Doc: https://docs.github.com/en/free-pro-team@latest/rest/reference/issues#list-repository-issues
        """
        return self.api.list_all(self.host, f"repos/{owner}/{repo}/issues?state={state}")

    def get_repo_releases(self, owner, repo):
        """
        List repository releases.

        GitHub API v3 Doc: https://docs.github.com/en/free-pro-team@latest/rest/reference/repos#list-releases
        """
        return self.api.list_all(self.host, f"repos/{owner}/{repo}/releases")

    def get_repo_issue_comments(self, owner, repo, issue):
        """
        List pull request comments.

        GitHub API v3 Doc: https://docs.github.com/en/free-pro-team@latest/rest/reference/issues#list-issue-comments
        """
        return self.api.list_all(self.host, f"repos/{owner}/{repo}/issues/{issue}/comments")

    def get_repo_teams(self, owner, repo):
        """
        List repository teams.
        Available only for org repos, otherwise returns 404.

        GitHub API v3 Doc: https://docs.github.com/en/rest/reference/repos#list-repository-teams
        """
        return self.api.list_all(self.host, f"repos/{owner}/{repo}/teams")

    def get_all_public_repos(self, page_check=False):
        """
        Lists all public repositories in the order that they were created.

        GitHub API v3 Doc: https://docs.github.com/en/rest/reference/repos#list-public-repositories
        """
        return self.api.list_all(self.host, "repositories", page_check=page_check)

    def get_all_user_repos(self, username):
        """
        Lists public repositories for the specified user.

        GitHub API v3 Doc: https://docs.github.com/en/rest/reference/repos#list-repositories-for-a-user
        """
        yield self.api.list_all(self.host, f"users/{username}/repos")

    def get_all_repo_collaborators(self, owner, repo):
        """
        List repository collaborators.
        Requires a collaborator PAT.

        GitHub API v3 Doc: https://docs.github.com/en/rest/reference/repos#list-repository-collaborators
        """
        return self.api.list_all(self.host, f"repos/{owner}/{repo}/collaborators")

    def get_all_repo_deploy_keys(self, owner, repo):
        """
        List repository deploy keys.

        GitHub API v3 Doc: https://docs.github.com/en/rest/deploy-keys?apiVersion=2022-11-28#list-deploy-keys
        """
        return self.api.list_all(self.host, f"repos/{owner}/{repo}/keys")

    def create_auth_user_repo(self, data=None, message=None):
        """
        Creates a new repository for the authenticated user.

        GitHub API v3 Doc: https://docs.github.com/en/enterprise/2.21/user/rest/reference/repos#create-a-repository-for-the-authenticated-user
        """
        if not message:
            print(
                f"Creating a new repository for the authenticated user {data}")

        return self.api.generate_v3_post_request(
            self.host,
            "user/repos",
            json.dumps(data),
            description=message
        )

    def create_org_repo(self, org_name, data=None, message=None):
        """
        Create an organization repository.

        GitHub API v3 Doc: https://docs.github.com/en/enterprise/2.21/user/rest/reference/repos#create-an-organization-repository
        """
        if not message:
            print(f"Creating an organization repository {data}")

        return self.api.generate_v3_post_request(
            self.host,
            f"orgs/{org_name}/repos",
            data,
            description=message
        )

    def get_single_project_protected_branch(self, owner, repo, branch):
        """
        Gets branch protection.

        GitHub API v3 Doc: https://docs.github.com/en/free-pro-team@latest/rest/reference/repos#get-branch-protection
        """
        return self.api.generate_v3_get_request(self.host, f"repos/{owner}/{repo}/branches/{branch}/protection")

    def update_repo(self, owner, repo, data=None, message=None):
        """
        Update a repository.

        GitHub API v3 Doc: https://developer.github.com/v3/repos/#update-a-repository
        """
        return self.api.generate_v3_patch_request(self.host, f"repos/{owner}/{repo}", data, message)

    def list_pull_requests(self, owner, repo, state="all"):
        """
        List pull requests.

        GitHub API v3 Doc: https://developer.github.com/v3/pulls/#list-pull-requests
        """
        return self.api.generate_v3_get_request(self.host, f"repos/{owner}/{repo}/pulls?state={state}")

    def get_a_single_pull_request(self, owner, repo, pull_number):
        """
        Get a pull request.

        GitHub API v3 Doc: https://developer.github.com/v3/pulls/#get-a-pull-request
        """
        return self.api.generate_v3_get_request(self.host, f"repos/{owner}/{repo}/{pull_number}")

    def list_reviewers_for_a_pull_request(self, owner, repo, pull_number):
        """
        List requested reviewers for a pull request.

        GitHub API v3 Doc: https://developer.github.com/v3/pulls/review_requests/#list-requested-reviewers-for-a-pull-request
        """
        return self.api.generate_v3_get_request(self.host, f"repos/{owner}/{repo}/pulls/{pull_number}/requested_reviewers")
    
    def get_repo_v4(self, owner, repo):
        """
        Get a repository using GraphQL.
        """
        query = """
        query($owner: String!, $name: String!) {
            repository(owner: $owner, name: $name) {
                name
                description
                url
                createdAt
                updatedAt
                stargazerCount
                viewerPermission
            }
        }
        """
        variables = {
            "owner": owner,
            "name": repo
        }
        return self.api.generate_v4_post_request(self.host, query, variables)

    def get_repo_commits_v4(self, owner, repo):
        """
        List repository commits using GraphQL.
        """
        query = """
        query($owner: String!, $name: String!, $limit: Int!) {
            repository(owner: $owner, name: $name) {
                ref(qualifiedName: "main") {
                    target {
                        ... on Commit {
                            history(first: $limit) {
                                edges {
                                    node {
                                        message
                                        committedDate
                                        author {
                                            name
                                            email
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        variables = {
            "owner": owner,
            "name": repo,
            "limit": 100
        }
        return self.api.generate_v4_post_request(self.host, query, variables)

    def get_repo_branches_v4(self, owner, repo):
        """
        List repository branches using GraphQL with pagination.
        """
        query = """
        query($owner: String!, $name: String!, $cursor: String) {
            repository(owner: $owner, name: $name) {
                refs(refPrefix: "refs/heads/", first: 100, after: $cursor) {
                    nodes {
                        name
                        target {
                            ... on Commit {
                                oid
                            }
                        }
                        branchProtectionRule {
                            id
                        }
                    }
                    pageInfo {
                        endCursor
                        hasNextPage
                    }
                }
            }
        }
        """
        variables = {
            "owner": owner,
            "name": repo,
            "cursor": None
        }

        all_branches = []
        while True:
            response = safe_json_response(self.api.generate_v4_post_request(self.host, query, variables))
            if response and 'data' in response:
                branches_data = response['data']['repository']['refs']
                all_branches.extend(branches_data['nodes'])
                if branches_data['pageInfo']['hasNextPage']:
                    variables['cursor'] = branches_data['pageInfo']['endCursor']
                else:
                    break
            else:
                break

        return all_branches

    def get_repo_pulls_v4(self, owner, repo, state="OPEN"):
        """
        List repository pull requests using GraphQL.
        """
        query = """
        query($owner: String!, $name: String!, $state: PullRequestState!, $cursor: String) {
            repository(owner: $owner, name: $name) {
                pullRequests(states: [$state], first: 100, after: $cursor) {
                    nodes {
                        number
                        title
                        body
                        state
                        createdAt
                        updatedAt
                        draft
                        author {
                            login
                        }
                        assignees(first: 100) {
                            nodes {
                                login
                            }
                        }
                        milestone {
                            title
                        }
                    }
                    pageInfo {
                        endCursor
                        hasNextPage
                    }
                }
            }
        }
        """
        variables = {
            "owner": owner,
            "name": repo,
            "state": state,
            "cursor": None
        }

        all_pulls = []
        while True:
            response = safe_json_response(self.api.generate_v4_post_request(self.host, query, variables))
            if response and 'data' in response:
                pulls_data = response['data']['repository']['pullRequests']
                all_pulls.extend(pulls_data['nodes'])
                if pulls_data['pageInfo']['hasNextPage']:
                    variables['cursor'] = pulls_data['pageInfo']['endCursor']
                else:
                    break
            else:
                break

        return all_pulls

    def get_repo_tags_v4(self, owner, repo):
        """
        List repository tags using GraphQL.
        """
        query = """
        query($owner: String!, $name: String!, $cursor: String) {
            repository(owner: $owner, name: $name) {
                refs(refPrefix: "refs/tags/", first: 100, after: $cursor) {
                    nodes {
                        name
                        target {
                            ... on Commit {
                                oid
                            }
                        }
                    }
                    pageInfo {
                        endCursor
                        hasNextPage
                    }
                }
            }
        }
        """
        variables = {
            "owner": owner,
            "name": repo,
            "cursor": None
        }

        all_tags = []
        while True:
            response = safe_json_response(self.api.generate_v4_post_request(self.host, query, variables))
            if response and 'data' in response:
                tags_data = response['data']['repository']['refs']
                all_tags.extend(tags_data['nodes'])
                if tags_data['pageInfo']['hasNextPage']:
                    variables['cursor'] = tags_data['pageInfo']['endCursor']
                else:
                    break
            else:
                break

        return all_tags

    def get_repo_milestones_v4(self, owner, repo, state="ALL"):
        """
        List repository milestones using GraphQL.
        """
        query = """
        query($owner: String!, $name: String!, $state: [MilestoneState!]) {
            repository(owner: $owner, name: $name) {
                milestones(states: $state, first: 100) {
                    nodes {
                        title
                        description
                        state
                        dueOn
                    }
                }
            }
        }
        """
        variables = {
            "owner": owner,
            "name": repo,
            "state": state
        }
        return self.api.generate_v4_post_request(self.host, query, variables)

    def get_repo_issues_v4(self, owner, repo, state="OPEN"):
        """
        List repository issues using GraphQL.
        """
        query = """
        query($owner: String!, $name: String!, $state: [IssueState!]) {
            repository(owner: $owner, name: $name) {
                issues(states: $state, first: 100) {
                    nodes {
                        title
                        body
                        createdAt
                        url
                        state
                    }
                }
            }
        }
        """
        variables = {
            "owner": owner,
            "name": repo,
            "state": state
        }
        return self.api.generate_v4_post_request(self.host, query, variables)

    def get_repo_releases_v4(self, owner, repo):
        """
        List repository releases using GraphQL.
        """
        query = """
        query($owner: String!, $name: String!) {
            repository(owner: $owner, name: $name) {
                releases(first: 100) {
                    nodes {
                        name
                        description
                        publishedAt
                        url
                    }
                }
            }
        }
        """
        variables = {
            "owner": owner,
            "name": repo
        }
        return self.api.generate_v4_post_request(self.host, query, variables)

    def get_repo_issue_comments_v4(self, owner, repo, issue_number):
        """
        List repository issue comments using GraphQL.
        """
        query = """
        query($owner: String!, $name: String!, $issueNumber: Int!) {
            repository(owner: $owner, name: $name) {
                issue(number: $issueNumber) {
                    comments(first: 100) {
                        nodes {
                            body
                            createdAt
                            author {
                                login
                            }
                        }
                    }
                }
            }
        }
        """
        variables = {
            "owner": owner,
            "name": repo,
            "issueNumber": issue_number
        }
        return self.api.generate_v4_post_request(self.host, query, variables)

    def get_repo_teams_v4(self, owner, repo):
        """
        List repository teams using GraphQL.
        """
        query = """
        query($owner: String!, $name: String!) {
            repository(owner: $owner, name: $name) {
                teams(first: 100) {
                    nodes {
                        slug
                        name
                        description
                    }
                }
            }
        }
        """
        variables = {
            "owner": owner,
            "name": repo
        }
        return self.api.generate_v4_post_request(self.host, query, variables)

    def get_all_public_repos_v4(self):
        """
        Lists all public repositories using GraphQL.
        """
        query = """
        query {
            search(query: "is:public", type: REPOSITORY, first: 100) {
                edges {
                    node {
                        ... on Repository {
                            name
                            owner {
                                login
                            }
                            description
                            url
                        }
                    }
                }
            }
        }
        """
        return self.api.generate_v4_post_request(self.host, query)

    def get_all_user_repos_v4(self, username):
        """
        Lists public repositories for the specified user using GraphQL.
        """
        query = """
        query($login: String!, $limit: Int!) {
            user(login: $login) {
                repositories(first: $limit, privacy: PUBLIC) {
                    nodes {
                        name
                        description
                        url
                    }
                }
            }
        }
        """
        variables = {
            "login": username,
            "limit": 100
        }
        return self.api.generate_v4_post_request(self.host, query, variables)

    def get_all_repo_collaborators_v4(self, owner, repo):
        """
        List repository collaborators using GraphQL.
        """
        query = """
        query($owner: String!, $name: String!) {
            repository(owner: $owner, name: $name) {
                collaborators(first: 100) {
                    nodes {
                        login
                        name
                        url
                    }
                }
            }
        }
        """
        variables = {
            "owner": owner,
            "name": repo
        }
        return self.api.generate_v4_post_request(self.host, query, variables)

    def get_all_repo_deploy_keys_v4(self, owner, repo):
        """
        List repository deploy keys using GraphQL.
        """
        query = """
        query($owner: String!, $name: String!) {
            repository(owner: $owner, name: $name) {
                deployKeys(first: 100) {
                    nodes {
                        id
                        title
                        createdAt
                    }
                }
            }
        }
        """
        variables = {
            "owner": owner,
            "name": repo
        }
        return self.api.generate_v4_post_request(self.host, query, variables)

    def list_pull_requests_v4(self, owner, repo, state="OPEN"):
        """
        List pull requests using GraphQL.
        """
        query = """
        query($owner: String!, $name: String!, $state: [PullRequestState!]) {
            repository(owner: $owner, name: $name) {
                pullRequests(states: $state, first: 100) {
                    nodes {
                        title
                        body
                        createdAt
                        url
                        state
                    }
                }
            }
        }
        """
        variables = {
            "owner": owner,
            "name": repo,
            "state": state
        }
        return self.api.generate_v4_post_request(self.host, query, variables)

    def get_a_single_pull_request_v4(self, owner, repo, pull_number):
        """
        Get a pull request using GraphQL.
        """
        query = """
        query($owner: String!, $name: String!, $number: Int!) {
            repository(owner: $owner, name: $name) {
                pullRequest(number: $number) {
                    title
                    body
                    createdAt
                    url
                    state
                }
            }
        }
        """
        variables = {
            "owner": owner,
            "name": repo,
            "number": pull_number
        }
        return self.api.generate_v4_post_request(self.host, query, variables)

    def list_reviewers_for_a_pull_request_v4(self, owner, repo, pull_number):
        """
        List requested reviewers for a pull request using GraphQL.
        """
        query = """
        query($owner: String!, $name: String!, $number: Int!) {
            repository(owner: $owner, name: $name) {
                pullRequest(number: $number) {
                    requestedReviewers(first: 100) {
                        nodes {
                            login
                            name
                            url
                        }
                    }
                }
            }
        }
        """
        variables = {
            "owner": owner,
            "name": repo,
            "number": pull_number
        }
        return self.api.generate_v4_post_request(self.host, query, variables)
