from dacite import from_dict
from congregate.helpers.base_class import BaseClass
from congregate.migration.meta.api_models.project_feature_flags import ProjectFeatureFlagPayload
from congregate.migration.gitlab.api.project_feature_flags import ProjectFeatureFlagsApi
from gitlab_ps_utils.misc_utils import is_error_message_present, safe_json_response, get_dry_log

class ProjectFeatureFlagClient(BaseClass):
    def __init__(self, environment_conversion=None, DRY_RUN=True):
        self.project_feature_flags_api = ProjectFeatureFlagsApi()
        self.dry_run = DRY_RUN
        self.environment_conversion = environment_conversion
        super().__init__()

    def get_all_feature_flags_for_project(self, host, token, source_project_id):
        return self.project_feature_flags_api.get_all_project_feature_flags(host, token, source_project_id)

    def create_feature_flag_on_project(self, dst_host, dst_token, destination_project_id, feature_flag):
        """
        Create a new feature flag on a project.

        :param dst_host: (str) GitLab host destination URL
        :param dst_token: (str) Access token to destination GitLab instance
        :param destination_project_id: (int) GitLab destination project ID
        :param feature_flag: (dict) JSON representation of the feature flag
        :yield: Response object containing the migrated objects or False in any error condition
        """
        return self.project_feature_flags_api.create_feature_flag(
            dst_host,
            dst_token,
            destination_project_id,
            feature_flag.get('name'),
            "new_version_flag",
            feature_flag.get('description'),
            feature_flag.get('active'),
            feature_flag.get('strategies')
        )

    def migrate_project_feature_flags_for_project(self, source_project_id, destination_project_id, user_xid_conversion=None):
        """
        Migrate all feature flags from a source project to a destination project.

        :param source_project_id: (int) GitLab source project ID
        :param destination_project_id: (int) GitLab destination project ID
        :param user_xid_conversion: (dict) User ID conversions for the destination project
        :yield: True if successful, False otherwise
        """
        migrated_flags = []
        skipped_flags = []

        try:
            project_feature_flags = self.get_all_feature_flags_for_project(
                self.config.source_host, self.config.source_token, source_project_id
            )

            if not project_feature_flags:
                self.log.info(f"No feature flags found for source_project_id {source_project_id}")
                return True

            for flag in project_feature_flags:
                error, flag = is_error_message_present(flag)
                if error or not flag:
                    self.log.error(f"Failed to list feature flags: {flag}")
                    return False

                # Rewrite strategies
                # self.rewrite_strategies(flag, user_xid_conversion)

                modeled_flag = from_dict(data_class=ProjectFeatureFlagPayload, data=flag)
                self.log.info(f"Moving feature flag {modeled_flag.to_dict()} from source {source_project_id} to {destination_project_id}")

                if not self.dry_run:
                    response = self.create_feature_flag_on_project(
                        self.config.destination_host,
                        self.config.destination_token,
                        destination_project_id,
                        modeled_flag.to_dict()
                    )

                    resp = safe_json_response(response)
                    if response.status_code != 201 or not resp:
                        self.log.error(f"Failed to create feature flag:\nData: {modeled_flag.to_dict()}\nResponse: {resp}")
                        skipped_flags.append(modeled_flag.to_dict())
                    else:
                        migrated_flags.append(resp)
                        self.log.info(f"{get_dry_log(self.dry_run)}Move complete")

            self.log.info(f"Migrated feature flags from {source_project_id} to {destination_project_id}: {migrated_flags}")
            return True

        except Exception as e:
            self.log.error(f"Migration failure: {e}")
            return False

    def rewrite_strategies(self, feature_flag, user_xid_conversion_dict):
        """
        Rewrite strategies of a feature flag.

        :param feature_flag: (dict) Representation of a feature flag
        :param user_xid_conversion_dict: (dict) Mapping of old to new user IDs
        """
        if not user_xid_conversion_dict:
            self.log.error("user_xid_conversion_dict is None")
            return

        if not feature_flag:
            self.log.error("FeatureFlag is None")
            return

        strategies = feature_flag.get("strategies")
        if not strategies:
            self.log.info(f"No strategies found for feature_flag: {feature_flag}")
            return

        for strategy in strategies:
            user_list = strategy.get("user_list")
            if user_list:
                old_id = user_list.get("id")
                new_id = user_xid_conversion_dict.get(str(old_id))
                if not self.dry_run:
                    if old_id and new_id:
                        strategy['user_list_id'] = new_id
                    else:
                        self.log.error(f"Incomplete dictionary:\nstrategy: {strategy}\nuser_xid_conversion_dict: {user_xid_conversion_dict}")
                else:
                    self.log.info(f"{get_dry_log(self.dry_run)}Would rewrite old ID {old_id} with new ID {new_id}")
