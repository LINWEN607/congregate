# Notes

## Schema

This is a very basic schema, so there is currently no matching email field. That means that only logins using LDAP name are currently supported. You can add email by modifying the entries ([see below](#ldap-functions))

## Base Container

This compose is reliant on the base LDAP container at:

```yaml
registry.gitlab.com/gitlab-com/customer-success/professional-services-group/global-practice-development/migration/openldap-container-bases/master:latest
```

## Volume Mounts

The mounts are based at `$GITLAB_HOME` for the GitLab volumes, and `$LDAP_HOME` for the LDAP volumes. Please make sure these are set before executing.

## LDAP Tools

You can test ldap from either container. The `openldap` container of course has all of the proper items installed. However, if you need to install on the `gilab-web` container,
you can follow the instructions, below:

### Installing Tools

If doing tests searches, you may need to install tools on the `gitlab` container.

First, log into the container:

```bash
docker exec -it gitlab-web /bin/bash 
```

Then, in the container, run the following:

```bash
export DEBIAN_FRONTEND=noninteractive
apt update
apt -y install libnss-ldap libpam-ldap ldap-utils
```

## LDAP Functions

Following assumes the configuration currently called out in the [docker-compose.yml](./docker-compose.yml) file and that you have installed tools as described, above

First, log into the container:

```bash
docker exec -it ldap_openldap_1 /bin/bash
```

or

```bash
docker exec -it gitlab-web /bin/bash 
```

Then, in the container, you can run queries such as:

```bash
ldapsearch -p 1389 -w 'adminpassword' -x -v -h openldap -D 'cn=admin,dc=example,dc=org' -b 'dc=example,dc=org' cn=user01
```

Or modify users to add email:

```bash
ldapmodify -a -p 1389 -w 'adminpassword' -x -v -h openldap -D 'cn=admin,dc=example,dc=org'
dn: cn=user01,ou=users,dc=example,dc=org
changetype: modify
add: mail
mail: user01@example.org
```

## Random Debug

More around docker and GitLab than LDAP, if you get errors about `postgres` not being able to create sockets, there are two possible issues:

1) You've nested your volume links too deep in the host machine (e.g. under the entire `Congregate` path). Move your `$GITLAB_HOME` folder to a shallower location on the host

## Future State

This just provides the base containers for additional testing in the future

```bash
ln -s /Users/gmiller/gitlab gitlab_dir
ln -s /Users/gmiller/gitlab ldap_dir
```
