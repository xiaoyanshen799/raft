import grpc
import random
import time
import threading
from concurrent import futures
import raft_pb2
import raft_pb2_grpc
from state import NodeState, LogEntry
import logging
from logging.handlers import RotatingFileHandler


# # 配置日志系统
# def setup_logger(node_id):
#     logger = logging.getLogger(f'raft.node.{node_id}')
#     logger.setLevel(logging.INFO)
#
#     # 创建控制台处理器
#     console_handler = logging.StreamHandler()
#     console_handler.setLevel(logging.INFO)
#     console_formatter = logging.Formatter(
#         '%(asctime)s - Node %(node_id)s - %(levelname)s - %(message)s'
#     )
#     console_handler.setFormatter(console_formatter)
#
#     # 创建文件处理器
#     file_handler = RotatingFileHandler(
#         f'node_{node_id}.log',
#         maxBytes=1024 * 1024,  # 1MB
#         backupCount=5
#     )
#     file_handler.setLevel(logging.INFO)
#     file_formatter = logging.Formatter(
#         '%(asctime)s - %(levelname)s - %(message)s'
#     )
#     file_handler.setFormatter(file_formatter)
#
#     # 添加处理器到logger
#     logger.addHandler(console_handler)
#     logger.addHandler(file_handler)
#
#     return logger

