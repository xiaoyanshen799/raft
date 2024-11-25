import unittest
import time
from client import RaftClient


class TestRaftClient(unittest.TestCase):
    def setUp(self):
        """在每个测试用例前运行"""
        # 给系统一些时间完成leader选举
        time.sleep(2)

    def test_go_node_request(self):
        """Test Case 1: 测试Go节点的请求处理"""
        client = RaftClient('localhost:50054')
        success, result = client.send_request('test_operation')
        self.assertIsNotNone(result)
        print(f"Go Node Test - Success: {success}, Result: {result}")

    def test_python_node_request(self):
        """Test Case 2: 测试Python节点的请求处理"""
        client = RaftClient('localhost:50051')
        success, result = client.send_request('test_operation')
        self.assertIsNotNone(result)
        print(f"Python Node Test - Success: {success}, Result: {result}")

    def test_leader_node_request(self):
        """Test Case 3: 测试Leader节点的请求处理"""
        client = RaftClient('localhost:50052')
        success, result = client.send_request('test_operation')
        self.assertIsNotNone(result)
        print(f"Leader Node Test - Success: {success}, Result: {result}")

    def test_follower_node_request(self):
        """Test Case 4: 测试Follower节点的请求处理"""
        client = RaftClient('localhost:50053')
        success, result = client.send_request('test_operation')
        self.assertIsNotNone(result)
        print(f"Follower Node Test - Success: {success}, Result: {result}")

    def test_multiple_operations(self):
        """Test Case 5: 测试多个连续操作"""
        client = RaftClient('localhost:50051')
        operations = ['op1', 'op2', 'op3']

        for op in operations:
            success, result = client.send_request(op)
            self.assertTrue(success)
            self.assertIsNotNone(result)
            print(f"Multiple Operations Test - Operation: {op}, Success: {success}, Result: {result}")

    def test_node_failure_recovery(self):
        """Test Case 6: 测试节点失败和恢复情况"""
        # 首先确保可以连接
        client = RaftClient('localhost:50051')
        success, result = client.send_request('test_before_failure')
        self.assertTrue(success)

        # 模拟节点失败（这里需要实现一个方法来模拟节点失败）
        time.sleep(2)  # 等待系统重新选举

        # 测试系统是否仍然可用
        success, result = client.send_request('test_after_failure')
        self.assertTrue(success)
        print(f"Failure Recovery Test - Success: {success}, Result: {result}")

    def test_concurrent_requests(self):
        """Test Case 7: 测试并发请求处理"""
        import threading

        def send_concurrent_request(client, operation):
            success, result = client.send_request(operation)
            print(f"Concurrent Test - Operation: {operation}, Success: {success}, Result: {result}")

        client = RaftClient('localhost:50051')
        threads = []

        # 创建多个并发请求
        for i in range(5):
            thread = threading.Thread(
                target=send_concurrent_request,
                args=(client, f'concurrent_op_{i}')
            )
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()


if __name__ == '__main__':
    unittest.main(verbosity=2)