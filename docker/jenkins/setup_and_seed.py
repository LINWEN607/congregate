from time import sleep
from os.path import exists
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

    suggested_plugins =  [
        "cloudbees-folder", 
        "antisamy-markup-formatter", 
        "build-timeout", 
        "credentials-binding", 
        "timestamper", 
        "ws-cleanup", 
        "ant", 
        "gradle", 
        "workflow-aggregator", 
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
        "multiple-scms"
    ]

    # Not needed currently, but it will return a list of all the jenkins plugins available
    # getPlugins = s.get(formatted_url('pluginManager/plugins'))
    # print(formatted_message("Get plugins", getPlugins))

    # Installing suggested list of plugins
    for plugin in suggested_plugins:
        plugin_name = f"plugin.{plugin}"
        installPlugins = s.post(formatted_url(f"pluginManager/install?{plugin_name}=true"), 
            data={
                "dynamicLoad": True,
                "Jenkins-Crumb": crumb
            }
        )

        print(formatted_message(f"Installing plugin {plugin_name}", installPlugins))

    # Since the plugin requests above just trigger the install, the actual install is not completed
    # before a response is returned
    print("Waiting 60 seconds before continuing to get plugins installed")
    sleep(60)

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

    # Write a file to check if jenkins is already set up
    with open("/var/jenkins_home/install-finished", "w") as f:
        f.write("install complete")

def seed_data():
    j = Jenkins("http://localhost:8080", "test-admin", "password")
    


if __name__ == "__main__":
    if not exists("/var/jenkins_home/install-finished"):
        setup_jenkins()
    else:
        print("Jenkins is already setup. Skipping")