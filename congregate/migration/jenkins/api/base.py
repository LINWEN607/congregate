import json
import jenkins
from congregate.helpers.misc_utils import xml_to_dict


class JenkinsApi():
    GET_ALL_JOBS = """
            import groovy.json.JsonBuilder;

            // get all projects excluding matrix configuration
            // as they are simply part of a matrix project.
            // there may be better ways to get just jobs
            items = Jenkins.instance.getAllItems(AbstractProject);
            items.removeAll {
                it instanceof hudson.matrix.MatrixConfiguration
            };

            def json = new JsonBuilder()
            def root = json {
                jobs items.collect {
                    [
                    name: it.name,
                    url: Jenkins.instance.getRootUrl() + it.getUrl(),
                    color: it.getIconColor().toString(),
                    fullname: it.getFullName()
                    ]
                }
            }

            // use json.toPrettyString() if viewing
            println json.toString()
        """

    GET_ALL_SCM = """
            Jenkins.instance.getAllItems(hudson.model.AbstractProject.class).each
            {
                it ->
                scm = it.getScm()
                if(scm instanceof hudson.plugins.git.GitSCM)
                {
                    println scm.getUserRemoteConfigs()[0].getUrl()
                }
            }
        """

    def __init__(self, host, user, token):
        self.host = host
        # Jenkins API token generated within Jenkins instance by going to User Profile -> Configure -> API Token
        self.token = token
        self.user = user

        # Connect to server
        self.server = jenkins.Jenkins(self.host, username=self.user, password=self.token)

    def list_jobs(self):
        '''
        https://python-jenkins.readthedocs.io/en/latest/api.html#jenkins.Jenkins.get_jobs
        Parameters:
        folder_depth - Number of levels to search, int. By default 0, which will limit search to toplevel. None disables the limit.
        view_name - Name of a Jenkins view for which to retrieve jobs, str. By default, the job list is not limited to a specific view.
        Returns:	list of jobs, [{str: str, str: str, str: str, str: str}]
        '''
        return self.server.get_jobs()

    def list_all_jobs(self):
        # https://python-jenkins.readthedocs.io/en/latest/api.html#jenkins.Jenkins.get_all_jobs
        # returns dictionary with list of jobs
        return(json.loads(self.server.run_script(self.GET_ALL_JOBS)))

    def list_all_scm(self):
        # Get all SCM Git urls listed, uses https://python-jenkins.readthedocs.io/en/latest/api.html#jenkins.Jenkins.run_script
        # returns list of all scm found in jobs (includes duplicates)
        scmallinfo = self.server.run_script(self.GET_ALL_SCM)

        scmallinfo_list = scmallinfo.split('\n')

        return(scmallinfo_list)

    def get_job_config(self, job_name):
        '''
        https://python-jenkins.readthedocs.io/en/latest/api.html#jenkins.Jenkins.get_job_config
        Parameters:	name - Name of Jenkins job, str
        Returns:    Ordered Dictionary of job configuration data
        '''
        return xml_to_dict(self.server.get_job_config(job_name))

    def get_job_info(self, job_name):
        '''
        https://python-jenkins.readthedocs.io/en/latest/api.html#jenkins.Jenkins.get_job_info
        name - Job name, str
        depth - JSON depth, int
        fetch_all_builds - If true, all builds will be retrieved from Jenkins. Otherwise, Jenkins will only return the most recent 100 builds. 
        This comes at the expense of an additional API call which may return significant amounts of data. bool
        Returns:    dictionary of job information
        '''
        return self.server.get_job_info(job_name, 4)

    def get_info(self):
        '''
        https://python-jenkins.readthedocs.io/en/latest/api.html#jenkins.Jenkins.get_info
        Parameters:
        item - item to get information about on this Master
        query - xpath to extract information about on this Master
        Returns:	dictionary of information about Master or item, dict
        '''
        return self.server.get_info()

    def get_scm_by_job(self, job_name):
        # returns a string of scm from specified job
        return self.server.run_script(f"""
        item = Jenkins.instance.getItemByFullName("{ job_name }")
        println item.getScm().getUserRemoteConfigs()[0].getUrl()
        """)

    def get_job_params(self, job_name):
        # returns a list of job params
        job_info = self.get_job_info(job_name)

        param_list = []

        for action in job_info['actions']:
            if 'parameterDefinitions' in action:
                param_list.append(action['parameterDefinitions'])

        return param_list
