from dacite import from_dict
from congregate.helpers.base_class import BaseClass
from congregate.migration.meta.api_models.project_feature_flags_user_lists import ProjectFeatureFlagsUserListsPayload
from congregate.migration.gitlab.api.project_feature_flags_user_lists import ProjectFeatureFlagsUserListsApi
from gitlab_ps_utils.misc_utils import is_error_message_present, safe_json_response, get_dry_log

class ProjectFeatureFlagsUserListsClient(BaseClass):
    def __init__(self, DRY_RUN=True):
        self.project_feature_flag_user_lists_api = ProjectFeatureFlagsUserListsApi()
        self.dry_run = DRY_RUN
        super().__init__()

    def create_feature_flag_user_list_on_project(self, destination_project_id, name, destination_user_xids):
        """
        Create a new feature flag user list on a project.

        :param destination_project_id: (int) GitLab destination project ID
        :param destination_user_xids: (str) A comma-separated list of external user IDs
        :yield: Response object or False in any error condition
        """
        return self.project_feature_flag_user_lists_api.create_project_feature_flag_user_list(
            self.config.destination_host,
            self.config.destination_token,
            destination_project_id,
            name,
            destination_user_xids
        )

    def migrate_project_feature_flags_user_lists_for_project(self, source_project_id, destination_project_id):
        """
        Migrate all feature flag user lists from a source project to a destination project.

        :param source_project_id: (int) GitLab source project ID
        :param destination_project_id: (int) GitLab destination project ID
        :yield: Dictionary with migration status, skipped data, migrated data, and conversion list
        """
        migrated_user_lists = []
        skipped_data = []
        conversion_list = {}

        try:
            user_lists = self.project_feature_flag_user_lists_api.get_all_project_feature_flag_user_lists(
                self.config.source_host, self.config.source_token, source_project_id
            )

            # Convert the response to a list, ensuring the generator is fully consumed
            error, lists = is_error_message_present(user_lists)
            if error:
                self.log.error(f"Failed to list project {source_project_id} feature flag user lists: {lists}")
                return False
            if not lists:
                self.log.info(f"No feature flag user lists found for project {source_project_id}")
                return True

            for user_list in user_lists:
                error, user_list = is_error_message_present(user_list)
                if error or not user_list:
                    self.log.error(f"{get_dry_log(self.dry_run)} Failed to list project {source_project_id} feature flag user lists:\n{user_list}")
                    return None

                modeled_user_list = from_dict(data_class=ProjectFeatureFlagsUserListsPayload, data=user_list)
                self.log.info(f"{get_dry_log(self.dry_run)} Moving {modeled_user_list.to_dict()} from {source_project_id} to {destination_project_id}")

                if not self.dry_run:
                    response = self.create_feature_flag_user_list_on_project(
                        destination_project_id, user_list.get("name"), user_list.get('user_xids')
                    )

                    resp = safe_json_response(response)
                    if response.status_code != 201 or not resp:
                        self.log.error(f"Failed to create project {source_project_id} feature flag user list:\nData: {modeled_user_list.to_dict()}\nResponse: {resp}")
                        skipped_data.append(modeled_user_list.to_dict())
                        continue

                    migrated_user_lists.append(resp)
                    conversion_list[str(modeled_user_list.id)] = resp.get("id")
                    self.log.info(f"{get_dry_log(self.dry_run)} Move complete")

                else:
                    self.log.info(f"{get_dry_log(self.dry_run)} No action performed")

            self.log.info(f"{get_dry_log(self.dry_run)} Migrated {migrated_user_lists} from {source_project_id} to {destination_project_id}")
            self.log.info(f"{get_dry_log(self.dry_run)} User list conversion: {conversion_list}")

            return {
                "completed": len(skipped_data) == 0,
                "skipped_data": skipped_data,
                "migrated_data": migrated_user_lists,
                "user_lists_conversion_list": conversion_list
            }

        except Exception as e:
            self.log.error(f"Migration failure: {e}")
            return {
                "completed": False,
                "skipped_data": skipped_data,
                "migrated_data": migrated_user_lists,
                "user_lists_conversion_list": conversion_list
            }
