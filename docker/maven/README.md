# Maven gRPC server image - (DEPRECATED)

This image covers interacting with maven over RPC.

The Dockerfile is meant to be built from the root of this repository

## Important Update: Transition to Non-RPC Approach for Maven Package Migration

We have made significant updates to our process for migrating Maven packages. **The previous RPC-based method has been deprecated and replaced with a new, more efficient API-driven approach.**

### Why the Change?

- **Enhanced Performance:** The new API method provides a faster, more reliable experience when migrating Maven packages.
- **Improved Security:** This approach aligns with the latest security standards, ensuring that your package migration process is secure.
- **Greater Flexibility:** The API-based method offers more flexibility, allowing for better integration with the curent code base.

### What You Need to Do

If you are currently using the old RPC-based method, please transition to the new API approach as soon as possible by switching to the latest version of Congregate. The RPC method is no longer supported, and continuing to use it may result in migration failures or data inconsistencies.

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
