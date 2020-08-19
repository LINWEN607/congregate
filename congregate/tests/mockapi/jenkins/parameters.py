class ParametersApi():
    def get_parameters(self):
        return [
            {
                '_class': 'hudson.model.BooleanParameterDefinition',
                'defaultParameterValue': {
                    '_class': 'hudson.model.BooleanParameterValue',
                    'name': 'Boolean Parameter',
                    'value': True
                },
                'description': "Value is 'true'",
                'name': 'Boolean Parameter',
                'type': 'BooleanParameterDefinition'
            },
            {
                '_class': 'hudson.model.ChoiceParameterDefinition',
                'defaultParameterValue': {
                    '_class': 'hudson.model.StringParameterValue',
                    'name': 'Choice Parameter',
                    'value': 'choice 1'
                },
                'description': 'Contains two choice parameters',
                'name': 'Choice Parameter',
                'type': 'ChoiceParameterDefinition',
                'choices': [
                    'choice 1',
                    'choice 2',
                    '3 choice',
                    'other choice',
                    '',
                    '^ blank choice'
                ]
            },
            {
                '_class': 'com.cloudbees.plugins.credentials.CredentialsParameterDefinition',
                'defaultParameterValue': {
                    '_class': 'com.cloudbees.plugins.credentials.CredentialsParameterValue',
                    'name': 'Credentials Parameter '
                },
                'description': "Secret Text type: contains default value for 'Jenkins global secret'",
                'name': 'Credentials Parameter ',
                'type': 'CredentialsParameterDefinition'
            },
            {
                '_class': 'hudson.model.FileParameterDefinition',
                'defaultParameterValue': None,
                'description': "file param value of '/some/location/here'",
                'name': '/some/location/here',
                'type': 'FileParameterDefinition'
            },
            {
                '_class': 'hudson.model.TextParameterDefinition',
                'defaultParameterValue': {
                    '_class': 'hudson.model.StringParameterValue',
                    'name': 'ML string param',
                    'value': 'line 1\nline 2\n\nline 4'
                },
                'description': 'Line 3 left blank intentionally',
                'name': 'ML string param',
                'type': 'TextParameterDefinition'
            },
            {
                '_class': 'hudson.model.PasswordParameterDefinition',
                'defaultParameterValue': {
                    '_class': 'hudson.model.PasswordParameterValue',
                    'name': 'password param'
                },
                'description': 'value is password',
                'name': 'password param',
                'type': 'PasswordParameterDefinition'
            },
            {
                '_class': 'hudson.model.StringParameterDefinition',
                'defaultParameterValue': {
                    '_class': 'hudson.model.StringParameterValue',
                    'name': 'string param',
                    'value': 'string'
                },
                'description': 'value is string',
                'name': 'string param',
                'type': 'StringParameterDefinition'
            },
            {
                '_class': 'hudson.model.StringParameterDefinition',
                'defaultParameterValue': {
                    '_class': 'hudson.model.StringParameterValue',
                    'name': 'string param',
                    'value': 'string2'
                },
                'description': 'value for string2',
                'name': 'string param',
                'type': 'StringParameterDefinition'
            },
            {
                '_class': 'net.uaznia.lukanus.hudson.plugins.gitparameter.GitParameterDefinition',
                'defaultParameterValue': {
                    '_class': 'net.uaznia.lukanus.hudson.plugins.gitparameter.GitParameterValue',
                    'name': 'Git Parameter',
                    'value': 'origin/master'
                },
                'description': 'param type tag',
                'name': 'Git Parameter',
                'type': 'PT_TAG'
            },
            {
                '_class': 'hudson.model.RunParameterDefinition',
                'defaultParameterValue': None,
                'description': 'project descripiton',
                'name': 'run parameter',
                'type': 'RunParameterDefinition',
                'filter': 'ALL',
                'projectName': 'project'
            }
        ]

    def get_single_parameter(self):
        return {
            '_class': 'hudson.model.BooleanParameterDefinition',
            'defaultParameterValue': {
                '_class': 'hudson.model.BooleanParameterValue',
                'name': 'Boolean Parameter',
                'value': True
            },
            'description': "Value is 'true'",
            'name': 'Boolean Parameter',
            'type': 'BooleanParameterDefinition'
        }

    def get_single_parameter_no_default_param(self):
        return {
            '_class': 'hudson.model.RunParameterDefinition',
            'defaultParameterValue': None,
            'description': 'project descripiton',
            'name': 'run parameter',
            'type': 'RunParameterDefinition',
            'filter': 'ALL',
            'projectName': 'project'
        }