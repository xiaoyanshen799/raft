from client import RaftClient

if __name__ == '__main__':
    client = RaftClient('localhost:50054')
    success, result = client.send_request('test_operation')
    print(f"Success: {success}, Result: {result}")