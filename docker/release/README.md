# Using release images

## Docker images

Refer to the [full setup docs](./docs/full_setup.md) when using a congregate container with mongo built-in.

## Docker-compose

In an effort to provide a more [modular setup for using congregate](https://gitlab.com/groups/gitlab-org/professional-services-automation/tools/-/epics/115),
there will be some docker-compose files in this folder
that you can use to break up different components into distinct services.

Run

```bash
curl https://gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate/-/raw/master/docker/release/setup_congregate.sh | bash
```

which does the following:
- Pulls down the Congregate docker-compose file
- Creates a congregate-data folder and all necesary subfolders _for the other services in the docker-compose file_
- Pulls down standard configurations for Vector, Loki, and Grafana
- Sets CONGREGATE_DATA to the created congregate-data folder

then you should be all set to run Congregate and its related services
