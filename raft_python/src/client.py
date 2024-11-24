import grpc
import raft_pb2
import raft_pb2_grpc


class RaftClient:
    def __init__(self, server_address):
        self.channel = grpc.insecure_channel(server_address)
        self.stub = raft_pb2_grpc.RaftStub(self.channel)

    def send_request(self, operation):
        try:
            response = self.stub.ClientRequest(
                raft_pb2.ClientRequestMessage(operation=operation)
            )
            return response.success, response.result
        except grpc.RpcError as e:
            return False, str(e)