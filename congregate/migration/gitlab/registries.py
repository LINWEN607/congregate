from requests.exceptions import RequestException

from gitlab_ps_utils.misc_utils import is_error_message_present, safe_json_response

from docker import from_env
from docker.errors import APIError, TLSParameterError, NotFound
from congregate.helpers.base_class import BaseClass
from congregate.helpers.migrate_utils import get_target_project_path
from congregate.migration.gitlab.api.users import UsersApi
from congregate.migration.gitlab.api.projects import ProjectsApi


class RegistryClient(BaseClass):
    def __init__(self, reg_dry_run=False):
        self.users = UsersApi()
        self.projects_api = ProjectsApi()
        super().__init__()
        self.reg_dry_run = reg_dry_run

    def are_enabled(self, new_id, old_id):
        src = self.is_enabled(self.config.source_host,
                              self.config.source_token, old_id)
        dest = self.is_enabled(self.config.destination_host,
                               self.config.destination_token, new_id)
        return (src, dest)

    def is_enabled(self, host, token, pid):
        project = safe_json_response(
            self.projects_api.get_project(pid, host, token))
        return project.get("container_registry_enabled",
                           False) if project else False

    def migrate_registries(self, project, new_id):
        old_id = project.get("id")
        name = project.get("path_with_namespace")
        try:
            reg = self.are_enabled(new_id, old_id)
            if reg[0] and reg[1]:
                return self.migrate(project, old_id, name)
            self.log.warning(
                f"Container registry is disabled for project {name} on {'source' if not reg[0] else 'destination' if not reg[1] else 'source and destination'} instance")
        except Exception as e:
            self.log.error(
                f"Failed to migrate container registries for project {name}, with error:\n{e}")
            return False

    def migrate(self, project, old_id, name):
        try:
            # Login to source registry
            src_client = self.__login_to_registry(
                self.config.source_host,
                self.config.source_token,
                self.config.source_registry
            )
            dest_client = self.__login_to_registry(
                self.config.destination_host,
                self.config.destination_token,
                self.config.destination_registry
            )
            resp = self.projects_api.get_all_project_registry_repositories(
                old_id,
                self.config.source_host,
                self.config.source_token
            )
            repos = iter(resp)
            self.log.info(
                f"Migrating project {name} (ID: {old_id}) container registries")
            # For every registry in the source project
            for repo in repos:
                error, repo = is_error_message_present(repo)
                if error or not repo:
                    self.log.error(
                        f"Failed to fetch container registries ({repo}) for project {name}")
                    return False
                # Pull a list of tags via GitLab API
                tags_response = self.projects_api.get_all_project_registry_repositories_tags(
                    old_id, repo["id"], self.config.source_host, self.config.source_token)
                tags = iter(tags_response)
                self.__walk_tags(project, tags, repo, src_client,
                                 dest_client, name, old_id)
            return True
        except TypeError as te:
            self.log.error(
                f"Project {name} (ID: {old_id}) registries {resp} {te}")
            return False
        except NotFound as nf:
            self.log.error(
                f"Failed to migrate container registries for project {name}, with error:\n{nf}")
            return False
        except APIError as ae:
            self.log.error(f"Failed to export registry, with error:\n{ae}")
            return False
        except RequestException as re:
            self.log.error(
                f"Failed to migrate container registries for project {name}, with error:\n{re}")
            return False

    def __walk_tags(self, project, tags, repo, src_client, dest_client, name, old_id):
        """
        :param tags: list of tags as returned by the GitLab API
        :param repo: the repository we are currently working on for a project
        :param src_client: Docker client logged into the source
        :param dest_client: Docker client logged into the destination
        :param name: The project name
        :param old_id: The source project id

        Slightly modified version of the tagging functionality, that deviates from the original in a couple ways:
        1) Based on the tags as returned by the GitLab API, not by docker pull. This compensates for some issues with pulling where it can fail silently, or not return all images
            when pulling all
        2) Adds a retry scenario to clean-up when we don't get all images, as we can fail silently when disk space runs out
        3) Specifically compensates for NotFound in a disk full scenario by doing a cleaning
        4) Stacks up the cleaning, and only does it either in a potential disk-full scenario, and after every tag set
        """
        # List of tags to clean
        cleaner = {"src": [], "dest": []}

        # The source repo location
        # Eg: registry.gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate/jenkins-seed
        repo_loc = repo["location"]
        all_tags = []
        for tag in tags:
            # The current tag we are working on
            # Eg: latest or rolling-debian, etc
            tag_name = tag["name"]
            ex = False

            if not self.reg_dry_run:
                self.log.info(
                    f"Pulling images from project {name} (ID: {old_id}). Tagged image {repo_loc}:{tag_name}")

                # Pulling everything at once can lead to disk fill, which apparently fails silently. Pull/tag/push on each tag
                # Also, the library will *only* pull latest without the tag, or
                # setting all_tags=True

                for pull_attempt in range(2):
                    try:
                        tagged_image = src_client.images.pull(
                            repo_loc, tag_name)
                        # No NotFound exception, and not None/empty
                        # Exit the try loop
                        if tagged_image:
                            break
                    except NotFound as nf:
                        ex = nf
                        self.log.warning(
                            f"Registered a NotFound when attempting to pull {repo_loc}:{tag_name} on attempt {pull_attempt}. Cleaning.")
                        # NotFound or disk full returning NotFound falsely *OR* possibly returning just an empty image
                        # Let's try to clean-up. This could in theory happen
                        # twice
                        self.__clean_local(cleaner, src_client, "src")
                        self.__clean_local(cleaner, dest_client, "dest")
                    # Any other exception bubbles up
            if ex:
                self.log.error(
                    f"Failed to pull {repo_loc}:{tag_name}, skipping due to:\n{ex}")
                continue

            # Retag for the new destination
            new_reg = self.generate_destination_registry_url(project, repo_loc)

            all_tags.append(
                (f"{repo_loc}:{tag_name}", f"{new_reg}:{tag_name}")
            )

            if not self.reg_dry_run:
                tagged_image.tag(new_reg, tag_name)
                # Push to the new registry
                self.log.info(f"Pushing image {new_reg}:{tag_name}")

                for line in dest_client.images.push(
                        new_reg, tag_name, stream=True, decode=True):
                    print(line)
                    if "errorDetail" in line:
                        self.log.error(
                            f"Failed to push image to {new_reg}:{tag_name}, due to:\n{line}")

                # Clean-up. Slower, possibly, as we have to pull layers, again?
                # Or, can we just make a loop that goes until fails, cleans,
                # then restarts at the failure point?
                cleaner["src"].append(
                    {"repo_loc": repo_loc, "tag_name": tag_name})
                cleaner["dest"].append(
                    {"new_reg": new_reg, "tag_name": tag_name})

        self.__clean_local(cleaner, src_client, "src")
        self.__clean_local(cleaner, dest_client, "dest")

        self.log.info(
            f"All tags pulled for repo {repo_loc} of project {name} (ID: {old_id})\n")
        with open(f"{self.app_path}/data/reg_tuples/{old_id}_repos.tpls", "a") as tplf:
            for tpl in all_tags:
                self.log.info(f"{str(tpl)},\n")
                tplf.write(f"{str(tpl)},\n")

    def __clean_local(self, cleaner, client, key):
        """
        :param cleaner: List of tags to clean on src and dest client connections
        :param src_client: Docker client connected to the source instance
        :param dest_client: Docker client connected to the destination instance
        """
        self.log.info(f"Removing images for key {key} of: {cleaner}\n")
        for s in cleaner.get(key):
            client.images.remove(
                image=f"{s['repo_loc'] if key == 'src' else s['new_reg']}:{s['tag_name']}",
                force=True
            )
        self.log.info(f"Pruned {client.images.prune()}\n")
        cleaner[key] = []

    def __login_to_registry(self, host, token, registry):
        try:
            client = from_env()
            client.login(username=safe_json_response(self.users.get_current_user(host, token)).get("username"),
                         password=token,
                         registry=registry)
            return client
        except (APIError, TLSParameterError) as err:
            self.log.error(
                f"Failed to login to docker registry {registry}, with error:\n{err}")

    def generate_destination_registry_url(self, project, suffix):
        """
        :returns: New reg should be the path to the project prepended with new registry and parent path information, with the suffix
                    So, customer.registry.com/project/path/suffix -> registry.gitlab.com/parent/project/path/suffix
        """
        suffix = suffix.replace(
            f"{self.config.source_registry}/{project.get('path_with_namespace')}".lower(), "")
        return f"{self.config.destination_registry}/{get_target_project_path(project)}{suffix}".lower()
