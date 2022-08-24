import grpc

from congregate.helpers.configuration_validator import ConfigurationValidator
from congregate.migration.maven import maven_pb2
from congregate.migration.maven import maven_pb2_grpc

config = ConfigurationValidator()

def get_package(**kwargs):
    """
        Calls RPC service to download maven package to maven container

        Refer to /protos/maven.proto for available parameters

        Example usage:

        get_package(
            projectName="gitlab_project",
            artifact="com.example:demo:0.0.1-SNAPSHOT",
            remoteRepositories="gitlab-maven::::http://<gitlab-instance>/api/v4/projects/<project-id>/packages/maven"
        )
    """
    with grpc.insecure_channel(f"{config.grpc_host}:{config.maven_port}") as channel:
        stub = maven_pb2_grpc.MavenCommandHandlerStub(channel)
        response = stub.GetPackage(maven_pb2.GetPackageArgs(**kwargs))
    return response.exitCode, response.output

def deploy_package(**kwargs):
    """
        Calls RPC service to deploy maven package to GitLab repo

        Refer to /protos/maven.proto for available parameters

        Example usage:

        deploy_package(
            projectName="gitlab_project",
            groupId="com.example",
            artifactId="demo",
            version="0.0.1-SNAPSHOT",
            packaging="JAR",
            file="/home/ps-user/.m2/repository/com/example/demo/0.0.1-SNAPSHOT/demo-0.0.1.jar",
            pomFile="/home/ps-user/.m2/repository/com/example/demo/0.0.1-SNAPSHOT/demo-0.0.1-SNAPSHOT.pom",
            repositoryId="gitlab-maven",
            url="http://<gitlab-instance>/api/v4/projects/<project-id>/packages/maven"
        )
    """
    with grpc.insecure_channel(f"{config.grpc_host}:{config.maven_port}") as channel:
        stub = maven_pb2_grpc.MavenCommandHandlerStub(channel)
        response = stub.DeployPackage(maven_pb2.DeployPackageArgs(**kwargs))
    return response.exitCode, response.output
