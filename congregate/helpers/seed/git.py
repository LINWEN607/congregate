import json
import os
import re
import sys
import subprocess
import uuid
import requests
from gitlab_ps_utils.processes import MultiProcessing


class Manage_Repos():
    '''
    This module should be all about managing our source repo data.  Getting Repos, Cloning, changing remotes, etc...
    '''

    def __init__(
        self,
        remote_name='new-origin',
        temp_dir='congregate/tests/data/repos/',
        remote_url='git@github.example.net:',
        # git@github.example.net:seed-testing/purifycss.git-loop-0.git
        **kwargs

    ):
        """
        Class to manage seed repos. Most things are decided by keyword arguments you pass in.

            :param: rebuild: (str) Start from scratch, usually only for development
                will rebuild the json file.
            :param: clone: (str) Small, Medium, or Large. Clone/download the repos based
                on their size from the json file.
            :param: reorigin: (str) add new remote
            :param: clone: (str) Create a new repos.json file.

            example: git clone https://username:password@github.com/username/repository.git
        """
        self.__dict__.update(**kwargs)
        self.temp_dir = temp_dir
        self.remote_name = remote_name
        self.remote_url = remote_url
        self.verify = True
        self.set_size_limit()  # set the size_limit, defaults to small.
        self.repo_map = self.read_config()  # All the details from repos.json
        self.repos = self.create_repo_list()  # Specific repos we will work with
        self.colors = {
            'red': '\033[1;91m',
            'yellow': '\033[1;93m',
            'green': '\033[1;92m',
            'clear': '\033[0m'
        }
        self.multi = MultiProcessing()

        # Doing this to deal with self.multi.start_multi_process() and commands
        # that require a different cwd.
        if sys.path[0]:
            self.cwd = sys.path[0]
        else:
            self.cwd = "."

        # Some default stuff that will be needed for most tasks
        if not os.path.isdir(self.temp_dir):  # making sure chosen path exists
            message = (
                f"The temp directory '{self.colors['yellow']}{self.temp_dir}{self.colors['clear']}' could not be found.\n"
                f"This script will not create it for you. Either create the directory "
                f"or choose a new one."
            )
            raise Exception(message)

        # Better way of making sure I have a slash, Blame Petar
        os.path.join(self.temp_dir, '')

        if "bare" in self.__dict__:
            self.from_bare()

        # Beginning of our task specific section
        if 'rebuild' in self.__dict__:  # task to create a new json file, then clone the repos
            self.rebuild_config()

        # I screwed this up and need to ponder on it a bit.
        # if 'reorigin' in self.__dict__:  # singular task to add a new remote
        #     self.multi.start_multi_process(self.add_origin, self.repos)

        if 'clone' in self.__dict__:  # pull the repos down
            self.multi.start_multi_process(
                self.clone_single_repo,
                self.repos)  # clone the repos

        if 'push' in self.__dict__:  # push the repos up
            self.multi.start_multi_process(
                self.push_single_repo, self.repos)  # push the repos

        if 'test_all' in self.__dict__:  # This should be used for basic testing, will clone, change origin, and push
            self.multi.start_multi_process(self.clone_single_repo, self.repos)
            self.multi.start_multi_process(self.add_origin, self.repos)
            self.multi.start_multi_process(self.push_single_repo, self.repos)

    def set_size_limit(self):
        '''
        set the max repo size to be used, defaulting to small repos
        small < 10780 ; medium < 1255976 ; large > 1255976 (anything left)
        '''
        if 'size' in self.__dict__:
            self.size = str(self.size)
            if self.size.lower() == 'small':  # small repos 50 megs or less
                self.size = 10780
            elif self.size.lower() == 'medium':  # roughly 500 megs or less
                self.size = 106208
            elif self.size.lower() == 'large':
                self.size = 1255976
            elif self.size.lower() == 'plaid':
                self.size = 80000000  # This is huge, should not be used
        else:
            self.size = 10780

    def size_check(self, repo):
        '''
        Return a boolean if repo size under the size limit
        '''
        if int(self.repo_map[repo]['size']) < self.size:
            return True

    def clone_single_repo(self, repo):
        '''
        For a given repo, clone them to their own self.seed_path directory
        '''
        print(
            f"{self.colors['green']}INFO{self.colors['clear']}: Cloning the {repo} repo.")
        dir_name = self.rebuild_dir(repo)
        self.cwd = self.temp_dir
        cmd = ['git',
               'clone',
               self.repo_map[self.rebuild_dir(repo)]['remote'],
               dir_name]
        rc = self.execute_cmd(cmd)
        if rc.returncode:
            print(
                f"{self.colors['red']}ERROR{self.colors['clear']}: There was an Error cloning the repo "
                f"{self.colors['yellow']}{repo}{self.colors['clear']}:\n{rc.stderr}\n"
                f"Here is the cmd we used: \n{cmd}\n"
                f"Our current working directory: \n{os.getcwd()}\n"
            )
        else:
            print(
                f"{self.colors['green']}INFO{self.colors['clear']}: Successfully cloned the repo: {rc}")

    def push_single_repo(self, repo):
        '''
        Push a repo, including branches and tags, to its new remote.
        '''
        dir_name = self.rebuild_dir(repo)
        print(
            f"{self.colors['green']}INFO{self.colors['clear']}: "
            f"Attempting to push {repo} to {self.repo_map[dir_name]['remote']}"
        )
        # the remote should provide whatever GH ORG we should be pushing to.
        full_remote = self.remote_url + repo
        self.cwd = self.temp_dir + dir_name
        cmd = [
            'git',
            '-c',
            f'http.sslVerify={self.verify}',
            'push',
            '--all',
            full_remote]
        rc_push = self.execute_cmd(cmd)
        cmd = [
            'git',
            '-c',
            f'http.sslVerify={self.verify}',
            'push',
            '--tags',
            full_remote]
        rc_tags = self.execute_cmd(cmd)
        self.cwd = "."
        if rc_push.returncode != 0:
            print(
                f"{self.colors['red']}ERROR{self.colors['clear']}: pushing "
                f"{self.colors['yellow']}{repo}{self.colors['clear']}:\n{rc_push.stderr}"
                f"\nfailed push with: {rc_push}"
            )
        if rc_tags.returncode != 0:
            print(
                f"{self.colors['red']}ERROR{self.colors['clear']}: pushing tags for "
                f"{self.colors['yellow']}{repo}{self.colors['clear']}:\n{rc_tags.stderr}"
                f"\nfailed push with: {rc_push}"
            )

    def rebuild_config(self):
        '''
        This will clone all the repos, then create a json config file.  This
        will probably only be used for local workstation testing.  This will always assume all.
        '''
        self.get_new_seeds()
        self.multi.start_multi_process(
            self.clone_single_repo,
            self.seed_repos)   # clone the repos
        # TODO Clone or check for the existence of repos.
        self.repo_map = self.create_repo_data()
        self.write_config()

    def read_config(self):
        '''
        Sets the class var 'repo_map'
        '''
        with open(f'{self.temp_dir}repos.json', 'r') as f:
            return json.load(f)

    def create_repo_list(self):
        '''
        Sets the class var 'repos'.  This is redundant data, but makes it easier to work with.
        '''
        my_list = []
        for repo in self.repo_map:
            if self.size_check(repo):
                my_list.append(self.repo_map[repo]['name'])
        return my_list

    def write_config(self):
        '''
        Save our json to a file
        '''
        try:
            with open(f"{self.temp_dir}repos.json", "w") as f:
                f.write(json.dumps(self.repo_map, indent=4))
        except Exception as e:
            print(f"There was an error saving a JSON file:\n{e}")
            raise

    def get_new_seeds(self):
        '''
        I made this and its related functions thinking we were going to build
        it out everytime, but that wasn't the case.  Keeping it for posterity's
        sake.
        '''
        self.seed_url = "https://gitlab.com/gitlab-com/support/toolbox/replication/-/raw/master/gitlab/data/seed.rb?inline=false"
        self.seed_path = self.temp_dir + 'seed.rb'
        self.get_gemfile(self.seed_url, self.seed_path)
        self.seed_repos = self.get_repos(self.seed_path)

    def create_repo_data(self):
        '''
        Method to create a directory structure that contains pertinent repo data

        :return: (dict) Containing repo info
        '''
        self.get_new_seeds()  # Some data we need in order to create a config file
        self.repos = self.get_repos_from_dir()

        data = {}
        sizes = self.multi.start_multi_process(self.get_size, self.repos)
        for size in sizes:
            data[next(iter(size))] = {'size': size[next(iter(size))]}
        for repo in self.repos:
            for url in self.seed_repos:
                if repo in url:
                    data[repo].update(
                        {'name': repo, 'original_remote_url': url})
        return data

    def get_size(self, repo):
        '''
        Under Construction, idea being, this will be used to build or rebuild a size map for the JSON file.
        # arbitrarily decided, based off rough mental math
        # small < 10780 ; medium < 1255976 ; large > 1255976 (anything left)
        '''
        dir_name = self.rebuild_dir_for_bare(repo)
        cmd = ['du', '-s', self.temp_dir + dir_name]
        cmd_result = self.execute_cmd(cmd)
        stdout = cmd_result.stdout
        return {repo: stdout.split()[0].decode('utf-8')}

    def add_origin(self, repo):
        '''
        Adding a new remote to a repo, changing if it exists

        :param: repo: (str) The repo we are adding a new remote to.
        '''
        print(
            f"{self.colors['green']}INFO{self.colors['clear']}: Adding remote: "
            f"{self.colors['yellow']}{self.remote_name}{self.colors['clear']} to repo: "
            f"{self.colors['yellow']}{repo}{self.colors['clear']}"
        )
        cmd = [
            'git',
            'remote',
            'add',
            self.remote_name,
            f"{self.remote_url}{repo}.git"
        ]
        self.cwd = self.temp_dir + self.rebuild_dir(repo)
        rc_ao = self.execute_cmd(cmd)
        if rc_ao.returncode and 'fatal: remote new-origin already exists.' in str(
                rc_ao.stderr):
            cmd[2] = 'set-url'
            rc_so = self.execute_cmd(cmd)
            if rc_so.returncode:
                print(
                    f"{self.colors['red']}ERROR{self.colors['clear']}: We were unable to add "
                    f"or change the remote because;\nr{rc_so.stderr}"
                )
        # If we made it this far, we should probably make sure all the branches
        # are checked out as well
        cmd = 'for remote in `git branch -r | grep -v master `; do git checkout --track $remote ; done'
        rc_branch = subprocess.call(cmd, cwd=self.cwd, shell=False)
        print(rc_branch)

        self.cwd = "."

    def rebuild_dir(self, repo):
        '''
        Given our expaned repo names, rebuild the original name so we can find the path.
        This is very fragile as it requires the repo names to have a '-' in them. Our
        seed script should be doing this, but be forewarned.
        '''
        return '-'.join(repo.split('-')[:-2])

    def get_repos_from_dir(self):
        '''
        Return a list of self.temp_dir directories.  Setup for changing remote on git repos
        '''
        dirs_list = []
        try:
            for dir in os.listdir(self.temp_dir):
                if '.git' in dir:
                    dirs_list.append(dir)
            return dirs_list
        except Exception as e:
            print(
                f"There was a problem getting the repos.  Problem reported was:\n{e}")

    def execute_cmd(self, cmd):
        '''
        :param: cmd: (list) A list that starts with the command followed by its arguments as element items.
        :return: (tuple) containing the results of the command
        '''
        return subprocess.run(cmd, cwd=self.cwd, capture_output=True)

    def get_gemfile(self, url, seed_path):
        '''
        get the gemfile from gitlab.com and save it to the data directory, as everying in the data directory is
        .gitignored
        '''
        try:
            # Create the directory if it doesn't exist
            self.create_directory(self.temp_dir)
            r = requests.get(url)  # Get the file from url
            with open(seed_path, 'wb') as f:  # Save the file
                f.write(r.content)
        except Exception as e:
            print(f"We couldn't get or save the gemfile. Reasons:\n{e}")

    def get_repos(self, file_path):
        '''
        Get the https repos out of a ruby file.
        :param: file_path: (str) Path to the seed file
        '''
        with open(file_path, 'r') as f:
            repos = re.findall(r'(https://.*git)', f.read())
        return repos

    def get_seed_repos(self, file_path):
        '''
        Get the https repos out of a ruby file with a - in the name
        :param: file_path: (str) Path to the seed file
        '''
        with open(file_path, 'r') as f:
            repos = re.findall(r'(https://.*/[^/]*-[^/]*.git)', f.read())
        return repos

    def create_directory(self, dir):
        '''
        Make sure the path we are trying to write to exists
        '''
        if not os.path.exists(dir):
            try:
                os.makedirs(os.path.dirname(dir))
                return True
            except Exception as e:
                message = (
                    f"We were unable to create the directory '{dir}'"
                    f"The error returned was: \n {e}"
                )
                raise Exception(message)

    def from_bare(self, skip_pull=True, skip_clone=True):
        """
        Modified rebuild, as the other wasn't processing properly, and I didn't want to muck
        with it if there were any other hooksdatetime A combination of a date and a time. Attributes: ()

        Doesn't handle looping at all, so no appending.
        """

        self.seed_url = "https://gitlab.com/gitlab-com/support/toolbox/replication/-/raw/master/gitlab/data/seed.rb?inline=false"
        self.seed_path = self.temp_dir + 'seed.rb'

        if not skip_pull:
            # Get the seed info
            print(
                f"{self.colors['green']}INFO{self.colors['clear']}: Getting new seeds.")

            print(
                f"{self.colors['green']}INFO{self.colors['clear']}: Getting gemfile from {self.seed_url} and {self.seed_path}.")
            self.get_gemfile(self.seed_url, self.seed_path)

            print(
                f"{self.colors['green']}INFO{self.colors['clear']}: Setting seed_repos with seed_path of {self.seed_path}.")
        else:
            print(
                f"{self.colors['green']}INFO{self.colors['clear']}: Skipping seed file pull")

        # Set the total repos list to everything in the rb file
        self.repos = self.get_repos(self.seed_path)

        # Set seed_repos
        self.seed_repos = self.get_seed_repos(self.seed_path)

        print(
            f"{self.colors['green']}INFO{self.colors['clear']}: Seed_repos are {self.seed_repos}.")

        if not skip_clone:
            # Clone the seed info
            for sr in self.seed_repos:
                self.clone_single_repo_for_bare(sr)
        else:
            print(
                f"{self.colors['green']}INFO{self.colors['clear']}: Skipping clone")

        # Reset repos to only be the cloned set of seeds
        self.repos = self.get_repos_from_dir()

        data = {}
        sizes = self.multi.start_multi_process(self.get_size, self.seed_repos)
        for size in sizes:
            data[next(iter(size))] = {'size': size[next(iter(size))]}
        for repo in self.repos:
            for url in self.seed_repos:
                if repo in url:
                    data[repo].update(
                        {'name': repo, 'original_remote_url': url})
        self.repo_map = data
        self.write_config()

    def rebuild_dir_for_bare(self, repo):
        '''
        Given our expanded repo names, rebuild the original name so we can find the path.
        This is very fragile as it requires the repo names to have a '-' in them. Our
        seed script should be doing this, but be forewarned.
        '''
        print(
            f"{self.colors['green']}INFO{self.colors['clear']}: Rebuilding {repo} dir")
        last_match = re.match(r".*/(.*).git", repo)
        if last_match:
            dir_name = last_match[1]
        else:
            dir_name = str(uuid.uuid4())
        print(
            f"{self.colors['green']}INFO{self.colors['clear']}: Result {dir_name}")
        return dir_name

    def clone_single_repo_for_bare(self, repo):
        '''
        For a given repo, clone them to their own self.seed_path directory
        '''
        print(
            f"{self.colors['green']}INFO{self.colors['clear']}: Cloning the {repo} repo.")
        dir_name = self.rebuild_dir_for_bare(repo)
        self.cwd = self.temp_dir
        # cmd = ['git', 'clone', self.repo_map[self.rebuild_dir(repo)]['remote'], dir_name]
        cmd = ['git', 'clone', repo, dir_name]
        rc = self.execute_cmd(cmd)
        if rc.returncode:
            print(
                f"{self.colors['red']}ERROR{self.colors['clear']}: There was an Error cloning the repo "
                f"{self.colors['yellow']}{repo}{self.colors['clear']}:\n{rc.stderr}\n"
                f"Here is the cmd we used: \n{cmd}\n"
                f"Our current working directory: \n{os.getcwd()}\n"
            )
        else:
            print(
                f"{self.colors['green']}INFO{self.colors['clear']}: Successfully cloned the repo: {rc}")
