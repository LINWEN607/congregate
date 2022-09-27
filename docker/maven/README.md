# Maven gRPC server image

This image covers interacting with maven over RPC.

The Dockerfile is meant to be built from the root of this repository

## Building and Running the Container

```bash
cp docker/maven/Dockerfile ./
sudo podman build -t 'maven-grpc' .
# Generate a PAT in GitLab and pass it into the container
sudo podman run --name maven-grpc -e SRC_ACCESS_TOKEN=<src-access-token> -e DEST_ACCESS_TOKEN=<dest-access-token> -p 50051:50051 -it localhost/maven-grpc:latest /bin/bash
```

## Troubleshooting

If you receive an error about an http blocker, you will need to edit
the default maven settings (`/usr/share/maven/conf/settings.xml`) and comment
out the `maven-default-http-blocker` mirror. This is needed if the source is only using HTTP.
