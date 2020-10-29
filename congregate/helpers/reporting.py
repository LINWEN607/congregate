from congregate.helpers.base_class import BaseClass
from congregate.migration.gitlab.api.issues import IssuesApi
import re


class Reporting(BaseClass):
    def __init__(self, project_id=1, project_name='test'):
        self.project_id = project_id
        self.issuesApi = IssuesApi()
        self.templates = []
        super(Reporting, self).__init__()
        self.existing_issues = self.get_project_issues()

        self.new_issues = []
        for issue in self.config.reporting['post_migration_issues']:
            self.new_issues.append(self.read_template_file(issue))

        for issue in self.new_issues:
            self.get_issue_keys(issue['description'])
            issue['description'] = self.get_issue_keys(issue['description'])
            if not self.check_existing_issues(f"{project_name.upper()} | {issue['title']}"):
                r = self.create_issue(issue, project_name)

    def subs_replace(self, key, description):
        '''
        iterate over the details of an issue and do any variable substitution.  Return a new details.
        '''
        if key in self.config.reporting['subs']:
            description = description.replace(f"{{{{{key}}}}}", self.config.reporting['subs'][key])
        else:
            try:
                description = description.replace(f"{{{{{key}}}}}", str(eval(key)))
            except AttributeError:
                self.log.warn(f"Problem with VAR: '{key}', it does not exist.")
        return description

    def get_issue_keys(self, description):
        '''
        find all occurences of pattern and create a list of them. Then call the subs_replace function and replace the
        pattern, then return the updated description.
        '''
        occurrences = re.findall("{{(.*?)}}", description)  # One or more matches in the line
        for key in occurrences:
            description = self.subs_replace(key, description)
        return description

    def check_existing_issues(self, new_issue):
        '''
        Check if the new_issue we are about to create already exists, return true if so.
        '''
        for e_issue in self.existing_issues:
            if str(new_issue) == str(e_issue['title']):
                return True

    def read_template_file(self, issue_filename):
        '''
        Check that the md template file exists, if so read it in and return it as a dict.
        The first line of the template file should be the title of the issue, followed by a blank line.
        '''
        with open(f'{self.app_path}/data/issue_templates/{issue_filename}') as f:
            data = f.readlines()
        return {'title': data[0].rstrip(), 'description': ''.join(data[1:])}

    def get_project_issues(self):
        '''
        Get all the issues for our Reporting, so we can check for duplicates later.
        Returns a json body if successful, none if not.
        '''
        issues = []
        for i in self.issuesApi.get_all_project_issues(
            self.project_id,
            self.config.destination_host,
            self.config.destination_token
        ):
            issues.append(i)
        return issues

    def create_issue(self, details, project_name):
        '''
        Creating an issue using the issues.py, for reporting purposes.
        The issue title will be created using project_name, and the issue description will be filled in with details.
        Returns a json body if successful, none if not.
        '''
        r = self.issuesApi.create_issue(
            self.config.destination_host,
            self.config.destination_token,
            self.project_id,
            title=f"{project_name.upper()} | {details['title']}",
            description=details['description']
        )
        if r.status_code == 201:
            return r.json()


def main():
    test = Reporting(project_id=1, project_name=None)
    for i in test.templates:
        print(i['title'])
        print(i['description'])


if __name__ == "__main__":  # Python file ran directly, and not just imported
    main()
