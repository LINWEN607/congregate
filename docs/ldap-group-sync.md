# ldap-group-sync command

## Prequisites

### Ingestion File Format

The file is a pipe-delimited file with the headers:

```
group id|ldap group cn
```

### Configuration File Entries

in addition to the standard `congregate.conf` settings for your `DESTINATION`, you will also need these settings in the `DESTINATION` section of your configuration file:

#### ldap_group_link_provider

This is the LDAP server label from the instance configuration. This is the type, `ldap` in this case, plus the `gitlab_rails['ldap_servers']`
section value in gitlab.rb. Using the below default from gitlab.rb as an example, this value should be `ldapmain` as it is of type `ldap` and we want
to bind to the `main` server entry.

```yaml
gitlab_rails['ldap_servers'] = YAML.load <<-'EOS'                   
    main: # 'main' is the GitLab 'provider ID' of this LDAP server
        label: 'LDAP'                                                                              
        host: 'openldap'                                         
        port: 1389                                                                 
        uid: 'uid'
```

#### ldap_group_link_group_access

The minimum access to give users via the sync. This maps directly to the values at https://docs.gitlab.com/ee/api/members.html#valid-access-levels. 
Defaults to no access.

## Command

Like most `congregate` commands, `ldap-group-sync` accepts the `--commit` flag to run the work. Without `--commit`, you will only get logging of what activity would have occurred.

```bash
./congregate.sh ldap-group-sync <path to PDV file> [--commit]
```

## docker-compose

Note: These instructions assume familiarity with using docker/docker compose

A test `docker-compose.yml` file is included as well as a test `gitlab.rb` set to enable `LDAP`. This will spin up a `bitnami ldap` container, as well as the latest `gitlab-ee` container on 
the same network, so that they can communicate

```bash
docker-compose -f docker-compose.yml up
```

* Once the gitlab-ee instance is up, login as admin user `root` with password `5iveL!fe` and create an admin token. The site should be available at `http://127.0.0.1:8080` from the web browser of the host machine
* `docker exec` into the `congregate container` and configure the `congregate` `[DESTINATION]` section as usual, using the new admin token.
* Add your `ldap_group_link_provider` and `ldap_group_link_group_access` lines to the `[DESTINATION]` section. Eg:

```yaml
ldap_group_link_provider=ldapmain
ldap_group_link_group_access=10
```

* `docker cp` the `gitlab.rb` file, or `docker exec` into the `gitlab-src` container and set up LDAP
manually
    * Don't forget to `gitlab-ctl reconfigure` after modifying the `gitlab.rb` file
* You should now be able to login via LDAP to `http://127.0.0.1:8080` from the web browser of the host machine
    * Usernames and passwords are in the `docker-compose` file under the `openldap` section
* Create a group (should be fine as any user)
    * Note the group id
* Back in the running `congregate` container, create your `example.pdv` file with `group id|readers` as the only line
    * `readers` is an already-existing `CN` in the `openldap` container
* Excute the command:

```bash
./congregate.sh ldap-group-sync <path to example.pdv> --commit
```

This should setup the LDAP group sync on the `gitlab-src` instance. Log back in through the browser and verify
