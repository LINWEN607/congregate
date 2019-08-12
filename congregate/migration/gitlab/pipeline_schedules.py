from congregate.helpers.base_class import BaseClass
from congregate.helpers import api, misc_utils
from congregate.migration.gitlab.users import UsersClient
import json


class PipelineSchedulesClient(BaseClass):
    def __init__(self):
        self.users = UsersClient()
        self.token_expiration_date = misc_utils.expiration_date()
        super(PipelineSchedulesClient, self).__init__()

    def get_all_pipeline_schedules(self, host, token, project_id):
        return api.list_all(host, token, "projects/%d/pipeline_schedules" % project_id)

    def get_single_pipeline_schedule(self, host, token, project_id, schedule_id):
        return api.generate_get_request(host, token, "projects/%d/pipeline_schedules/%d" % (project_id, schedule_id))

    def create_new_pipeline_schedule(self, host, token, project_id, data):
        return api.generate_post_request(host, token, "projects/%d/pipeline_schedules" % project_id, json.dumps(data))

    def create_new_pipeline_schedule_variable(self, host, token, project_id, pipeline_id, data):
        return api.generate_post_request(host, token, "projects/%d/pipeline_schedules/%d/variables" % (project_id, pipeline_id), json.dumps(data))

    def migrate_pipeline_schedules(self, new_id, old_id, users_map):
        self.log.info("Migrating pipeline schedules")
        for schedule in self.get_all_pipeline_schedules(self.config.source_host, self.config.source_token, old_id):
            self.__handle_migrating_pipeline_schedule(
                schedule, old_id, new_id, users_map)

    def __handle_migrating_pipeline_schedule(self, schedule, old_project_id, new_project_id, users_map):
        pipeline_schedule_id = self.__get_pipeline_schedule_id(schedule)
        data = self.__build_pipeline_schedule_data(schedule)

        pipeline_schedule_owner = self.users.find_user_by_email_comparison(
            schedule["owner"]["id"])

        impersonation_token = self.users.find_or_create_impersonation_token(
            self.config.destination_host, self.config.destination_token, pipeline_schedule_owner, users_map, self.token_expiration_date)

        schedule_response = self.create_new_pipeline_schedule(
            self.config.destination_host, impersonation_token["token"], new_project_id, data)
        if schedule_response.status_code == 201:
            new_schedule_id = self.__get_pipeline_schedule_id(
                schedule_response.json())
            self.__handle_migrating_pipeline_schedule_variables(
                pipeline_schedule_id, new_schedule_id, old_project_id, new_project_id, users_map)

    def __handle_migrating_pipeline_schedule_variables(self, old_schedule_id, new_schedule_id, old_project_id, new_project_id, users_map):
        pipeline_schedule = self.get_single_pipeline_schedule(
            self.config.source_host, self.config.source_token, old_project_id, old_schedule_id)
        if pipeline_schedule.status_code == 200:
            schedule_json = pipeline_schedule.json()
            for var in schedule_json["variables"]:
                data = self.__build_pipeline_schedule_variable_data(var)
                self.create_new_pipeline_schedule_variable(
                    self.config.destination_host, self.config.destination_token, new_project_id, new_schedule_id, data)

    def __get_pipeline_schedule_id(self, schedule):
        return schedule["id"]

    def __build_pipeline_schedule_data(self, schedule):
        return {
            "description": schedule["description"],
            "ref": schedule["ref"],
            "cron": schedule["cron"],
            "cron_timezone": schedule["cron_timezone"],
            "active": schedule["active"]
        }

    def __build_pipeline_schedule_variable_data(self, variable):
        return {
            "key": variable["key"],
            "variable_type": variable["variable_type"],
            "value": variable["value"]
        }
