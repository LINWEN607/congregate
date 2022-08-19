from concurrent import futures
import logging

import grpc
import maven_pb2
import maven_pb2_grpc
import subprocess
from subprocess import Popen,PIPE,STDOUT

class MavenCommandHandler(maven_pb2_grpc.MavenCommandHandlerServicer):

    def execute_mvn_command(self, cmd):
        return Popen(cmd.split(' '), stderr=STDOUT,stdout=PIPE)
    
    def build_response(self, output):
        return maven_pb2.Response(output=output.communicate()[0], exitCode=output.returncode)
    
    def RunCommand(self, request, context):
        out = Popen(request.phase.split(' '), stderr=STDOUT,stdout=PIPE)
        return maven_pb2.Response(output=out.communicate()[0], exitCode=out.returncode)

    def GetPackage(self, request, context):
        cmd = f"mvn dependency:get -s /opt/settings.xml"
        if request.projectName:
            cmd += f" -Dmaven.repo.local=/opt/project_repositories/{request.projectName}"
        if request.artifact:
            cmd += f" -Dartifact={request.artifact}"
        if request.remoteRepositories:
            cmd += f" -DremoteRepositories={request.remoteRepositories}"
        if request.transitive and request.overrideDefault:
            cmd += f" -Dtransitive={request.transitive}"
        return self.build_response(self.execute_mvn_command(cmd))

    def DeployPackage(self, request, context):
        cmd = f"mvn deploy:deploy-file -s /opt/settings.xml"
        if request.projectName:
            cmd += f" -Dmaven.repo.local=/opt/project_repositories/{request.projectName}"
        if request.groupId:
            cmd += f" -DgroupId={request.groupId}"
        if request.artifactId:
            cmd += f" -DartifactId={request.artifactId}"
        if request.version:
            cmd += f" -Dversion={request.artifactId}"
        if request.packaging:
            cmd += f" -Dpackaging={request.packaging}"
        if request.file:
            cmd += f" -Dfile={request.file}"
        if request.pomFile:
            cmd += f" -Dfile={request.pomFile}"
        if request.repositoryId:
            cmd += f" -DrepositoryId={request.repositoryId}"
        if request.url:
            cmd += f" -Durl={request.url}"
        
        return self.build_response(self.execute_mvn_command(cmd))

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    maven_pb2_grpc.add_MavenCommandHandlerServicer_to_server(MavenCommandHandler(), server)
    server.add_insecure_port('[::]:50051')
    print("Starting server at 50051")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    logging.basicConfig()
    serve()
