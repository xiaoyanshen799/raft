import time
import random
import threading
import xmlrpc.client
from xmlrpc.server import SimpleXMLRPCServer

class State:
    FOLLOWER = "follower"
    CANDIDATE = "candidate"
    LEADER = "leader"

class Process:
    def __init__(self, id, peers):
        self.id = id
        self.state = State.FOLLOWER
        self.term = 0
        self.votes = 0
        self.log = []
        self.peers = peers
        self.heartbeat_timeout = 0.1
        self.election_timeout = random.uniform(0.15, 0.3)
        self.heartbeat_event = threading.Event()

    def start_election(self):
        self.state = State.CANDIDATE
        self.term += 1
        self.votes = 1
        print(f"Process {self.id} starts election for term {self.term}")

        for peer in self.peers:
            with xmlrpc.client.ServerProxy(peer) as proxy:
                try:
                    reply = proxy.request_vote(self.id)
                    if reply:
                        self.votes += 1
                except:
                    pass

        if self.votes > len(self.peers) / 2:
            self.state = State.LEADER
            print(f"Process {self.id} becomes the leader")
            self.send_heartbeats()

    def send_heartbeats(self):
        while self.state == State.LEADER:
            for peer in self.peers:
                with xmlrpc.client.ServerProxy(peer) as proxy:
                    try:
                        proxy.append_entries(self.id)
                    except:
                        pass
            time.sleep(self.heartbeat_timeout)

    def append_entries(self, leader_id):
        print(f"Process {self.id} received AppendEntries from {leader_id}")
        self.heartbeat_event.set()

    def request_vote(self, candidate_id):
        return True

def main():
    peers = ["http://localhost:9001", "http://localhost:9002"]  # List of peer addresses
    process = Process(1, peers)

    server = SimpleXMLRPCServer(("localhost", 9000), allow_none=True)
    server.register_instance(process)
    server.serve_forever()

if __name__ == "__main__":
    main()
