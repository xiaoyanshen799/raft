package main

import (
	"context"
	"fmt"
	"log"
	"math/rand"
	"net"
	"os"
	"strconv"
	"strings"
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
	Index   int32
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
	leaderId       int32
}

func NewRaftNode(id int32, peerAddresses []string) *RaftNode {
	rn := &RaftNode{
		id:            id,
		state:         Follower,
		term:          0,
		log:           []LogEntry{},
		commitIndex:   0,
		lastApplied:   0,
		electionTimer: time.NewTimer(time.Duration(rand.Intn(150)+150) * time.Millisecond),
	}

	go func() {
		for _, addr := range peerAddresses {
			if addr != fmt.Sprintf("localhost:%d", 50050+id) { // Skip self-address
				conn, err := grpc.Dial(addr, grpc.WithInsecure(), grpc.WithBlock(), grpc.WithTimeout(time.Second*5))
				if err != nil {
					log.Printf("Failed to connect to peer %s: %v", addr, err)
					continue
				}
				fmt.Printf("Process %d connected to peer at %s\n", id, addr)
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

	// Start election
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
				if rn.voteCount > int32((len(rn.peers)+1)/2) && rn.state == Candidate {
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
	fmt.Printf("req.term %d, rn.term %d Process %d received RPC AppendEntries from %d\n", req.Term, rn.term, rn.id, req.LeaderId)
	rn.mutex.Lock()
	defer rn.mutex.Unlock()
    //fmt.Printf("req.term %d, rn.term %d Process %d received RPC AppendEntries from %d\n", req.Term, rn.term, rn.id, req.LeaderId)
	// Only reset if the term is valid (leader's term is greater than or equal to follower's term)
	if req.Term >= rn.term {
		rn.state = Follower
		rn.term = req.Term
		// Reset the election timer to prevent this node from starting a new election
		rn.electionTimer.Reset(time.Duration(rand.Intn(150)+150) * time.Millisecond)
		// set leader id
		rn.leaderId = req.LeaderId
		fmt.Printf("Process %d received RPC AppendEntries from %d\n", rn.id, req.LeaderId)
		if(req.Entries != nil){
		    for _, entry := range req.Entries {
		                rn.log = append(rn.log, LogEntry{
		                    Term:    entry.Term,
		                    Command: entry.Command,
		                    Index:   entry.Index,
                        })
                        fmt.Printf("Process %d appended log entry at index %d: %s\n", rn.id, entry.Index, entry.Command)
            }
        }

		return &pb.AppendEntriesResponse{Success: true}, nil
	}

	return &pb.AppendEntriesResponse{Success: false}, nil
}

func (rn *RaftNode) RequestVote(ctx context.Context, req *pb.RequestVoteRequest) (*pb.RequestVoteResponse, error) {
	fmt.Printf("Process %d received RequestVote from %d\n", rn.id, req.CandidateId)
	rn.mutex.Lock()
	defer rn.mutex.Unlock()

	if req.Term < rn.term {
		return &pb.RequestVoteResponse{VoteGranted: false}, nil
	}

	// Step down if we see a higher term and reset election timer
	if req.Term > rn.term {
		rn.term = req.Term
		rn.state = Follower
		rn.electionTimer.Reset(time.Duration(rand.Intn(150)+150) * time.Millisecond)
	}

	return &pb.RequestVoteResponse{VoteGranted: true}, nil
}

func (rn *RaftNode) executeLogEntries() {
	for rn.lastApplied < rn.commitIndex {
		rn.lastApplied++
		entry := rn.log[rn.lastApplied-1]
		fmt.Printf("Process %d executed log entry at index %d: %s\n", rn.id, entry.Index, entry.Command)
	}
}

func (rn *RaftNode) ClientRequest(ctx context.Context, req *pb.ClientRequestMessage) (*pb.ClientResponseMessage, error) {
	rn.mutex.Lock()
	defer rn.mutex.Unlock()

	// Only leader handles client requests
	if rn.state != Leader {
		// Forward request to the leader
		if rn.leaderId != 0 && int(rn.leaderId) <= (len(rn.peers)+1) {
			fmt.Printf("Process %d forwards client request to leader %d\n", rn.id, rn.leaderId)
			return rn.peers[rn.leaderId-1].ClientRequest(ctx, req)
		}
		fmt.Println("leadid", rn.leaderId)
		return &pb.ClientResponseMessage{
			Success: false,
			Result:  "Not the leader, cannot process request",
		}, nil
	}

	// Append the operation to the leader's log
	newIndex := int32(len(rn.log) + 1)
	entry := LogEntry{
		Term:    rn.term,
		Command: req.Operation,
		Index:   newIndex,
	}
	rn.log = append(rn.log, entry)
	fmt.Printf("Process %d (Leader) appends operation '%s' to log at index %d\n", rn.id, req.Operation, newIndex)

	// Start log replication to followers
	successCount := 1 // Leader's own ACK
	for _, peer := range rn.peers {
		go func(peer pb.RaftClient) {
			res, err := peer.AppendEntries(context.Background(), &pb.AppendEntriesRequest{
				Term:         rn.term,
				LeaderId:     rn.id,
				Entries:      []*pb.LogEntry{{Term: entry.Term, Command: entry.Command, Index: entry.Index}},
				LeaderCommit: rn.commitIndex,
			})
			if err == nil && res.Success {
				rn.mutex.Lock()
				successCount++
				if successCount > (len(rn.peers)+1)/2 {
					// Majority ACKs received, commit the log
					rn.commitIndex = newIndex
					rn.executeLogEntries()
				}
				rn.mutex.Unlock()
			}
		}(peer)
	}

	// Respond to client
	return &pb.ClientResponseMessage{
		Success: true,
		Result:  fmt.Sprintf("Operation '%s' added to log", req.Operation),
	}, nil
}

func main() {
	// Read Node ID and peer addresses from environment variables
	nodeIDStr := os.Getenv("NODE_ID")
	nodeID, err := strconv.Atoi(nodeIDStr)
	if err != nil {
		log.Fatalf("Invalid NODE_ID: %v", err)
	}

	// Use service names to form peer addresses
	allPeerAddresses := os.Getenv("PEER_ADDRESSES")
	if allPeerAddresses == "" {
		log.Fatal("PEER_ADDRESSES environment variable is not set")
	}

	// Parse peer addresses into a list
	peerList := strings.Split(allPeerAddresses, ",")

	// Exclude self from the peer list
	var peerAddresses []string
	for _, addr := range peerList {
		if addr != fmt.Sprintf("node%d:5005%d", nodeID, nodeID) {
			peerAddresses = append(peerAddresses, addr)
		}
	}

	raftNode := NewRaftNode(int32(nodeID), peerAddresses)

	// Set up the gRPC server
	port := 50050 + nodeID
	lis, err := net.Listen("tcp", fmt.Sprintf(":%d", port))
	if err != nil {
		log.Fatalf("Failed to listen on port %d: %v", port, err)
	}

	grpcServer := grpc.NewServer()
	pb.RegisterRaftServer(grpcServer, raftNode)

	// Election timer handling
	go func() {
		for {
			select {
			case <-raftNode.electionTimer.C:
				if raftNode.state != Leader {
					raftNode.startElection()
				}
			}
		}
	}()

	fmt.Printf("Raft node %d is listening on port %d\n", nodeID, port)
	if err := grpcServer.Serve(lis); err != nil {
		log.Fatalf("Failed to serve gRPC server: %v", err)
	}
}
