# Jenkins Development in Congregate

This directory contains a Dockerfile file for standing up a test Jenkins instance with some populated test data.

**NOTE:** This image is to be used for local testing and automated testing in a pipeline so credentials are present in this README and Dockerfile. **Do not use this image for production use**

## Local image

### Build the docker image

```bash
cd $CONGREGATE_PATH/docker/jenkins
docker build -t jenkins-test .
```

### Spin up the local container

```bash
# With test data
docker run --name jenkins -p 8080:8080 -it jenkins-test --env SEED_DATA=true /bin/bash

# Without test data
docker run --name jenkins -p 8080:8080 -it jenkins-test /bin/bash
```

## From the congregate container registry

### Spin up the container

```bash
docker run --name jenkins -p 8080:8080 -it registry.gitlab.com/gitlab-org/professional-services-automation/tools/migration/congregate/jenkins-seed:latest /bin/bash
```

Navigate to localhost:8080 to see jenkins up and running. You can log in with the following credentials:

```
username: test-admin
password: password
```

