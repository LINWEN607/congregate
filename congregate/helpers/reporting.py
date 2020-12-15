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

    def handle_creating_issues(self, staged_projects, import_results):
        '''
        Do the needful. Check/Create issues, assign tasks, etc...

        >>> ri = Reporting(reporting_project_id, project)
        >>> ri.handle_creating_issues()
        >>> ri.reporting_issues # saving this data in case we want to use it later
        {issue_iid: {'iid': 345, 'title', 'some title'}, issue_iid: {'iid': 345, 'title', 'some title'}}

        '''

        self.template_issues = []
        self.reporting_issues = {}  # The issues this class will return

        # Read our configuration template_issues in
        for issue in self.config.reporting['post_migration_issues']:
            i = self.read_template_file(issue)
            i['description'] = self.check_substitutions(i['description'])
            self.template_issues.append(i)

        # making an issues data strucuture, building off previous structures
        combined_data = self.combine_wave_data(staged_projects, import_results)
        self.existing_issues = self.combine_existing_issues()
        combined_issues = self.create_new_combined_issues(combined_data['issues'], self.existing_issues)

        # Some stats ahead of time
        stats = {
            'total_projects': len(combined_data),
            'total_issues': len(combined_issues),
            'existed': 0,
            'changed': 0,
            'create': 0
        }
        for issue in combined_issues:
            if not combined_issues[issue]['status']['exists']:
                stats['create'] += 1
            elif combined_issues[issue]['status']['changed']:
                stats['changed'] += 1
            elif combined_issues[issue]['status']['exists']:
                stats['existed'] += 1

        self.log.info(f"\n{'*' * 80}\n{'*' * 80}\n\n")
        for stat in stats:
            self.log.info(f"REPORTING: {stat}: {stats[stat]}")
        self.log.info(f"\n{'*' * 80}\n{'*' * 80}\n")

        # Do it
        progress = {'total': len(combined_issues), 'current': 0}
        for issue in combined_issues:
            # Create an issue
            if not combined_issues[issue]['status']['exists']:
                progress['current'] += 1
                self.log.info(f"Creating issue: '{issue}' Progress: [ {progress['current']} / {progress['total']} ]")
                data = {'title': issue, 'description': combined_issues[issue]['description']}
                self.create_issue(data)
            # Update an issue
            elif combined_issues[issue]['status']['changed']:
                progress['current'] += 1
                self.log.info(f"Updating issue: '{issue}' Progress: [ {progress['current']} / {progress['total']} ]")
                data = {'description': combined_issues[issue]['description']}
                r = self.update_issue(combined_issues[issue]['status']['exists'], data)
            # Nothing to see here, move along
            else:
                progress['current'] += 1
                self.log.info(f"No changes for issue: '{issue}' Progress: [ {progress['current']} / {progress['total']} ]")

    def create_new_combined_issues(self, new_data, exst_data):
        '''
        Take our new data and our existing data, and combine them as required.  Returning a new issues dict with
        any updates or creations we need to do.

        :param new_data: (dict) Our existing combined data, as created from staged_data import_results.
        :param exst_data: (dict) Existing GitLab issue data from the GitLab instance.
        :return combined_issues: (dict) Combined dict with whether or not we need to create or update issue.

        '''

        for issue in new_data:
            new_data[issue]['status'] = {'exists': None, 'changed': None}
            if issue in exst_data:
                new_data[issue]['status']['exists'] = exst_data[issue]['iid']
                if not new_data[issue]['assignees'] == exst_data[issue]['assignees']:
                    # stupid hack so I can goto bed. Equality on a list of dicts only works if the list is in the same order.
                    nusers = []
                    for new_user in new_data[issue]['assignees']:
                        nusers.append(new_user['name'])
                    ousers = []
                    for old_user in exst_data[issue]['assignees']:
                        ousers.append(old_user['name'])
                    if not (ousers.sort() == nusers.sort()):
                        # Readability Simplification
                        new = new_data[issue]['assignees']
                        old = exst_data[issue]['assignees']
                        # replacing our new assignees list with users that aren't in existing assignees
                        new = [user for user in new if user not in old]
                        new_data[issue]['status']['changed'] = True
                else:
                    # No changes to make, so we empty the list, I feel like this should be handled differently
                    new_data[issue]['assignees'] = []
                # Get the required tasks
                new_data[issue]['tasks'] = self.check_existing_tasks(new_data[issue]['tasks'], exst_data[issue]['tasks'])
                if new_data[issue]['tasks']:
                    new_data[issue]['status']['changed'] = True
                # Use the existing description
                new_data[issue]['description'] = exst_data[issue]['description']

        # Now that our data is all munged up, lets go ahead and change descriptions if needed
        for issue in new_data:
            # Tasks first
            for task in new_data[issue]['tasks']:
                newline = f"- [ ] [{task['repo_name']}]({task['url']})"
                new_data[issue]['description'] += f"\n{newline}"

            # Now assignees
            for assignee in new_data[issue]['assignees']:
                new_data[issue]['description'] += f"\n/assign {assignee['name']}"

        return new_data

    def combine_existing_issues(self):
        '''
        Get EXISTING issues, and put it in a format similar to what our combined_data looks like. Add tasks and
        assignees lists split out into its own key in the existing dict.

        :return existing: (dict) existing issues, formatted similar to our combined data.
        '''
        # Get any existing issues
        existing = self.get_project_issues()
        for issue in existing:
            existing[issue]['tasks'] = self.get_existing_tasks(existing[issue]['description'])

        return existing

    def combine_wave_data(self, staged_projects, import_results):
        '''
        Take staged_projects and import_results, combine them, and return the resulting successful dataset

        :param staged_projects: (str) The staged projects used in our migration
        :param import_results: (str) The results of our migration
        :return: (dict) A dictionary of the successful results, keyed off repo.

        '''
        clean_data = {}
        # Raw projects
        clean_data['projects'] = self.check_import_results(import_results)
        # Combine with successful projects.  This limits us to only successful projects
        clean_data['projects'] = self.check_staged_projects(staged_projects, clean_data['projects'])
        # Create the email to username map
        clean_data['users_map'] = self.create_users_map_from_data(clean_data['projects'])
        # Create our issues
        clean_data['issues'] = self.create_issues_from_data(clean_data, self.template_issues)

        return clean_data

    def create_issues_from_data(self, clean_data, template_issues):
        '''
        Create issues using supplied project data

        :param clean_data: (dict) dict of successful projects and users
        :return issues: (dict) new dict of issues keyed on title

        '''
        req_issues = {}
        # readability simplification
        projects = clean_data['projects']

        for _, project in projects.items():
            # readability simplifications
            if isinstance(project, dict) and project.get('swc_manager_email'):
                email = project['swc_manager_email']
                uname = clean_data['users_map'].get(email)
                task = {
                    'repo_name': project['name'],
                    'status': None
                }
                if project.get("target_namespace"):
                    task['url'] = f"{self.config.destination_host}/{project['target_namespace']}/{project['path_with_namespace']}"
                else:
                    task['url'] = f"{self.config.destination_host}/{project['path_with_namespace']}"

                for issue in template_issues:
                    cur_title = f"{project['swc_id']} | {issue['title']}"
                    cur_desc = issue['description']
                    # Does our issue already exist in the dataset, if not create it with current assignee and task
                    if cur_title not in req_issues:
                        req_issues[cur_title] = {'assignees': [{'name': uname}], 'tasks': [task], 'description': cur_desc}
                    else:
                        req_issues[cur_title]['tasks'].append(task)
                        # Making sure username exists, and its not already in the list of assignees, add it
                        if (uname) and not any(u['name'] == uname for u in req_issues[cur_title]['assignees']):
                            req_issues[cur_title]['assignees'].append({'name': uname})
            else:
                self.log.warning("Unable to create issue due to missing SWC manager email. Check your staged_projects.json")

        return req_issues

    def create_users_map_from_data(self, projects):
        '''
        Check if our email has a GitLab username or not. Return a dict containing the map of username to gitlab name

        :param projects: (dict) successful migrated project data
        :return users_map: (dict) dict keys: users values: gitlab username

        '''

        progress = {'total': len(projects), 'current': 0}
        users_map = {}

        for _, project in projects.items():
            if isinstance(project, dict):
                email = project.get('swc_manager_email')
                # Did the staged project have a customer defined email and is it already mapped?
                if email and email not in users_map:
                    # Did we get a username back from the GitLab instance?
                    if uname := self.usersClient.find_user_by_email_comparison_without_id(email):
                        users_map[email] = uname['username']
                        progress['current'] += 1
                        self.log.info(
                            f"Found username: '{uname['username']}' for email: '{email}' Progress: "
                            f"[ {progress['current']} / {progress['total']} ]"
                        )
                    else:
                        # No username for a given user, still adding it, so we don't repeat an API call
                        users_map[email] = None
                        progress['current'] += 1
                        self.log.warning(
                            f"No username found for '{email}' Progress: [ {progress['current']} / {progress['total']} ]"
                        )
                elif email in users_map:
                    progress['current'] += 1
                    self.log.info(
                        f"User '{users_map[email]}' existed. No need to look it up again. Progress: [ {progress['current']} / {progress['total']} ]"
                    )
                else:
                    # No email in the staged project
                    progress['current'] += 1
                    self.log.warning(
                        f"No email staged found for '{projects[project]['name']}' "
                        f"Progress: [ {progress['current']} / {progress['total']} ]"
                    )
            else:
                self.log.warning("""
                    Unable to add user to map due to malformed project found. 
                    Check project_migration_results.json or staged_projects.json
                """)

        return users_map

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

    def check_existing_tasks(self, new, old):
        '''
        See if our repo has a task already, return True if so

            :param new: (list) Tasks created from staged_projects
            :param old: (list) Tasks pulled from existing issues on GitLab instance
            :return required: (list) Return a list of new tasks that don't exist in old tasks

        '''

        not_required = []
        required_tasks = new.copy()
        # Find any tasks that exist in old
        old_repo_names = [o['repo_name'] for o in old]
        not_required = [
            i for i in new if i['repo_name'] in old_repo_names
        ]

        for d in not_required:
            required_tasks.remove(d)

        return required_tasks


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

    def modify_description(self, description, change):
        '''
        Returns a description with the change appended to a new line at the end of the description.

            :param description: (str) issue description (body).
            :param change: (str) a list of formatted strings appropriate for a GitLab issue markdown document.
            :return: (str) updated description

        '''
        if change:
            description = description + f"\n{change}"
        return description

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
            except NameError as e:
                self.log.warning(f"Problem with REPORTING VAR: {e}")
        return description

    def check_substitutions(self, description):
        '''
        find all occurences of pattern and create a list of them. Then call the subs_replace function and replace the
        pattern, then return the updated description.
        '''
        occurrences = re.findall("{{(.*?)}}", description)  # One or more matches in the line
        for var in occurrences:
            description = self.subs_replace(var, description)
        return description

    def format_assignees(self, assignees):
        '''
        Take in a list of dicts of a gitlab assignee, and return only the data we are interested in

        :param assignees: (list) issue api call for assignees.
        return users: (list) stripped down dict to just gitlab username
        '''
        # I should probably do something else here. This is so basic. Maybe something with pop, or list comprehension.
        users = []
        for assignee in assignees:
            users.append({'name': assignee['username']})
        return users

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
        clean_issues = {}

        for issue in self.issuesApi.get_all_project_issues(
            self.reporting_project_id,
            self.config.destination_host,
            self.config.destination_token
        ):
            clean_issues[issue['title']] = {
                'url': issue['_links']['self'],
                'web_url': issue['web_url'],
                'state': issue['state'],
                'iid': issue['iid'],
                'description': issue['description'],
                'project_id': issue['project_id'],
                'assignees': self.format_assignees(issue['assignees']),
                'task_completion_status': issue['task_completion_status']
            }

        return clean_issues

    def create_issue(self, details):
        '''
        Creating an issue using the issues.py, for reporting purposes.
        The issue title will be created using project_name, and the issue description will be filled in with details.
        Returns a json body if successful, None if not.
        '''

        if not self.dry_run:
            created_issue = safe_json_response(
                self.issuesApi.create_issue(
                    self.config.destination_host,
                    self.config.destination_token,
                    self.reporting_project_id,
                    title=f"{details['title']}",
                    description=details['description']
                )
            )
