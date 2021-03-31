external_url 'http://gitlab-web-local.com/'
gitlab_rails['initial_root_password'] = File.read('/run/secrets/gitlab_root_password')

### LDAP Settings
###! Docs: https://docs.gitlab.com/omnibus/settings/ldap.html
###! **Be careful not to break the indentation in the ldap_servers block. It is
###!   in yaml format and the spaces must be retained. Using tabs will not work.**

gitlab_rails['ldap_enabled'] = true
# gitlab_rails['prevent_ldap_sign_in'] = false

###! **remember to close this block with 'EOS' below**
 gitlab_rails['ldap_servers'] = YAML.load <<-'EOS'
   main: # 'main' is the GitLab 'provider ID' of this LDAP server
     label: 'LDAP'
     host: 'openldap'
     port: 1389
     uid: 'uid'
     bind_dn: 'CN=admin,DC=example,DC=org'
     password: 'adminpassword'
     encryption: 'plain' # "start_tls" or "simple_tls" or "plain"
     verify_certificates: false
     smartcard_auth: false
     active_directory: false
     allow_username_or_email_login: true
     lowercase_usernames: false
     block_auto_created_users: false
     base: 'DC=example,DC=org'
     user_filter: ''
#     ## EE only
     group_base: ''
     admin_group: ''
     sync_ssh_keys: false
#
#   secondary: # 'secondary' is the GitLab 'provider ID' of second LDAP server
#     label: 'LDAP'
#     host: '_your_ldap_server'
#     port: 389
#     uid: 'sAMAccountName'
#     bind_dn: '_the_full_dn_of_the_user_you_will_bind_with'
#     password: '_the_password_of_the_bind_user'
#     encryption: 'plain' # "start_tls" or "simple_tls" or "plain"
#     verify_certificates: true
#     smartcard_auth: false
#     active_directory: true
#     allow_username_or_email_login: false
#     lowercase_usernames: false
#     block_auto_created_users: false
#     base: ''
#     user_filter: ''
#     ## EE only
#     group_base: ''
#     admin_group: ''
#     sync_ssh_keys: false
EOS

################################################################################
# Let's Encrypt integration
################################################################################
letsencrypt['enable'] = false
