# Distributed Raft Consensus Implementation

This project implements a distributed Raft consensus algorithm using both Python and Go, demonstrating cross-language communication via gRPC.

## Project Structure
```
.
├── proto
│   ├── raft.pb.go
│   ├── raft.proto
│   └── raft_grpc.pb.go
├── raft_go
│   ├── Dockerfile
│   ├── client
│   │   └── client.go
│   ├── docker-compose.yml
│   ├── go.mod
│   ├── go.sum
│   ├── logic
│   │   └── main.go
│   ├── raft.pb.go
│   └── raft_grpc.pb.go
└── raft_python
    ├── Dockerfile
    ├── docker-compose.yml
    ├── proto
    │   └── raft.proto
    ├── requirements.txt
    └── src
        ├── client.py
        ├── main.py
        ├── node.py
        ├── raft_pb2.py
        ├── raft_pb2_grpc.py
        ├── state.py
        └── test.py
```

## Features

- Leader Election
- Log Replication
- Cross-language communication (Python and Go)
- Docker containerization
- gRPC-based communication
- Fault tolerance

## Prerequisites

- Docker and Docker Compose
- Python 3.9+
- Go 1.19+
- Protocol Buffers compiler
- gRPC tools

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd raft-implementation
```

2. Install Python dependencies:
```bash
cd raft_python
pip install -r requirements.txt
```

3. Install Go dependencies:
```bash
cd ../raft_go
go mod download
```

4. Generate Protocol Buffers code:

For Python:
```bash
cd raft_python
python -m grpc_tools.protoc -I../proto --python_out=./src --grpc_python_out=./src ../proto/raft.proto
```

For Go:
```bash
cd raft_go
protoc --go_out=. --go_opt=paths=source_relative \
    --go-grpc_out=. --go-grpc_opt=paths=source_relative \
    ../proto/raft.proto
```

## Running the Cluster

1. Start the entire cluster using Docker Compose:
```bash
docker-compose up --build
```

This will start 5 nodes (3 Python nodes and 2 Go nodes) in separate containers.

## Testing

1. Run the Python client:
```bash
cd raft_python
python src/client.py
```

2. Run the Go client:
```bash
cd raft_go
go run client/client.go
```

## Implementation Details

### Node States
- Follower
- Candidate
- Leader

### Key Components
- Leader Election
- Log Replication
- Client Request Handling
- Heartbeat Mechanism

### Configuration

Environment variables for each node:
- `NODE_ID`: Unique identifier for each node
- `PORT`: Port number for gRPC server
- `PEERS`: Comma-separated list of peer addresses

## Docker Configuration

The cluster uses a custom bridge network to enable communication between containers. Each node runs in its own container with the following port mappings:

- Python Node 1: 50051
- Python Node 2: 50052
- Python Node 3: 50053
- Go Node 1: 50054
- Go Node 2: 50055

## Protocol Definition

The Raft protocol is defined in `proto/raft.proto` and includes:
```protobuf
service Raft {
  rpc RequestVote(RequestVoteRequest) returns (RequestVoteResponse);
  rpc AppendEntries(AppendEntriesRequest) returns (AppendEntriesResponse);
  rpc ClientRequest(ClientRequestMessage) returns (ClientResponseMessage);
}
```

## Troubleshooting

Common issues and solutions:
1. Connection refused
   - Ensure all containers are running
   - Check network configuration
   - Verify port mappings

2. Protocol Buffer version mismatch
   - Install protobuf version 5.27.0 or higher
   - Regenerate protocol buffer code

3. Node communication issues
   - Check PEERS environment variable configuration
   - Verify network connectivity between containers

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
