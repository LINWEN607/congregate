import sys
import time

from congregate.helpers.base_class import BaseClass
from congregate.helpers.processes import start_multi_process
from congregate.helpers.seed.git import Manage_Repos
from congregate.migration.github.api.orgs import OrgsApi
from congregate.migration.github.api.repos import ReposApi


class Seed_GHE(BaseClass):
    '''
    Basic Seed Class, will walk through the various class pieces, and push repos up to the specified GHE.
    Currently, it assumes you have the repos already cloned.
    '''
    def __init__(self, seeds_count=20, size_ratio=.9, organization="Mike-Test", owner="mlindsay"):
        super(Seed_GHE, self).__init__()
        self.manage_repos = Manage_Repos(size='small')
        self.orgs_api = OrgsApi(self.config.source_host, self.config.source_token)
        self.repos_api = ReposApi(self.config.source_host, self.config.source_token)
        self.seeds_count = seeds_count

        self.repos = self.manage_repos.repos
        self.repo_map = self.manage_repos.repo_map
        self.organization = organization
        self.owner = owner
        self.manage_repos.remote_url = self.manage_repos.remote_url + organization + '/'

    # TODO: Clone the repos if they don't exist.

    def define_seed_repos(self):
        '''
        Using our self.seeds_count, self.size_ratio, and self.repos, create unique names for each repo to fill
        out the complete list of repos we need to work with.
        '''
        new_repos = []
        no_repos = len(self.repos)
        i = 0
        while True:
            cur = i - (i // no_repos) * no_repos
            new_repos.append(f"{self.repos[cur]}-loop-{i // no_repos}")
            i += 1
            if i == self.seeds_count - 1:
                break
        self.repos = new_repos

    def create_org(self):
        '''
        Create an ORG in GHE
        '''
        orgs = self._get_remote_orgs()

        if self._check_org_exists(self.organization, orgs):
            print(f"ERROR: Wouldn't be prudent. Org '{self.organization}' already exists")
            sys.exit()
        else:
            data = {
                'login': self.organization,
                'admin': self.owner
            }
            r = self.orgs_api.create_org(data=data)
            if r.status_code != 201:
                print(
                    f"Encountered an error creating Organization: '{self.organization}'.\nA {r.status_code}"
                    f" was returned, with the following message;\n{r.text}\n"
                )
                sys.exit()

    def create_repo(self, repo):
        data = {
            'name': repo,
        }
        r = self.repos_api.create_org_repo(org_name=self.organization, data=data)
        if r.status_code != 201:
            print(
                f"Encountered an error creating Org Repo: '{repo}'.\nA {r.status_code}"
                f" was returned, with the following message;\n{r.text}\n"
            )
            sys.exit()

    def _check_org_exists(self, org, orgs):
        for record in orgs:
            if org == record['login']:
                return True

    def _get_remote_orgs(self):
        return self.orgs_api.get_all_orgs()

    def check_repos_are_local(self):  # See if we already have the repos downloaded
        pass

    def clone_repos(self):  # Clone the repos
        pass

    def do_it(self, repo):
        self.create_repo(repo)
        self.manage_repos.clone_single_repo(repo)
        self.manage_repos.add_origin(repo)
        self.manage_repos.push_single_repo(repo)


def main():
    start_time = time.time()
    seeds = Seed_GHE(organization='clone-test', seeds_count=100)
    seeds.create_org()  # Creating the org in GHE
    seeds.define_seed_repos()
    print(f"Our Seed Repos in all their glory: \n{seeds.repos}\n")
    start_multi_process(seeds.do_it, seeds.repos)
    print(f"The script took {time.time() - start_time} second !")


if __name__ == "__main__":
    main()
