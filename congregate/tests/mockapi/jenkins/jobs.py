from collections import OrderedDict

class JenkinsJobsApi():
    def get_job_config_xml(self):
        return """
            <project>
            <actions/>
            <description/>
            <keepDependencies>false</keepDependencies>
            <properties>
                <com.dabsquared.gitlabjenkins.connection.GitLabConnectionProperty plugin="gitlab-plugin@1.5.13">
                <gitLabConnection/>
                </com.dabsquared.gitlabjenkins.connection.GitLabConnectionProperty>
                <org.jenkinsci.plugins.gitlablogo.GitlabLogoProperty plugin="gitlab-logo@1.0.5">
                <repositoryName/>
                </org.jenkinsci.plugins.gitlablogo.GitlabLogoProperty>
                <hudson.model.ParametersDefinitionProperty>
                <parameterDefinitions>
                    <hudson.model.BooleanParameterDefinition>
                    <name>boolean_parameter</name>
                    <description/>
                    <defaultValue>true</defaultValue>
                    </hudson.model.BooleanParameterDefinition>
                    <com.cloudbees.plugins.credentials.CredentialsParameterDefinition plugin="credentials@2.3.12">
                    <name>demo-job secret text</name>
                    <description/>
                    <defaultValue>global_secret</defaultValue>
                    <credentialType>org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl</credentialType>
                    <required>false</required>
                    </com.cloudbees.plugins.credentials.CredentialsParameterDefinition>
                </parameterDefinitions>
                </hudson.model.ParametersDefinitionProperty>
            </properties>
            <scm class="hudson.plugins.git.GitSCM" plugin="git@4.3.0">
                <configVersion>2</configVersion>
                <userRemoteConfigs>
                <hudson.plugins.git.UserRemoteConfig>
                    <url>https://github.gitlab-proserv.net/firdaus/gitlab-jenkins.git</url>
                    <credentialsId>gitlabgithub</credentialsId>
                </hudson.plugins.git.UserRemoteConfig>
                </userRemoteConfigs>
                <branches>
                <hudson.plugins.git.BranchSpec>
                    <name>*/master</name>
                </hudson.plugins.git.BranchSpec>
                </branches>
                <doGenerateSubmoduleConfigurations>false</doGenerateSubmoduleConfigurations>
                <submoduleCfg class="list"/>
                <extensions/>
            </scm>
            <canRoam>true</canRoam>
            <disabled>false</disabled>
            <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
            <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
            <triggers/>
            <concurrentBuild>false</concurrentBuild>
            <builders/>
            <publishers/>
            <buildWrappers/>
            </project>
        """

    def get_job_config_dict(self):
        return {'project': OrderedDict([('actions', None),
                                        ('description', None),
                                        ('keepDependencies', False),
                                        ('properties',
                                         OrderedDict([('com.dabsquared.gitlabjenkins.connection.GitLabConnectionProperty',
                                                       OrderedDict([('@plugin',
                                                                     'gitlab-plugin@1.5.13'),
                                                                    ('gitLabConnection',
                                                                     None)])),
                                                      ('org.jenkinsci.plugins.gitlablogo.GitlabLogoProperty',
                                                       OrderedDict([('@plugin',
                                                                     'gitlab-logo@1.0.5'),
                                                                    ('repositoryName',
                                                                     None)])),
                                                      ('hudson.model.ParametersDefinitionProperty',
                                                       OrderedDict([('parameterDefinitions',
                                                                     OrderedDict([('hudson.model.BooleanParameterDefinition',
                                                                                   OrderedDict([('name',
                                                                                                 'boolean_parameter'),
                                                                                                ('description',
                                                                                                 None),
                                                                                                ('defaultValue',
                                                                                                 True)])),
                                                                                  ('com.cloudbees.plugins.credentials.CredentialsParameterDefinition',
                                                                                   OrderedDict([('@plugin',
                                                                                                 'credentials@2.3.12'),
                                                                                                ('name',
                                                                                                 'demo-job '
                                                                                                 'secret '
                                                                                                 'text'),
                                                                                                ('description',
                                                                                                 None),
                                                                                                ('defaultValue',
                                                                                                 'global_secret'),
                                                                                                ('credentialType',
                                                                                                 'org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl'),
                                                                                                ('required',
                                                                                                 False)]))]))]))])),
                                        ('scm',
                                         OrderedDict([('@class', 'hudson.plugins.git.GitSCM'),
                                                      ('@plugin', 'git@4.3.0'),
                                                      ('configVersion', '2'),
                                                      ('userRemoteConfigs',
                                                       OrderedDict([('hudson.plugins.git.UserRemoteConfig',
                                                                     OrderedDict([('url',
                                                                                   'https://github.gitlab-proserv.net/firdaus/gitlab-jenkins.git'),
                                                                                  ('credentialsId',
                                                                                   'gitlabgithub')]))])),
                                                      ('branches',
                                                       OrderedDict([('hudson.plugins.git.BranchSpec',
                                                                     OrderedDict([('name',
                                                                                   '*/master')]))])),
                                                      ('doGenerateSubmoduleConfigurations',
                                                       False),
                                                      ('submoduleCfg',
                                                       OrderedDict([('@class', 'list')])),
                                                      ('extensions', None)])),
                                        ('canRoam', True),
                                        ('disabled', False),
                                        ('blockBuildWhenDownstreamBuilding', False),
                                        ('blockBuildWhenUpstreamBuilding', False),
                                        ('triggers', None),
                                        ('concurrentBuild', False),
                                        ('builders', None),
                                        ('publishers', None),
                                        ('buildWrappers', None)])}
