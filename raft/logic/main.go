package main

import (
	"context"
	"fmt"
	"log"
	"math/rand"
	"net"
	"sync"
	"time"

	pb "raft" // Replace with actual path to the generated proto

	"google.golang.org/grpc"
)

type State int

const (
	Follower State = iota
	Candidate
	Leader
)

type LogEntry struct {
	Term    int32
	Command string
}

type RaftNode struct {
	pb.UnimplementedRaftServer
	id             int32
	state          State
	term           int32
	log            []LogEntry
	commitIndex    int32
	lastApplied    int32
	peers          []pb.RaftClient
	peerAddresses  []string
	voteCount      int32
	electionTimer  *time.Timer
	heartbeatTimer *time.Ticker
	mutex          sync.Mutex
}

func NewRaftNode(id int32, peerAddresses []string) *RaftNode {
	rn := &RaftNode{
		id:            id,
		state:         Follower,
		term:          0,
		log:           []LogEntry{},
		commitIndex:   0,
		lastApplied:   0,
		electionTimer: time.NewTimer(time.Duration(rand.Intn(150)+150) * time.Millisecond), // Initialize electionTimer
	}

	// Initialize gRPC clients for each peer
	go func() {
		for _, addr := range peerAddresses {
			if addr != fmt.Sprintf("localhost:%d", 50050+id) { // Skip self-address
				conn, err := grpc.Dial(addr, grpc.WithInsecure(), grpc.WithBlock(), grpc.WithTimeout(time.Second*30))
				if err != nil {
					log.Fatalf("Failed to connect to peer %s: %v", addr, err)
				}
				fmt.Print("connect : %s", conn.GetState())
				rn.peers = append(rn.peers, pb.NewRaftClient(conn))
			}
		}
	}()
	return rn
}

func (rn *RaftNode) startElection() {
	rn.mutex.Lock()
	defer rn.mutex.Unlock()

	// Ensure there are at least 5 nodes before starting an election
	for len(rn.peers) < 4 { // 4 peers + self = 5 nodes
		fmt.Printf("Process %d: Not enough nodes to start election\n", rn.id)
		time.Sleep(time.Second * 5)
	}

	rn.state = Candidate
	rn.term++
	rn.voteCount = 1 // Vote for itself
	fmt.Printf("Process %d starts election for term %d\n", rn.id, rn.term)

	// Send RequestVote RPC to all peers
	for _, peer := range rn.peers {
		go func(peer pb.RaftClient) {
			req := &pb.RequestVoteRequest{
				Term:        rn.term,
				CandidateId: rn.id,
			}
			res, err := peer.RequestVote(context.Background(), req)
			if err == nil && res.VoteGranted {
				rn.mutex.Lock()
				rn.voteCount++
				if rn.voteCount > int32(len(rn.peers)/2) && rn.state == Candidate {
					fmt.Printf("Process %d wins the election and becomes the leader\n", rn.id)
					rn.state = Leader
					rn.heartbeatTimer = time.NewTicker(1000 * time.Millisecond)
					go rn.sendHeartbeats()
				}
				rn.mutex.Unlock()
			}
		}(peer)
	}
}

func (rn *RaftNode) sendHeartbeats() {
	for range rn.heartbeatTimer.C {
		for _, peer := range rn.peers {
			go func(peer pb.RaftClient) {
				req := &pb.AppendEntriesRequest{
					Term:         rn.term,
					LeaderId:     rn.id,
					Entries:      []*pb.LogEntry{}, // Empty entries as heartbeat
					LeaderCommit: rn.commitIndex,
				}
				_, err := peer.AppendEntries(context.Background(), req)
				if err != nil {
					fmt.Printf("Failed to send AppendEntries to peer: %v\n", err)
				}
			}(peer)
		}
	}
}

func (rn *RaftNode) AppendEntries(ctx context.Context, req *pb.AppendEntriesRequest) (*pb.AppendEntriesResponse, error) {
	fmt.Printf("Process %d received AppendEntries from %d\n", rn.id, req.LeaderId)
	rn.mutex.Lock()
	defer rn.mutex.Unlock()

	if req.Term < rn.term {
		return &pb.AppendEntriesResponse{Success: false}, nil
	}

	rn.state = Follower
	rn.term = req.Term
	rn.electionTimer.Reset(time.Duration(rand.Intn(150)+150) * time.Millisecond) // Reset election timer upon heartbeat
	return &pb.AppendEntriesResponse{Success: true}, nil
}

func (rn *RaftNode) RequestVote(ctx context.Context, req *pb.RequestVoteRequest) (*pb.RequestVoteResponse, error) {
	fmt.Printf("Process %d received RequestVote from %d\n", rn.id, req.CandidateId)
	rn.mutex.Lock()
	defer rn.mutex.Unlock()

	if req.Term < rn.term {
		return &pb.RequestVoteResponse{VoteGranted: false}, nil
	}

	rn.term = req.Term
	rn.state = Follower
	rn.electionTimer.Reset(time.Duration(rand.Intn(150)+150) * time.Millisecond) // Reset election timer
	return &pb.RequestVoteResponse{VoteGranted: true}, nil
}

func main() {
	nodeID := int32(6) // Set this ID uniquely for each node
	peerAddresses := []string{
		"localhost:50051",
		"localhost:50052",
		"localhost:50053",
		"localhost:50054",
		"localhost:50055",
	}

	raftNode := NewRaftNode(nodeID, peerAddresses)

	lis, err := net.Listen("tcp", fmt.Sprintf("localhost:%d", 50050+nodeID))
	if err != nil {
		log.Fatalf("Failed to listen on port %d: %v", 50050+nodeID, err)
	}

	grpcServer := grpc.NewServer()
	pb.RegisterRaftServer(grpcServer, raftNode)

	go func() {
		for {
			select {
			case <-raftNode.electionTimer.C:
				if raftNode.state == Follower {
					raftNode.startElection()
				}
			}
		}
	}()

	fmt.Printf("Raft node %d is listening on port %d\n", nodeID, 50050+nodeID)
	if err := grpcServer.Serve(lis); err != nil {
		log.Fatalf("Failed to serve gRPC server: %v", err)
	}
}
