from httpx import RequestError
from datetime import datetime
import shutil

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
            
            # Track overall migration statistics
            total_repos = 0
            total_tags = 0
            total_success = 0
            total_skipped = 0
            
            # For every registry in the source project
            for repo in repos:
                error, repo = is_error_message_present(repo)
                if error or not repo:
                    self.log.error(
                        f"Failed to fetch container registries ({repo}) for project {name}")
                    return False
                
                total_repos += 1
                
                # Pull a list of tags via GitLab API
                tags_response = self.projects_api.get_all_project_registry_repositories_tags(
                    old_id, repo["id"], self.config.source_host, self.config.source_token)
                tags = iter(tags_response)
                
                # Process tags and get statistics
                result = self.__walk_tags(project, tags, repo, src_client,
                             dest_client, name, old_id)
                
                # Update overall statistics
                if result:
                    total_tags += result.get("total_tags", 0)
                    total_success += result.get("success_count", 0)
                    total_skipped += result.get("skipped_count", 0)
            
            # Log migration summary at the end
            self.log.info(f"Registry migration summary for project {name} (ID: {old_id}):")
            self.log.info(f"  Total repositories: {total_repos}")
            self.log.info(f"  Total tags across all repositories: {total_tags}")
            self.log.info(f"  Successfully migrated tags: {total_success}")
            self.log.info(f"  Skipped tags (not found or error): {total_skipped}")
            
            # Log warning if there were mismatches
            if total_success < total_tags:
                self.log.warning(f"WARNING: {total_tags - total_success} tags could not be migrated from project {name}")
                if total_tags > 0:
                    self.log.warning(f"Migration completion for project {name}: {total_success}/{total_tags} tags")
            
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
        except RequestError as re:
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
        success_count = 0
        skipped_count = 0
        
        # Count total source tags
        total_tags = len(list(tags))
        
        # Reset tags iterator (since we just consumed it)
        tags_response = self.projects_api.get_all_project_registry_repositories_tags(
            old_id, repo["id"], self.config.source_host, self.config.source_token
        )
        tags = iter(tags_response)
        
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
                            success_count += 1
                            break
                    # Update the error handling in the pull attempt loop
                    except NotFound as nf:
                        ex = nf
                        self.log.warning(
                            f"Registered a NotFound when attempting to pull {repo_loc}:{tag_name} on attempt {pull_attempt}. " +
                            "This could be due to platform incompatibility (e.g., Windows containers on Linux) or the image may not exist. Cleaning.")
                        # NotFound or disk full returning NotFound falsely *OR* possibly returning just an empty image
                        # Let's try to clean-up. This could in theory happen twice
                        self.__clean_local(cleaner, src_client, "src")
                        self.__clean_local(cleaner, dest_client, "dest")
                    except Exception as other_ex:
                        # Handle other exceptions that might occur during pull
                        ex = other_ex
                        self.log.error(
                            f"Error pulling {repo_loc}:{tag_name} on attempt {pull_attempt}: {other_ex}")
                        self.__clean_local(cleaner, src_client, "src")
                        self.__clean_local(cleaner, dest_client, "dest")
                    # Any other exception bubbles up
            if ex:
                skipped_count += 1
                self.log.error(
                    f"Failed to pull {repo_loc}:{tag_name}, skipping due to:\n{ex}" +
                    "\nNote: If this is a Windows container being migrated on a Linux system (or vice versa), " +
                    "this is expected behavior as containers are platform-specific.")
                continue

            # Retag for the new destination
            new_reg = self.generate_destination_registry_url(project, repo_loc)

            all_tags.append(
                (f"{repo_loc}:{tag_name}", f"{new_reg}:{tag_name}")
            )

            if not self.reg_dry_run:
                try:
                    tagged_image.tag(new_reg, tag_name)
                    # Push to the new registry
                    self.log.info(f"Pushing image {new_reg}:{tag_name}")

                    push_success = True
                    for line in dest_client.images.push(
                            new_reg, tag_name, stream=True, decode=True):
                        print(line)
                        if "errorDetail" in line:
                            push_success = False
                            self.log.error(
                                f"Failed to push image to {new_reg}:{tag_name}, due to:\n{line}")

                    # Add to cleaner list
                    cleaner["src"].append(
                        {"repo_loc": repo_loc, "tag_name": tag_name})
                    cleaner["dest"].append(
                        {"new_reg": new_reg, "tag_name": tag_name})
                    
                    # Clean up after each tag to prevent disk space issues
                    self.__clean_local(cleaner, src_client, "src")
                    self.__clean_local(cleaner, dest_client, "dest")
                except Exception as e:
                    self.log.error(f"Error during tag/push for {new_reg}:{tag_name}: {e}")

        # Final cleanup is still needed for any images that may not have been cleaned during iteration
        self.__clean_local(cleaner, src_client, "src")
        self.__clean_local(cleaner, dest_client, "dest")

        # Report on migration results for this repository
        self.log.info(
            f"Registry migration report for repository {repo_loc} of project {name} (ID: {old_id}):")
        self.log.info(f"  Total tags in source: {total_tags}")
        self.log.info(f"  Successfully migrated: {success_count}")
        self.log.info(f"  Skipped (not found or error): {skipped_count}")
        
        if success_count < total_tags:
            self.log.warning(
                f"  WARNING: {total_tags - success_count} tags could not be migrated for repository {repo_loc}")
            self.log.warning(
                f"  Migration completion: {success_count}/{total_tags} tags")
        else:
            self.log.info(f"  All tags successfully migrated ({success_count}/{total_tags})")

        # Write tag mappings to file (without logging each one)
        with open(f"{self.app_path}/data/reg_tuples/{old_id}_repos.tpls", "a") as tplf:
            for tpl in all_tags:
                tplf.write(f"{str(tpl)},\n")
        
        return {
            "total_tags": total_tags,
            "success_count": success_count,
            "skipped_count": skipped_count
        }

    def __clean_local(self, cleaner, client, key):
        """
        Cleans up processed images from the migration only
        
        :param cleaner: List of tags to clean on src and dest client connections
        :param client: Docker client connected to the source or destination instance
        :param key: 'src' or 'dest' to indicate which cleaner list to use
        """
        self.log.info(f"Removing images for key {key} of: {cleaner}\n")
        
        # Remove specific processed images
        for s in cleaner.get(key):
            try:
                client.images.remove(
                    image=f"{s['repo_loc'] if key == 'src' else s['new_reg']}:{s['tag_name']}",
                    force=True
                )
            except Exception as e:
                self.log.warning(f"Error removing image: {e}")
        
        # Only prune dangling images (images with no tags), which are likely leftovers from the migration
        client.images.prune()
        
        # Check disk space, but only log a warning if low
        try:
            # Try common Docker storage paths
            docker_paths = [
                "/var/lib/docker",     # Standard Docker path
                "/var/lib/containers", # Common Podman path
                "/var/lib/podman",     # Alternative Podman path
                "."                    # Current directory as fallback
            ]
            
            # Find first existing path
            docker_dir = None
            for path in docker_paths:
                try:
                    import os
                    if os.path.exists(path):
                        docker_dir = path
                        break
                except:
                    pass
            
            if docker_dir:
                import shutil
                total, used, free = shutil.disk_usage(docker_dir)
                free_gb = free / (1024 * 1024 * 1024)
                
                if free_gb < 10:
                    self.log.warning(f"Low disk space detected ({free_gb:.2f}GB free). You may need to manually clean up unrelated images.")
        except Exception as e:
            self.log.warning(f"Could not check disk space: {e}")
        
        # Reset the cleaner list
        cleaner[key] = []

    def __login_to_registry(self, host, token, registry):
        try:
            # Set up a temporary Docker config directory to avoid permission issues
            import os
            tmp_config_dir = "/tmp/dockerconfig"
            try:
                os.makedirs(tmp_config_dir, mode=0o700, exist_ok=True)
                os.environ['DOCKER_CONFIG'] = tmp_config_dir
            except:
                self.log.warning("Could not set temporary Docker config directory")
            
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
        TODO: Check to see if this change is necessary as it may have been due to a red 
        herring when trying to migrate windows containers on a linux VM.
        Creates a Docker-compatible registry URL while preserving structure as much as possible
        """
        # Debug input values
        self.log.debug(f"Original suffix: {suffix}")
        self.log.debug(f"Source registry: {self.config.source_registry}")
        self.log.debug(f"Project path: {project.get('path_with_namespace')}")
        
        # 1. Extract domain parts without protocol
        if '://' in self.config.source_registry:
            source_domain = self.config.source_registry.split('://')[-1]
        else:
            source_domain = self.config.source_registry
            
        if '://' in self.config.destination_registry:
            dest_domain = self.config.destination_registry.split('://')[-1]
        else:
            dest_domain = self.config.destination_registry
        
        # Remove trailing slashes
        source_domain = source_domain.rstrip('/')
        dest_domain = dest_domain.rstrip('/')
        
        # 2. Handle various source formats
        # First check if the suffix starts with the domain
        suffix_lower = suffix.lower()
        
        if suffix_lower.startswith(source_domain):
            # Extract the path after the domain
            path_after_domain = suffix_lower[len(source_domain):].lstrip('/')
            self.log.debug(f"Path after domain: {path_after_domain}")
        else:
            # If not starting with domain, we might have a different format
            # Just use the full suffix as the path
            path_after_domain = suffix_lower
            self.log.debug(f"Using full suffix: {path_after_domain}")
        
        # 3. Construct final Docker-compatible URL
        target_path = get_target_project_path(project).lower()
        project_path = project.get('path_with_namespace').lower()
        
        # Check for path duplication - avoid adding path segments that are already in the target path
        if path_after_domain.startswith(project_path):
            # Extract only the part after the project path to avoid duplication
            unique_path = path_after_domain[len(project_path):].lstrip('/')
            if unique_path:
                final_url = f"{dest_domain}/{target_path}/{unique_path}"
            else:
                # If nothing left after removing project path, just use the target path
                final_url = f"{dest_domain}/{target_path}"
        elif not path_after_domain or path_after_domain == project_path:
            # Use just the project name for the image if path is empty or matches project
            final_url = f"{dest_domain}/{target_path}"
        else:
            # Keep the path structure but ensure it's Docker-compatible
            # Replace any invalid characters with hyphens
            clean_path = path_after_domain.replace(':', '-').replace('..', '-')
            final_url = f"{dest_domain}/{target_path}/{clean_path}"
        
        # Ensure there are no double slashes
        while '//' in final_url:
            final_url = final_url.replace('//', '/')
        
        # Make sure we don't end with a slash
        final_url = final_url.rstrip('/')
        
        self.log.debug(f"Final URL: {final_url}")
        
        return final_url