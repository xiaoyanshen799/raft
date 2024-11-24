# Start from a base Go image
FROM golang:1.23-bullseye AS builder

# Set the working directory
WORKDIR /app

# Copy the Go module files and install dependencies
COPY go.mod  /app
COPY go.sum /app
RUN go mod download

RUN mkdir -p /app/logic

# Copy the rest of the application source code
COPY ./logic /app/logic
COPY raft_grpc.pb.go /app/
COPY raft.pb.go /app/

ENV GO111MODULE=on

RUN go mod tidy
ENV CGO_ENABLED=1
ENV GOOS=linux
ENV GOARCH=arm64

# Build the Raft application
RUN go build -o raft_node ./logic/main.go

# Set environment variables for node ID and peer addresses
ENV NODE_ID=1

# Expose the port for this node
EXPOSE 50051 50052 50053 50054 50055

# Run the Raft node application
CMD ["./raft_node"]
