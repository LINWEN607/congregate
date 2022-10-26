from time import sleep
from os.path import exists
from os import getenv
import requests
from jenkins import Jenkins

def formatted_message(message, resp):
    fmt_message = f"\n{message}\n{resp.status_code}\n"
    if resp.status_code != 200:
        fmt_message = f"\n{message}\n{resp.status_code}: {resp.text}\n"
    return fmt_message


def formatted_url(endpoint):
    url_base = "http://localhost:8080"
    return f"{url_base}/{endpoint}"


def setup_jenkins():
    s = requests.Session()

    while not exists("/var/jenkins_home/secrets/initialAdminPassword"):
        print("Waiting to retrieve password")
        sleep(1)

    with open("/var/jenkins_home/secrets/initialAdminPassword", "r") as f:
        password = (f.read()).rstrip()

    s.auth = ('admin', password)

    while True:
        resp = s.get(formatted_url('crumbIssuer/api/json'))
        print(formatted_message("Crumb", resp))
        if resp.status_code != 200:
            print("Waiting for jenkins to start")
            sleep(1)
        else:
            break

    # Retrieving crumb to retain initial session
    crumb = s.get(formatted_url('crumbIssuer/api/json')).json()['crumb']

    # Logging in to jenkins
    login = s.post(formatted_url('login'), data={
        'Jenkins-Crumb': crumb,
        'j_username': 'admin',
        'j_password': password
    })

    print(formatted_message("Logging in", login))

    suggested_plugins = [
        "cloudbees-folder",
        "antisamy-markup-formatter",
        "workflow-aggregator",
        "build-timeout",
        "credentials-binding",
        "timestamper",
        "ws-cleanup",
        "ant",
        "gradle",
        "github-branch-source",
        "pipeline-github-lib",
        "pipeline-stage-view",
        "git",
        "subversion",
        "ssh-slaves",
        "matrix-auth",
        "pam-auth",
        "ldap",
        "email-ext",
        "mailer",
        "multiple-scms",
        "gitlab-plugin"
    ]

    # Not needed currently, but it will return a list of all the jenkins plugins available
    # getPlugins = s.get(formatted_url('pluginManager/plugins'))
    # print(formatted_message("Get plugins", getPlugins))

    # Installing suggested list of plugins
    # for plugin in suggested_plugins:
    #     plugin_name = f"plugin.{plugin}"
    #     installPlugins = s.post(formatted_url(f"pluginManager/install?{plugin_name}=true"),
    #                             data={
    #         "dynamicLoad": True,
    #         "Jenkins-Crumb": crumb
    #     }
    #     )

    #     print(formatted_message(
    #         f"Installing plugin {plugin_name}", installPlugins))

    # # Since the plugin requests above just trigger the install, the actual install is not completed
    # # before a response is returned
    # print("Waiting 60 seconds before continuing to get plugins installed")
    # sleep(60)

    # Create new admin user
    createAdmin = s.post(formatted_url('setupWizard/createAdminUser'), data={
        "username": "test-admin",
        "password1": "password",
        "password2": "password",
        "fullname": "test admin",
        "email": "test@email.com",
        "Jenkins-Crumb": crumb
    })

    print(formatted_message("Creating Admin User", createAdmin))

    # Changing authentication to new admin user
    s.auth = ('test-admin', 'password')
    # Retrieving new session crumb
    crumb = s.get(formatted_url('crumbIssuer/api/json')).json()['crumb']

    # Setting rootUrl. Note this will still throw a warrning in the UI
    configureInstance = s.post(formatted_url('setupWizard/configureInstance'), data={
        "rootUrl": "http://localhost:8080",
        "Jenkins-Crumb": crumb
    })

    print(formatted_message("Configuring instance", configureInstance))

    # Mark the installation as complete
    resp = s.post(formatted_url('setupWizard/completeInstall'), data={
        "Jenkins-Crumb": crumb
    })

    print(formatted_message("Completing install", resp))

    if getenv('SEED_DATA') == "true" and not exists("/var/jenkins_home/seed-finished"):
        seed_data()
    else:
        print("Skipping seed_data")

    # Mark the installation as complete
    # resp = s.post(formatted_url('restart'), data={
    #     "Jenkins-Crumb": crumb
    # })

    # print(formatted_message("Restarting jenkins and waiting 60 seconds", resp))

    # sleep(60)

    # Write a file to check if jenkins is already set up
    with open("/var/jenkins_home/install-finished", "w") as f:
        f.write("install complete")


def seed_data():
    print("Logging in to Jenkins to seed data")
    j = Jenkins("http://localhost:8080", "test-admin", "password")

    print("Creating job test-job")
    j.create_job("test-job", """
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
        <url>https://github.example.net/firdaus/gitlab-jenkins.git</url>
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
    """)

    print("Creating job freestyle-job")
    j.create_job("freestyle-job", """
        <project>
        <keepDependencies>false</keepDependencies>
        <properties/>
        <scm class="hudson.scm.NullSCM"/>
        <canRoam>false</canRoam>
        <disabled>false</disabled>
        <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
        <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
        <triggers/>
        <concurrentBuild>false</concurrentBuild>
        <builders/>
        <publishers/>
        <buildWrappers/>
        </project>
    """)

    print("Creating job scm-info-job")
    j.create_job("scm-info-job", """
        <project>
        <description/>
        <keepDependencies>false</keepDependencies>
        <properties>
        <com.dabsquared.gitlabjenkins.connection.GitLabConnectionProperty plugin="gitlab-plugin@1.5.13">
        <gitLabConnection/>
        </com.dabsquared.gitlabjenkins.connection.GitLabConnectionProperty>
        <org.jenkinsci.plugins.gitlablogo.GitlabLogoProperty plugin="gitlab-logo@1.0.5">
        <repositoryName/>
        </org.jenkinsci.plugins.gitlablogo.GitlabLogoProperty>
        </properties>
        <scm class="hudson.plugins.git.GitSCM" plugin="git@4.3.0">
        <configVersion>2</configVersion>
        <userRemoteConfigs>
        <hudson.plugins.git.UserRemoteConfig>
        <url>https://github.example.net/firdaus/scm-info-repo.git</url>
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
    """)

    # Write a file to check if jenkins is already set up
    with open("/var/jenkins_home/seed-finished", "w") as f:
        f.write("install complete")


if __name__ == "__main__":
    if not exists("/var/jenkins_home/install-finished"):
        setup_jenkins()
    else:
        print("Jenkins is already setup. Skipping")
