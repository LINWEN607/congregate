class Level(object):

    def __init__(self, value):
        self.value = value
        self.gitlab_api_bridge = self.map_level_to_gitlab_api()
        self.bitbucket_level_name = self.get_bitbucket_level_name()
        self.gitlab_level_name = self.get_gitlab_level_name()

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        valid_values = [
            'bitbucket_repo',
            'bitbucket_project'
        ]
        assert value in valid_values
        self._value = value

    def map_level_to_gitlab_api(self):
        if self.value == 'bitbucket_repo':
            return 'projects'
        elif self.value == 'bitbucket_project':
            return 'groups'

    def get_bitbucket_level_name(self):
        if self.value == 'bitbucket_repo':
            return 'Bitbucket repository'
        elif self.value == 'bitbucket_project':
            return 'Bitbucket project'

    def get_gitlab_level_name(self):
        if self.value == 'bitbucket_repo':
            return 'GitLab project'
        elif self.value == 'bitbucket_project':
            return 'GitLab group'

    def get_level_name(self):
        return '%s/%s' % (self.get_bitbucket_level_name(), self.get_gitlab_level_name())
