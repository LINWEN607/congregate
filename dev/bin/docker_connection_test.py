# This code chunk has to be run from withing the Poetry context of Congregate so that it has access to the Docker libraries
# Eg: poetry shell
# After that, you can run python dev/bin/docker_connection_test.py from within the shell
# poetry run python dev/bin/docker_connection_test.py should also work
# variables should be self explanatory

# Registry to connect the client to without protocol
registry = "registry.gitlab.com"
username = "my_docker_username"
password = "my_reg_scoped_pat"

# This is a test image that it will attempt to pull. Add an image for your source or destination system as appropriate.
# Use an image that would require authentication to your source or destination server to get the pull test with the client configuration
full_image_path = "registry.gitlab.com/gitlab-org/example-dont-user"

# Tag for the above image to pull
image_tag = "some-tag"

from docker import from_env
client = from_env()
client.login(username=f"{username}",password=f"{password}",registry=f"https://{registry}")

# Test connection to Docker registry. This defaults to docker hub regardless of how registry is set and searches for busybox
try:
    # List repositories in the registry
    repositories = client.images.search(f"busybox")
    print(f"Successfully connected to Docker registry.")
    print(f"Found {len(repositories)} repositories.")
except Exception as e:
    print(f"Failed to connect to Docker registry: {str(e)}")

# Test local Docker daemon connection
try:
    # List local images
    images = client.images.list()
    print("Successfully connected to Docker daemon.")
    print(f"Found {len(images)} local images.")
    print(f"{images}")
except Exception as e:
    print(f"Failed to connect to Docker daemon: {str(e)}")

# Test pulling from the registry you've connected to. Use a container that would require authentication (non-public)
try:
    image = client.images.pull(repository=f"{full_image_path}", tag=f"{image_tag}")
    print(f"Successfully pulled image {full_image_path}:{image_tag}")
    print(f"Image ID: {image.id}")
except Exception as e:
    print(f"Failed to pulled image: {str(e)}")