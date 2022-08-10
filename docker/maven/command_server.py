# NOTE: this file currently doesn't work and needs to be refactored to handle the new maven gRPC files

from concurrent import futures
import logging

import grpc
import cmd_pb2
import cmd_pb2_grpc
import subprocess
from subprocess import Popen,PIPE,STDOUT

class CommandCaller(cmd_pb2_grpc.CommandHandlerServicer):

    def RunCommand(self, request, context):
        out = Popen(request.command.split(' '), stderr=STDOUT,stdout=PIPE)
        return cmd_pb2.Response(output=out.communicate()[0], exitCode=out.returncode)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    cmd_pb2_grpc.add_CommandHandlerServicer_to_server(CommandCaller(), server)
    server.add_insecure_port('[::]:50051')
    print("Starting server at 50051")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    logging.basicConfig()
    serve()
