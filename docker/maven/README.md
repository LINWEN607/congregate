# Maven gRPC server image

This image covers interacting with maven over RPC.

The Dockerfile is meant to be built from the root of this repository

## Troubleshooting

If you receive an error about an http blocker, you will need to edit
the default maven settings (`/usr/share/maven/conf/settings.xml`) and comment
out the `maven-default-http-blocker` mirror. This is needed if the source is only using HTTP.