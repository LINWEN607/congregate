import json

from congregate.helpers.base_class import BaseClass
from congregate.helpers import api, misc_utils
from congregate.migration.gitlab.users import UsersClient
from congregate.migration.gitlab.api.projects import ProjectsApi

class PipelineSchedulesClient(BaseClass):
    def __init__(self):
        self.users = UsersClient()
        self.token_expiration_date = misc_utils.expiration_date()
        self.projects_api = ProjectsApi()
        super(PipelineSchedulesClient, self).__init__()

    def migrate_pipeline_schedules(self, old_id, new_id, users_map, name):
        try:
            p_schedules = self.projects_api.get_all_project_pipeline_schedules(
                old_id,
                self.config.source_host,
                self.config.source_token)
            if p_schedules:
                p_schedules = list(p_schedules)
                if p_schedules:
                    self.log.info("Migrating project {} pipeline schedules".format(name))
                    for schedule in p_schedules:
                        self.__handle_migrating_pipeline_schedule(
                            schedule,
                            old_id,
                            new_id,
                            users_map)
                    return True
                else:
                    self.log.info("Project {} has no scheduled pipelines".format(name))
            else:
                self.log.warn("Failed to retrieve scheduled pipelines for {0}, with response:\n{1}".format(name, p_schedules))
        except Exception, e:
            self.log.error("Failed to migrate scheduled pipelines for {0}, with error:\n{1}".format(name, e))
            return False

    def __handle_migrating_pipeline_schedule(self, schedule, old_project_id, new_project_id, users_map):
        pipeline_schedule_id = self.__get_pipeline_schedule_id(schedule)
        data = self.__build_pipeline_schedule_data(schedule)

        pipeline_schedule_owner = self.users.find_user_by_email_comparison_with_id(
            schedule["owner"]["id"])

        impersonation_token = self.users.find_or_create_impersonation_token(
            self.config.destination_host, self.config.destination_token, pipeline_schedule_owner, users_map, self.token_expiration_date)

        schedule_response = self.projects_api.create_new_project_pipeline_schedule(
            self.config.destination_host, impersonation_token["token"], new_project_id, data)
        if schedule_response.status_code == 201:
            new_schedule_id = self.__get_pipeline_schedule_id(
                schedule_response.json())
            self.__handle_migrating_pipeline_schedule_variables(
                pipeline_schedule_id, new_schedule_id, old_project_id, new_project_id, users_map)

    def __handle_migrating_pipeline_schedule_variables(self, old_schedule_id, new_schedule_id, old_project_id, new_project_id, users_map):
        pipeline_schedule = self.projects_api.get_single_project_pipeline_schedule(
            old_project_id, old_schedule_id, self.config.source_host, self.config.source_token)
        if pipeline_schedule.status_code == 200:
            schedule_json = pipeline_schedule.json()
            for var in schedule_json["variables"]:
                data = self.__build_pipeline_schedule_variable_data(var)
                self.projects_api.create_new_project_pipeline_schedule_variable(
                    new_project_id, new_schedule_id, self.config.destination_host, self.config.destination_token, data)

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
