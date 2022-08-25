import grpc

TIMEOUT_SEC = 5
def is_rpc_service_running(service_url) -> bool:
    """
        Checks if gRPC service is running

        :param: service_url: (str) the url to where the gRPC service is running. Ex: localhost:50051

        :return: True if the service is running, False if not
    """
    with grpc.insecure_channel(service_url) as channel:
        try:
            grpc.channel_ready_future(channel).result(timeout=TIMEOUT_SEC)
            return True
        except grpc.FutureTimeoutError:
            return False

