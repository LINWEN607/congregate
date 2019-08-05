#!groovy

def pipelineStatus = '0'

// Jenkins agent
def agentLabel = 'GTS.H32V.L52.Migration'

// Use to store values from config.json
def MY_JOB_CONFIG = []

// command parameter
def commandChoices = ['migrate'].join("\n")
def commandDescription = """
Select an ondemand flow:
<ul>
<li><b>migrate</b>: migrate an entire BitBucket project or a single git repo, then verify that the migration is succesful</li>
</ul>
"""

def repoOrProject = ['Project', 'Repository'].join("\n")
def repoOrProjectDescription = """
<ul>
<li>Project: to run the migration job for every repository within the project. Use the Project url from the web browser.</li>
<li>Repository: to run the migration job for a single repo. Use the https clone url.</li>
</ul>
"""

// url parameter
def urlDescription = '''
URL of the onestash.verizon.com project to migrate.
'''
def urlDefaultValue = 'https://onestash.verizon.com/projects/MDMIG'

// environment parameter
def envDescription = '''
<ul>
<li>Prod Gitlab: https://gitlab.verizon.com</li>
</ul>
'''
def envChoices = ['prod'].join("\n")


pipeline {
  agent {
    label agentLabel
  }
  environment {
    BITBUCKET_SERVER = 'https://onestash.verizon.com'
    GITLAB_SERVER = 'https://gitlab.verizon.com'
    CONGREGATE_PATH = "${env.WORKSPACE}/etc"
    CONGREGATE_SRC = "${env.WORKSPACE}/src"
  }
  options {
    buildDiscarder(
      logRotator(
        daysToKeepStr: '90',
        artifactDaysToKeepStr: '90',
      )
    )
    timestamps()
  } //end of options
  parameters {
    choice(
      name: 'command',
      description: commandDescription,
      choices: commandChoices,
    )
    choice(
      name: 'repoOrProject',
      description: repoOrProjectDescription,
      choices: repoOrProject,    
    )
    string(
      name: 'url',
      description: urlDescription,
      defaultValue: urlDefaultValue,
    )
    choice(
      name: 'environment',
      description: envDescription,
      choices: envChoices,
    )
  } //end of parameters
  stages {
    stage('configure job') {
      steps {
        dir(env.CONGREGATE_SRC) {
          checkout([
            $class: 'GitSCM',
            branches: [[name: env.GIT_BRANCH]],
            doGenerateSubmoduleConfigurations: false,
            extensions: [[$class: 'LocalBranch'],[$class: 'WipeWorkspace']],
            submoduleCfg: [],
            userRemoteConfigs: [[
              credentialsId: '3e1417f1-8622-4b9f-8840-0de9e55c6cc9',
              url: 'git@gitlab.verizon.com:H32V-SCM-Services/GitlabMigration.git'
            ]]
          ])
        }
        dir("${env.CONGREGATE_PATH}/data") {
          sh """
            aws s3 cp s3://vz-app-gts-celv-prod-gitlab-secrets-west-s3bucket/config_${params.environment}.json config.json
          """
          script {
            MY_JOB_CONFIG = readJSON file: 'config.json'
            env.GITLAB_SERVER = MY_JOB_CONFIG.config.destination_instance_host
          }
        }
      }
    }
    stage('migrate') {
      when {
        expression {
          return params.command == 'migrate'
        }
      }
      steps {
        dir(env.CONGREGATE_SRC) {
          wrap([$class: 'BuildUser']) {
            script {
              pipelineStatus = sh(
                script: """
                  python jenkinsjob.py ondemand migrate_to_gitlab ${params.repoOrProject} ${params.url}
                """,
                returnStatus: true
              )
              if (pipelineStatus == "0" || pipelineStatus == 0) {
                currentBuild.result = 'SUCCESS'
              }
              else if (pipelineStatus == "1" || pipelineStatus == 1) {
                currentBuild.result = 'FAILURE'
              }
              else if (pipelineStatus == "2" || pipelineStatus == 2) {
                currentBuild.result = 'UNSTABLE'
              }
              else {
                currentBuild.result = 'FAILURE'
              }
            }
          }
        }
      }
    }
  } //end of stages
  post {
    failure {
      emailext(
        subject: 'Your migration cannot be completed.',
        recipientProviders: [[$class: 'RequesterRecipientProvider']],
        mimeType: 'text/html',
        body: """
<p>
Something went wrong with the migration job for <b>${params.url}</b>.

Click <a href='${env.RUN_DISPLAY_URL}'>here</a> to review the job output and details about the failure.
</p>
<p>
Find out more about GitLab at Verizon,
<ul>
 <li>
 Search <a href='https://cloudsearch.verizon.com/?q=gitlab'>GitLab on cloudsearch.verizon.com</a>
 </li>
 <li>
 Ask questions about <a href='https://stackoverflow.verizon.com/questions/tagged/gitlab'>GitLab on Stackoverflow</a>
 </li>
 <li>
 Request support on <a href='https://onejira.verizon.com/browse/TOOLS'>onejira.verizon.com/browse/tools</a>
 </li>
 <li>
 Join the <a href='https://hangouts.google.com/group/XMtIsdDJbhZKRQYf2'>oneStash -> Gitlab Migration Support</a> chat room on Hangouts.
 </li>
</ul>
</p>
"""
      )
    }
    success {
      emailext(
        subject: 'Your migration has been completed.',
        recipientProviders: [[$class: 'RequesterRecipientProvider']],
        mimeType: 'text/html',
        body: """
<p>
Congratulations, you have migrated <b>${params.url}</b> to ${env.GITLAB_SERVER}!

Click <a href='${env.RUN_DISPLAY_URL}'>here</a> to review the migration results.
</p>
<p>
Find out more about GitLab at Verizon,
<ul>
 <li>
 Search <a href='https://cloudsearch.verizon.com/?q=gitlab'>GitLab on cloudsearch.verizon.com</a>
 </li>
 <li>
 Ask questions about <a href='https://stackoverflow.verizon.com/questions/tagged/gitlab'>GitLab on Stackoverflow</a>
 </li>
 <li>
 Request support on <a href='https://onejira.verizon.com/browse/TOOLS'>onejira.verizon.com/browse/tools</a>
 </li>
 <li>
 Join the <a href='https://hangouts.google.com/group/XMtIsdDJbhZKRQYf2'>oneStash -> Gitlab Migration Support</a> chat room on Hangouts.
 </li>
</ul>
</p>
"""
      )
    }
    unstable {
      emailext(
        subject: 'Your migration needs verification.',
        recipientProviders: [[$class: 'RequesterRecipientProvider']],
        mimeType: 'text/html',
        body: """
<p>
The ${params.repoOrProject} migration, <b>${params.url}</b>, to ${env.GITLAB_SERVER} requires verification.

Click <a href='${env.RUN_DISPLAY_URL}'>here</a> to review the migration results.
</p>
<p>
One of the following conditions has occurred,

<ul>
 <li>The commit history on ${env.GITLAB_SERVER} is ahead of the ${params.url}</li>
 <li>You do not have permissions to configure ${params.url} to read-only. Please have your project admin re-execute the job.</li>
</ul>
</p>
<p>
Find out more about GitLab at Verizon,
<ul>
 <li>
 Search <a href='https://cloudsearch.verizon.com/?q=gitlab'>GitLab on cloudsearch.verizon.com</a>
 </li>
 <li>
 Ask questions about <a href='https://stackoverflow.verizon.com/questions/tagged/gitlab'>GitLab on Stackoverflow</a>
 </li>
 <li>
 Request support on <a href='https://onejira.verizon.com/browse/TOOLS'>onejira.verizon.com/browse/tools</a>
 </li>
 <li>
 Join the <a href='https://hangouts.google.com/group/XMtIsdDJbhZKRQYf2'>oneStash -> Gitlab Migration Support</a> chat room on Hangouts.
 </li>
</ul>
</p>
"""
      )
    }
    always {
      cleanWs(
        cleanWhenAborted: true,
        cleanWhenFailure: true,
        cleanWhenSuccess: true,
        cleanWhenUnstable: true
      )
    }
  } //end of post
} //end of pipeline