class RaftNode(raft_pb2_grpc.RaftServicer):
    def __init__(self, node_id, peer_addresses):
        self.id = node_id
        self.peer_addresses = peer_addresses
        # self.logger = setup_logger(node_id)
        self.state = NodeState.FOLLOWER
        self.current_term = 0
        self.voted_for = None
        self.log = []
        self.index = 0
        self.commit_index = 0
        self.last_applied = 0
        self.leader_id = None

        # 选举相关的计时器
        self.election_timeout = random.randint(150, 300) / 1000
        self.last_heartbeat = time.time()

        # 启动选举计时器
        self.election_timer = threading.Thread(target=self._election_timer_loop)
        self.election_timer.daemon = True
        self.election_timer.start()

    def RequestVote(self, request, context):
        # self.logger.info(f"Received vote request from node {request.candidate_id}")
        # print(f"Process {self.id} receives RPC RequestVote from Process {request.candidate_id}")

        if request.term < self.current_term:
            return raft_pb2.RequestVoteResponse(vote_granted=False)

        if (self.voted_for is None or self.voted_for == request.candidate_id):
            self.voted_for = request.candidate_id
            self.current_term = request.term
            return raft_pb2.RequestVoteResponse(vote_granted=True)

        return raft_pb2.RequestVoteResponse(vote_granted=False)

    def AppendEntries(self, request, context):
        # self.logger.info(f"Received append entries from leader {request.leader_id}")
        # print(f"Process {self.id} receives RPC AppendEntries from Process {request.leader_id}")

        if request.term < self.current_term:
            return raft_pb2.AppendEntriesResponse(success=False)

        self.last_heartbeat = time.time()
        self.state = NodeState.FOLLOWER
        self.leader_id = request.leader_id
        self.current_term = request.term

        # 处理日志条目
        if request.entries:
            for entry in request.entries:
                log_entry = LogEntry(term=entry.term, command=entry.command)
                if len(self.log) <= self.commit_index:
                    self.log.append(log_entry)
                else:
                    self.log[self.commit_index] = log_entry
                self.commit_index += 1
                print(f"Process {self.id} appends log entry: {log_entry}", flush=True)

        if request.leader_commit > self.commit_index:
            self.commit_index = min(request.leader_commit, len(self.log) - 1)

        return raft_pb2.AppendEntriesResponse(success=True)

    def ClientRequest(self, request, context):
        print(f"Process {self.id} receives client request: {request.operation}")

        # 如果当前节点不是leader，需要转发请求到leader
        if self.state != NodeState.LEADER:
            if self.leader_id is None:
                return raft_pb2.ClientResponseMessage(
                    success=False,
                    result="No leader available"
                )

            # 找到leader的地址
            leader_address = None
            for peer in self.peer_addresses:
                if str(self.leader_id) in peer:  # 假设peer地址格式包含节点ID
                    leader_address = peer
                    break

            if leader_address:
                try:
                    with grpc.insecure_channel(leader_address) as channel:
                        stub = raft_pb2_grpc.RaftStub(channel)
                        print(f"Process {self.id} forwards request to leader {self.leader_id}", flush=True)
                        # 添加超时设置
                        response = stub.ClientRequest(
                            request,
                            timeout=5.0  # 5秒超时
                        )
                        return response
                except grpc.RpcError as e:
                    print(f"RPC failed: {e.code()}")
                    return raft_pb2.ClientResponseMessage(
                        success=False,
                        result=f"Request failed: {e.details()}"
                    )
            else:
                return raft_pb2.ClientResponseMessage(
                    success=False,
                    result=f"Cannot find leader address"
                )

        # 如果是leader，直接处理请求 (2) append <o, t, k+1> to log
        log_entry = LogEntry(term=self.current_term, command=request.operation)
        self.log.append(log_entry)
        self.index = len(self.log)
        print(f"Process {self.id} appends log entry: {log_entry} index {self.index}", flush=True)

        # 复制到其他节点
        success_count = 1  # 包括自己
        for peer in self.peer_addresses:
            try:
                with grpc.insecure_channel(peer) as channel:
                    stub = raft_pb2_grpc.RaftStub(channel)
                    response = stub.AppendEntries(raft_pb2.AppendEntriesRequest(
                        term=self.current_term,
                        leader_id=self.id,
                        entries=[raft_pb2.LogEntry(
                            term=log_entry.term,
                            command=log_entry.command
                        )],
                        leader_commit=self.commit_index
                    ))
                    if response.success:
                        success_count += 1
            except grpc.RpcError:
                continue

        # 如果多数节点确认，提交该条目
        if success_count > len(self.peer_addresses) / 2:
            self.commit_index = len(self.log) - 1
            return raft_pb2.ClientResponseMessage(
                success=True,
                result=f"Operation '{request.operation}' committed"
            )

        return raft_pb2.ClientResponseMessage(
            success=False,
            result="Failed to replicate to majority"
        )

    def _election_timer_loop(self):
        print(f"Process {self.id} starts election timer", flush=True)
        while True:
            time.sleep(0.01)  # 10ms检查间隔

            if self.state == NodeState.LEADER:
                self._send_heartbeat()
                continue

            if self.state == NodeState.FOLLOWER:
                if time.time() - self.last_heartbeat > self.election_timeout:
                    print(f"Process {self.id} starting election: no heartbeat received")

            if time.time() - self.last_heartbeat > self.election_timeout:
                self._start_election()

    def _start_election(self):
        print(f"Process {self.id} starts election")
        self.state = NodeState.CANDIDATE
        self.current_term += 1
        self.voted_for = self.id
        votes = 1

        for peer in self.peer_addresses:
            try:
                with grpc.insecure_channel(peer) as channel:
                    stub = raft_pb2_grpc.RaftStub(channel)
                    print(f"Process {self.id} sends RPC RequestVote to {peer}")
                    response = stub.RequestVote(raft_pb2.RequestVoteRequest(
                        term=self.current_term,
                        candidate_id=self.id
                    ))
                    if response.vote_granted:
                        votes += 1
            except grpc.RpcError:
                continue

        if votes > (len(self.peer_addresses) + 1) / 2:
            print(f"Process {self.id} wins election", flush=True)
            self.state = NodeState.LEADER
            self._send_heartbeat()

    def _send_heartbeat(self):
        for peer in self.peer_addresses:
            try:
                with grpc.insecure_channel(peer) as channel:
                    stub = raft_pb2_grpc.RaftStub(channel)
                    # print(f"Process {self.id} sends heartbeat to {peer}")
                    stub.AppendEntries(raft_pb2.AppendEntriesRequest(
                        term=self.current_term,
                        leader_id=self.id,
                        entries=[],
                        leader_commit=self.commit_index
                    ))
            except grpc.RpcError:
                continue