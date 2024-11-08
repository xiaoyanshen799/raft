package main

import (
	"context"
	"fmt"
	"log"
	"math/rand"
	"net"
	"sync"
	"time"

	pb "raft" // Import generated proto file

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
	voteCount      int32
	electionTimer  *time.Timer
	heartbeatTimer *time.Ticker
	mutex          sync.Mutex
}

func (rn *RaftNode) RequestVote(ctx context.Context, req *pb.RequestVoteRequest) (*pb.RequestVoteResponse, error) {
	fmt.Printf("Process %d received RequestVote from %d\n", rn.id, req.CandidateId)
	rn.mutex.Lock()
	defer rn.mutex.Unlock()
	// Election logic
	response := &pb.RequestVoteResponse{VoteGranted: true}
	return response, nil
}

func (rn *RaftNode) AppendEntries(ctx context.Context, req *pb.AppendEntriesRequest) (*pb.AppendEntriesResponse, error) {
	fmt.Printf("Process %d received AppendEntries from %d\n", rn.id, req.LeaderId)
	rn.heartbeatTimer.Reset(100 * time.Millisecond)
	rn.mutex.Lock()
	defer rn.mutex.Unlock()
	// Append entries to log...
	response := &pb.AppendEntriesResponse{Success: true}
	return response, nil
}

func (rn *RaftNode) ClientRequest(ctx context.Context, req *pb.ClientRequestMessage) (*pb.ClientResponseMessage, error) {
	if rn.state != Leader {
		return &pb.ClientResponseMessage{Success: false, Result: "Not the leader"}, nil
	}
	rn.appendEntriesToLog(req.Operation)
	return &pb.ClientResponseMessage{Success: true, Result: "Operation added to log"}, nil
}

func (rn *RaftNode) startElection() {
	rn.mutex.Lock()
	rn.state = Candidate
	rn.term++
	rn.voteCount = 1 // Vote for self
	rn.mutex.Unlock()

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
					rn.heartbeatTimer = time.NewTicker(100 * time.Millisecond)
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
				req := &pb.AppendEntriesRequest{Term: rn.term, LeaderId: rn.id}
				peer.AppendEntries(context.Background(), req)
				fmt.Printf("Process %d sends AppendEntries to Process %d\n", rn.id, rn.id)
			}(peer)
		}
	}
}

func (rn *RaftNode) appendEntriesToLog(command string) {
	rn.mutex.Lock()
	rn.log = append(rn.log, LogEntry{Term: rn.term, Command: command})
	fmt.Printf("Process %d appends command to its log: %s\n", rn.id, command)
	rn.mutex.Unlock()

	// Send the new log entry to followers
	for _, peer := range rn.peers {
		go func(peer pb.RaftClient) {
			req := &pb.AppendEntriesRequest{
				Term:         rn.term,
				LeaderId:     rn.id,
				Entries:      []*pb.LogEntry{{Term: rn.term, Command: command}},
				LeaderCommit: rn.commitIndex,
			}
			res, err := peer.AppendEntries(context.Background(), req)
			if err == nil && res.Success {
				fmt.Printf("Process %d received ACK from peer\n", rn.id)
			}
		}(peer)
	}
}

func main() {
	lis, err := net.Listen("tcp", ":50051")
	if err != nil {
		log.Fatalf("failed to listen: %v", err)
	}
	grpcServer := grpc.NewServer()
	raftNode := &RaftNode{id: 1}
	pb.RegisterRaftServer(grpcServer, raftNode)
	log.Printf("Process 1 started")
	go func() {
		for {
			time.Sleep(time.Duration(rand.Intn(150)+150) * time.Millisecond)
			if raftNode.state == Follower {
				raftNode.startElection()
			}
		}
	}()
	grpcServer.Serve(lis)
}
