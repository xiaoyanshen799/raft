package main

import (
	"context"
	"fmt"
	"log"
	pb "raft"

	"google.golang.org/grpc"
)

func sendClientRequest(addr string, operation string) {
	conn, err := grpc.Dial(addr, grpc.WithInsecure())
	if err != nil {
		log.Fatalf("Failed to connect to %s: %v", addr, err)
	}
	defer conn.Close()

	client := pb.NewRaftClient(conn)
	res, err := client.ClientRequest(context.Background(), &pb.ClientRequestMessage{
		Operation: operation,
	})
	if err != nil {
		log.Fatalf("Failed to send client request: %v", err)
	}

	fmt.Printf("Client received response: Success=%t, Result=%s\n", res.Success, res.Result)
}

func main() {
//     // Send a client add request to the server - case 5
// 	sendClientRequest("localhost:50051", "add")
//
// 	// Send a client subtract request to the server - case 6
// 	sendClientRequest("localhost:50051", "subtract")
//
// 	// Send a client subtract request to the server - case 6
// 	sendClientRequest("localhost:50053", "subtract")

	// Send a client subtract request to the server - case 6
	sendClientRequest("localhost:50052", "subtract")
}
