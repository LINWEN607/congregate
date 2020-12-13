from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import safe_json_response
from congregate.migration.gitlab.api.issues import IssuesApi
from congregate.migration.gitlab.users import UsersClient
import re


class Reporting(BaseClass):
    '''
    Reporting class, designed to work at the project level.  Feed it a project data structure, and it will attempt to
    create reporting issues. If dry_run is passed, we WILL make read only API calls (Checking users, issues, etc...).

        :param reporting_project_id: (int)  This should be the project ID where the issues will be created.  They
            should exist OUTSIDE of migration groups or projects, so as to not effect rollbacks.
        :param project: (dict) This should be the dict from migrate.py containing relevant project data.

    TODO: If we add link to issue, make sure issue state is open
    TODO: The spreadsheet importer should return a None value for empty columns
    TODO: if a task already exists in a issue, verify task link is correct (incase we rollback or some other shenanigans)
    TODO: if we actually did reimport the repo, reopen the task
    TODO: followup on issue update status, log messages appropriately if issue updated
    TODO: Issues are modified/created even on a dry run.

    '''

    def __init__(self, reporting_project_id, dry_run=True):
        self.reporting_project_id = reporting_project_id
        self.issuesApi = IssuesApi()
        self.usersClient = UsersClient()
        self.templates = []
        super(Reporting, self).__init__()
        self.dry_run = dry_run

    def init_class_vars(self, staged_projects, import_results):
        '''
        Do the needful. Check/Create issues, assign tasks, etc...

        >>> ri = Reporting(reporting_project_id, project)
        >>> ri.init_class_vars()
        >>> ri.reporting_issues # saving this data in case we want to use it later
        {issue_iid: {'iid': 345, 'title', 'some title'}, issue_iid: {'iid': 345, 'title', 'some title'}}

        '''

        self.combined_data = self.combine_wave_data(staged_projects, import_results)
        self.reporting_issues = {}  # The issues this class will return
        self.combined_data['issues'] = self.get_project_issues()
        self.new_issues = []
        self.combined_data['users'] = self.define_users(self.combined_data['projects'])


        # Read our configuration issues in
        for issue in self.config.reporting['post_migration_issues']:
            self.new_issues.append(self.read_template_file(issue))
        # self.reporting_issues = {self.project['swc_id']: {}}

        # print(f"{'*' * 80}")
        # for issue in self.combined_data['users']:
        #     print(f"issue: {issue['title']}")
        # print(f"{'*' * 80}")
        # print(f"users: {self.combined_data['users']}")
        self.get_required_users(self.combined_data['users'])
        return

        # Convert our spreadsheet defined email into a GitLab Username
        if user := self.usersClient.find_user_by_email_comparison_without_id(self.project.get('swc_manager_email')):
            self.assignee = user['username']
        else:
            self.assignee = None

        for issue in self.new_issues:
            # Template variable substitution
            issue['description'] = self.check_substituions(issue['description'])
            # Use an existing issue if we find one, otherwise create a new issue
            issue_data = self.check_existing_issues(f"{self.project['swc_id'].upper()} | {issue['title']}")
            if not issue_data:
                issue_data = self.create_issue(issue, self.project['swc_id'])
            # Clean up the data and save it in the class var self.reporting_issues
            if issue_data:
                self.reporting_issues[self.project['swc_id']][issue_data['iid']] = self.format_issue_data(issue_data)
        self.fix_issues()

    def get_required_users(self, users):
        '''
        Check if our email has a GitLab username or not
        '''

        new_users = {}
        self.log.info(f"There are '{len(users)}' emails to check.")
        for email in users:
            if not users[email]:
                if username := self.usersClient.find_user_by_email_comparison_without_id(email):
                    print(f"\nFound username: {username['username']}\n")
                else:
                    print(f"\nno user for '{email}'\n")
        

    def define_users(self, clean_data):
        '''

        Create a user mapping dict from clean_data, containing email as key to hold future data

        :param clean_data: (dict)

        '''

        users = {}
        for project in clean_data:
            users[clean_data[project]['swc_manager_email']] = None

        return users

    def combine_wave_data(self, staged_projects, import_results):
        '''
        Take staged_projects and import_results, combine them, and return the resulting successful dataset

        :param staged_projects: (str) The staged projects used in our migration
        :param import_results: (str) The results of our migration
        :return: (dict) A dictionary of the successful results, keyed off repo.

        '''
        clean_data = {}
        # removing the counts dictionary
        clean_data['projects'] = self.check_import_results(import_results)
        clean_data['projects'] = self.check_staged_projects(staged_projects, clean_data['projects'])
        return clean_data

    # TODO: recreate all the migrate.py stuff into reporting.py.  Leaving only the class instantiation in migrate.py
    # TODO: implement all the random code pulled over from migrate.py
    '''
            if self.check_required_reporting_issues:  # This is making sure all required fields are present.
            self.log.info("Successfully got reporting config from congregate.conf. Proceeding to make our issues.")

       else:
            self.log.warning(
                f"Couldn't find a required REPORTING config in [DESTINATION] section of congregate.conf.\n"
                f"Issues will not be created."
            )

    '''
    def rpt_needful(self, import_results, staged_projects):
        '''

        This method will call the required methods to massage the data, and lessen our API calls.
        '''

        # Getting successful project imports or already imported projects
        successes = self.reporting_check_results(import_results)

        # Reporting on completed projects
        for completed_project in staged_projects:
            if completed_project['path_with_namespace'] in successes:
                self.create_tracking_issues(completed_project)

    def check_reporting_config(self):
        '''
        Check that all our REQUIRED reporting fields are in congregate.conf. Return True if so. This will not check non 
        required fields.
        '''
        if all([
            self.config.reporting,
            self.config.reporting.get("post_migration_issues"),
            self.config.reporting.get("pmi_project_id")
        ]):
            return True

    def check_import_results(self, import_results):
        '''

        Take in an import_results, convert all successful imports + specfic fails to a list, and return it.

            :param import_results: (list) results of the last stage import in its raw form
            :return: (dict) containing just the names of the successful repos

        '''
        # removing reporting dict from import_results
        import_results.pop(-1)
        good_errors = ['Name has already been taken, Path has already been taken']
        successes = {}
        for result in import_results:
            for k, v in result.items():
                if result[k]['repository']:
                    successes[k.split('/')[1]] = None
                else:
                    if result[k]['response']['errors'] in good_errors:
                        successes[k.split('/')[1]] = None
        return successes

    def check_staged_projects(self, staged_projects, clean_data):
        '''

        Take a staged_projects and imported_projects, return all the pertinent stage data if its in imported_projects.

            :param staged_projects: (list) staged project data
            :param cleaned_data: (dict) succesfully imported or already existing projects
            :return: (dict) containing successful projects and its associated data

        '''

        for project in staged_projects:
            if project['name'] in clean_data:
                clean_data[project['name']] = project

        return clean_data

    def fix_issues(self):
        '''
        Add all the required details, using quick commands, to the end of an issues description. Currently this is only
        assigning the issue, and adding tasks to the end of the issue.

        '''

        # By the point this method gets called, everything required should be a class var
        for issue_id in self.reporting_issues[self.project['swc_id']].keys():
            # Oversimplifcations for readability
            description = self.reporting_issues[self.project['swc_id']][issue_id]['description']
            original_desc_len = len(description)
            assignees = self.reporting_issues[self.project['swc_id']][issue_id]['assignees']

            # Add assignee if needed
            if not self.check_existing_assignees(assignees, self.assignee) and self.assignee:
                description = self.modify_description(description, f"/assign {self.assignee}")

            # Add task with link to repo into issue if needed
            tasks = self.get_existing_tasks(description)
            if not self.check_existing_tasks(tasks, self.project['name']):
                newline = (
                    f"- [ ] [{self.project['name']}]"
                    f"({self.config.destination_host}/{self.project['target_namespace']}"
                    f"/{self.project['path_with_namespace']})"
                )
                description = self.modify_description(description, newline)
            else:
                self.log.info(f"The correct task: '{self.project['name']}' all ready existing in issue: '#{issue_id}'.")

            # finally, update the issue with our new and improved description
            if len(description) != original_desc_len:
                self.log.info(f"Issue: '#{issue_id}' description has been changed. Attempting to update.")
                data = {'description': description}
                r = self.update_issue(issue_id, data)

    def get_existing_tasks(self, description):
        '''
        Iterate over an issues description and return any tasks as a dict

            :param description: (str) issue description
            :return tasks: (list) a tasks repos name, status, and web url

        '''

        tasks = []
        # REGEX Explainer: 1st Capture Group(): status. 2nd Capture Group(): repo name. 3rd Capture Group(): repo url.
        # re.findall returns a list of tuples. Using a python (r)aw string to help with some of the character escaping.
        if issue_tasks := re.findall(r"^- \[(.)\] \[(.+)\]\((.+)\)", description, flags=re.MULTILINE):
            for task in issue_tasks:
                tasks.append({
                    'repo_name': task[1],
                    'status': 'closed' if task[0] == 'x' else 'opened',
                    'url': task[2]
                })

        return tasks

    def check_existing_tasks(self, tasks, repo_name):
        '''
        See if our repo has a task already, return True if so

            :param tasks: (list) a sanitized list of issue tasks
            :param repo: (string) a repos name we want to check if exists in tasks
            :return bool: (bool) return True if found

        '''
        for task in tasks:
            if task['repo_name'] == repo_name:
                return True

    def update_issue(self, issue_id, data):
        '''
        Use the IssuesApi to actually update the issue

        :param data: (dict) diction containing fields to update, usually just a description.
        :return: response object?

        '''
        if not self.dry_run:
            return self.issuesApi.update_issue(
                self.config.destination_host,
                self.config.destination_token,
                self.reporting_project_id,
                issue_id, data
            )

    def check_existing_assignees(self, assignees, username):
        '''
        Return True if assignee in the list assignees

            :param: assignees: (list) Assigned users list from an issue
            :param: username: (str) GitLab username to check
            :return: True if username found in assignees

        '''

        for user in assignees:
            if (user['username'] == username) and username:  # Meaning our username can't be None
                return True

    def modify_description(self, description, change):
        '''
        Returns a description with the change appended to a new line at the end of the description.

            :param description: (str) issue description (body).
            :param change: (str) a list of formatted strings appropriate for a GitLab issue markdown document.
            :return: (str) updated description

        '''

        description = description + f"\n{change}"
        return description

    def format_issue_data(self, issue_data):
        '''
        Clean up all the superfluous data and return a nice clean dict.

            :param issue_data: (dict) This should be all the messy data from either a newly created or existing issue.
                Meant to replace existing data with a smaller subset of data, saving or freeing memory.

        '''
        if issue_data:
            return {
                'url': issue_data['url'],
                'web_url': issue_data['web_url'],
                'state': issue_data['state'],
                'iid': issue_data['iid'],
                'description': issue_data['description'],
                'project_id': issue_data['project_id'],
                'assignees': issue_data['assignees'],
                'task_completion_status': issue_data['task_completion_status']
            }

    def subs_replace(self, var, description):
        '''
        Performs variable substitution on issue description, returning a new description.  Check the config first for a
        var. If its not found, check python variables.

            :param var: (str) A variable to look for.  Checking config first, followed by python variables
            :param description: (str) An issues description body, really messy with formatting usually.
            :return description: (str) an updated description with the vars replaced

        '''

        if var in self.config.reporting['subs']:
            description = description.replace(f"{{{{{var}}}}}", self.config.reporting['subs'][var])
        else:
            try:
                description = description.replace(f"{{{{{var}}}}}", str(eval(var)))
            except AttributeError:
                self.log.warning(f"Problem with REPORTING VAR: '{var}', it does not exist.")
        return description

    def check_substituions(self, description):
        '''
        find all occurences of pattern and create a list of them. Then call the subs_replace function and replace the
        pattern, then return the updated description.
        '''
        occurrences = re.findall("{{(.*?)}}", description)  # One or more matches in the line
        for var in occurrences:
            description = self.subs_replace(var, description)
        return description

    def check_existing_issues(self, new_issue):
        '''
        Check if the new_issue we are about to create already exists, return a dict of iid, state, url, web_url,
        description, and project_id.
        '''
        for e_issue in self.existing_issues:
            if str(new_issue) == str(e_issue['title']):
                self.log.info(
                    f"Will not create issue: '{new_issue}' because of: {e_issue['state']} '#{e_issue['iid']}'"
                )
                return {
                    'state': e_issue['state'],
                    'iid': e_issue['iid'],
                    'url': e_issue['_links']['self'],
                    'web_url': e_issue['web_url'],
                    'description': e_issue['description'],
                    'project_id': e_issue['project_id'],
                    'assignees': e_issue['assignees'],
                    'task_completion_status': e_issue['task_completion_status']
                }

        self.log.info(f"Will create issue: '{new_issue}'")

    def read_template_file(self, issue_filename):
        '''
        Check that the md template file exists, if so read it in and return it as a dict.
        The first line of the template file should be the title of the issue, followed by a blank line.
        '''
        with open(f'{self.app_path}/data/issue_templates/{issue_filename}') as f:
            data = f.readlines()
        return {'title': data[0].replace('#', '').strip(), 'description': ''.join(data[1:])}

    def get_project_issues(self):
        '''
        Get all the issues for our Reporting project, so we can check for duplicates later.
        Returns a json body if successful, none if not.
        '''
        issues = []
        for i in self.issuesApi.get_all_project_issues(
            self.reporting_project_id,
            self.config.destination_host,
            self.config.destination_token
        ):
            issues.append(i)
        return issues

    def create_issue(self, details, project_name):
        '''
        Creating an issue using the issues.py, for reporting purposes.
        The issue title will be created using project_name, and the issue description will be filled in with details.
        Returns a json body if successful, None if not.
        '''
        message = "Will Create"
        if not self.dry_run:
            created_issue = safe_json_response(
                self.issuesApi.create_issue(
                    self.config.destination_host,
                    self.config.destination_token,
                    self.reporting_project_id,
                    title=f"{project_name.upper()} | {details['title']}",
                    description=details['description']
                )
            )
            message = "Created"
            # Remapping for convenience
            created_issue['url'] = created_issue['_links']['self']
        else:
            created_issue = None

        self.log.info(f"{message} issue: {project_name.upper()} | {details['title']}")

        return created_issue
