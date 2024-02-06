This is a wrapper around [skopeo](https://github.com/containers/skopeo) to help migrate images between two container registries. Skopeo doesn't require docker or podman to be installed!

## Prerequisites

The script is a wrapper around skopeo, hense it requires it. Check [installation](https://github.com/containers/skopeo/blob/main/install.md) options.

## How to use

`image-migrator.sh` expects several variables (which can be set in `config.sh` file):

* `SOURCE_USER` - username on source for docker login
* `SOURCE_PAT` - password / token on source for docker login
* `TARGET_USER` - username on target for docker login
* `TARGET_PAT` - password / token on target for docker login
* `BASE_URL_SOURCE` - base URL on source (i.e. *registry.gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate*)
* `BASE_URL_TARGET` - base URL on target (i.e. *registry.gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate_target*)

`images.yml` contains list of images on source to be migrated (one image per line), example:

```yaml

registry.gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate/maven-server:latest
registry.gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate:6.12.0-centos

```

Once done: 

```bash 

chmod +x image-migrator.sh

./image-migrator.sh > logs/image-migrator-ddmmyyyy.log 2>&1

tail -f logs/image-migrator-ddmmyyyy.log

```