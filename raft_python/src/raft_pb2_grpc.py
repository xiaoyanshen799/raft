# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import raft_pb2 as raft__pb2


class RaftStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.RequestVote = channel.unary_unary(
                '/raft.Raft/RequestVote',
                request_serializer=raft__pb2.RequestVoteRequest.SerializeToString,
                response_deserializer=raft__pb2.RequestVoteResponse.FromString,
                )
        self.AppendEntries = channel.unary_unary(
                '/raft.Raft/AppendEntries',
                request_serializer=raft__pb2.AppendEntriesRequest.SerializeToString,
                response_deserializer=raft__pb2.AppendEntriesResponse.FromString,
                )
        self.ClientRequest = channel.unary_unary(
                '/raft.Raft/ClientRequest',
                request_serializer=raft__pb2.ClientRequestMessage.SerializeToString,
                response_deserializer=raft__pb2.ClientResponseMessage.FromString,
                )


class RaftServicer(object):
    """Missing associated documentation comment in .proto file."""

    def RequestVote(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def AppendEntries(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def ClientRequest(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_RaftServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'RequestVote': grpc.unary_unary_rpc_method_handler(
                    servicer.RequestVote,
                    request_deserializer=raft__pb2.RequestVoteRequest.FromString,
                    response_serializer=raft__pb2.RequestVoteResponse.SerializeToString,
            ),
            'AppendEntries': grpc.unary_unary_rpc_method_handler(
                    servicer.AppendEntries,
                    request_deserializer=raft__pb2.AppendEntriesRequest.FromString,
                    response_serializer=raft__pb2.AppendEntriesResponse.SerializeToString,
            ),
            'ClientRequest': grpc.unary_unary_rpc_method_handler(
                    servicer.ClientRequest,
                    request_deserializer=raft__pb2.ClientRequestMessage.FromString,
                    response_serializer=raft__pb2.ClientResponseMessage.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'raft.Raft', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class Raft(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def RequestVote(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/raft.Raft/RequestVote',
            raft__pb2.RequestVoteRequest.SerializeToString,
            raft__pb2.RequestVoteResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def AppendEntries(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/raft.Raft/AppendEntries',
            raft__pb2.AppendEntriesRequest.SerializeToString,
            raft__pb2.AppendEntriesResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def ClientRequest(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/raft.Raft/ClientRequest',
            raft__pb2.ClientRequestMessage.SerializeToString,
            raft__pb2.ClientResponseMessage.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
