import grpc
import time
import random
import threading
from concurrent import futures
from raft_pb2 import RequestVoteRequest, AppendEntriesRequest, ClientRequestMessage
import raft_pb2_grpc

class RaftNode(raft_pb2_grpc.RaftServicer):
    def __init__(self, id):
        self.id = id
        self.term = 0
        self.state = "follower"
        self.vote_count = 0
        self.log = []
        self.commit_index = 0
        self.peers = []  # Initialize with other node connections

    def RequestVote(self, request, context):
        print(f"Process {self.id} received RequestVote from {request.candidate_id}")
        return raft_pb2.RequestVoteResponse(vote_granted=True)

    def AppendEntries(self, request, context):
        print(f"Process {self.id} received AppendEntries from {request.leader_id}")
        return raft_pb2.AppendEntriesResponse(success=True)

    def ClientRequest(self, request, context):
        if self.state != "leader":
            return raft_pb2.ClientResponseMessage(success=False, result="Not the leader")
        self.log.append({"term": self.term, "command": request.operation})
        return raft_pb2.ClientResponseMessage(success=True, result="Operation added to log")

    def start_election(self):
        self.state = "candidate"
        self.term += 1
        self.vote_count = 1
        print(f"Process {self.id} starts election for term {self.term}")
        for peer in self.peers:
            try:
                response = peer.RequestVote(RequestVoteRequest(term=self.term, candidate_id=self.id))
                if response.vote_granted:
                    self.vote_count += 1
            except:
                pass
        if self.vote_count > len(self.peers) // 2:
            self.state = "leader"
            self.send_heartbeats()

    def send_heartbeats(self):
        while self.state == "leader":
            for peer in self.peers:
                peer.AppendEntries(AppendEntriesRequest(term=self.term, leader_id=self.id))
                print(f"Process {self.id} sends AppendEntries to peer")
            time.sleep(0.1)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    raft_node = RaftNode(id=2)
    raft_pb2_grpc.add_RaftServicer_to_server(raft_node, server)
    server.add_insecure_port('[::]:50052')
    server.start()
    print("Process 2 started")
    while True:
        time.sleep(random.uniform(0.15, 0.3))
        if raft_node.state == "follower":
            raft_node.start_election()

if __name__ == "__main__":
    serve()
