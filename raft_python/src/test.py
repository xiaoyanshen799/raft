from client import RaftClient

if __name__ == '__main__':
    # # TEST CLIENT case 1 for go node
    # client = RaftClient('localhost:50054')
    # success, result = client.send_request('test_operation')
    # print(f"Success: {success}, Result: {result}")

    # TEST CLIENT case 2 
    client = RaftClient('localhost:50054')
    success, result = client.send_request('test_operation')
    print(f"Success: {success}, Result: {result}")

    # # TEST CLIENT case 3 for Leader node
    # client = RaftClient('localhost:50053')
    # success, result = client.send_request('test_operation')
    # print(f"Success: {success}, Result: {result}")
    #
    # # TEST CLIENT case 4 for Follower node
    # # case 5 is in the golang test file - client.go
    # client = RaftClient('localhost:50052')
    # success, result = client.send_request('test_operation')
    # print(f"Success: {success}, Result: {result}")