FROM golang:1.17
WORKDIR /app
COPY . .
RUN go build -o raft_server .
CMD ["./raft_server"]
