# Using release images

## Docker images

Refer to the [full setup docs](./docs/full_setup.md) when using a congregate container with mongo built-in.

## Docker-compose

In an effort to provide a more [modular setup for using congregate](https://gitlab.com/groups/gitlab-org/professional-services-automation/tools/-/epics/115),
there will be some docker-compose files in this folder
you can use that will break up different components into distinct services.

### Congregate and mongo as separate services

- Copy the *docker-compose.yml* file you would like to use in your environment
- Set the `CONGREGATE_DATA` environment variable to a path on your host
  where you will store all congregate data outside of the container
- Spin up the docker containers by running `docker-compose up -d`
- Configure in your *congregate.conf* file

    ```ini
    [APP]
    mongo_host = mongo
    ```

- Interact with congregate either through running `docker exec congregate congregate <command>`
  or by entering a shell in the congregate container and running your congregate commands there

### Congregate, mongo, and maven

- Follow the instructions above with these additional steps
    - Configure in your *congregate.conf* file

    ```ini
    [APP]
    maven_port = 50050
    ```

    - If you are running into an issue where congregate cannot communicate with
      the maven gRPC server, try configuring the following in your *congregate.conf* file 

    ```ini
    [APP]
    maven_port = 50050
    grpc_host = <docker_host_local_ip> # E.g. 192.168.0.5
    ```

