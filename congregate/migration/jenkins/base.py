import json
from congregate.helpers.base_class import BaseClass
from congregate.migration.jenkins.api.base import JenkinsApi


class JenkinsClient(BaseClass):
    def __init__(self):
        super(JenkinsClient, self).__init__()
        self.jenkins_api = JenkinsApi(self.config.source_host, self.config.source_user, self.config.source_token)

    def retrieve_jobs_with_scm_info(self):
        """
        List and assigns jobs to associated SCM
        """
        data = self.jenkins_api.list_all_jobs()

        jobs_dict = {'jobs': []}
        for job in data['jobs']:
            job_name = job['fullname']
            scm_url = self.jenkins_api.get_scm_by_job(job_name)
            job_dict = {'name': job_name, 'url': scm_url}
            jobs_dict['jobs'].append(job_dict)
        with open('%s/data/jobs.json' % self.app_path, "w") as f:
            json.dump(jobs_dict, f, indent=4)

        return jobs_dict
