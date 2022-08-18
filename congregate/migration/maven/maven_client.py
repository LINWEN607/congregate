import os
import grpc

from congregate.migration.maven import maven_pb2
from congregate.migration.maven import maven_pb2_grpc

def get_package(**kwargs):
    """
        Calls RPC service to download maven package to maven container

        Refer to /protos/maven.proto for available parameters
    """
    with grpc.insecure_channel(f"{os.getenv('HOST_IP')}:50051") as channel:
        stub = maven_pb2_grpc.MavenCommandHandlerStub(channel)
        response = stub.GetPackage(maven_pb2.GetPackageArgs(**kwargs))
    return response.output, response.exitCode

def deploy_package(**kwargs):
    """
        Calls RPC service to deploy maven package to GitLab repo

        Refer to /protos/maven.proto for available parameters
    """
    with grpc.insecure_channel(f"{os.getenv('HOST_IP')}:50051") as channel:
        stub = maven_pb2_grpc.MavenCommandHandlerStub(channel)
        response = stub.DeployPackage(maven_pb2.DeployPackageArgs(**kwargs))
    return response.output, response.exitCode
