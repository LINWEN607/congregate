# Nginx Proxy Setup

## Install certbot

 ```bash
 sudo apt-get install nginx certbot -y
 sudo apt-get install python3-certbot-nginx -y
 sudo certbot --nginx -d congregate.example.net
 ```

You will be prompted for an email "used for urgent renewal and security notices". Feel free to enter a dummy email if this is a temporary solution and you do not plan to maintain the certificate.

 **NOTE:** Allow port 80 for `certbot` to generate a cert from host VM. Block port 80 (if needed) afterwards.

## Certificate chain

- Retrieve self-signed certificate.
  - One may need to manually download the certificate from the SCM (BitBucket Server, GitHub) server.
  - If available to select download format, choose `Base-64 encoded X.509 (.CER)`.
- Manually create a `cert.pem` file in `/etc/nginx/` and append the **root**, **intermediate**, and **leaf** certificates.
- Compile `cert.pem` file as follows:

  ```text
  -----BEGIN CERTIFICATE-----
  root key
  -----END CERTIFICATE-----
  -----BEGIN CERTIFICATE-----
  intermediate key
  -----END CERTIFICATE-----
  -----BEGIN CERTIFICATE-----
  leaf key
  -----END CERTIFICATE-----
  ```

## NGINX Configuration

- Match the [`congregate.example.net.conf`](./congregate.example.net.conf) file with the assigned domain name.
- Store file at `/etc/nginx/sites-available/` as the default location.
- From the `/etc/nginx/sites-enabled/` folder symlink the file as follows:

  ```bash
  ln -s .../sites-available/congregate.example.net.conf .
  ```

## Transient Imports VM Firewall (GitLab PS specific)

- Configure the firewall for the transient imports VM ([console](https://console.cloud.google.com/compute/instances?project=transient-imports) and [project](https://gitlab.com/gitlab-com/gl-infra/transient-imports)) to allow the proxy pass-through.
- This usually means one has to additionally allow ports 80 and 443 for:
  - The [GitLab Web/API Fleet](https://docs.gitlab.com/ee/user/gitlab_com/#ip-range)
  - The user's local machine
  - The VM itself
    - Wait until the VM is created and add the host IP. Updating firewall rules should not change the host IP

**NOTE:** Any transient imports pipeline run will erase manual firewall changes to all machines in the space.

## Migration Note

When using the nginx proxy to run migrations, before running `congregate list`, configure the `congregate.conf` file's `src_hostname` to point to the source instance.

After listing (and staging), reconfigure the `congregate.conf` file's `src_hostname` to use the proxy's server name for the actual migration (`congregate migrate`).
