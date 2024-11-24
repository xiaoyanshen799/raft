import os
import sys
import grpc
import signal
import logging
from concurrent import futures
import raft_pb2
import raft_pb2_grpc
from node import RaftNode

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - Node %(message)s'
)
logger = logging.getLogger(__name__)


def get_config():
    """从环境变量获取配置"""
    try:
        node_id = int(os.environ.get('NODE_ID'))
        port = int(os.environ.get('PORT'))
        peers_str = os.environ.get('PEERS', '')
        peers = [p.strip() for p in peers_str.split(',') if p.strip()]

        return node_id, port, peers
    except (ValueError, TypeError) as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)


def serve():
    """启动GRPC服务器"""
    # 获取配置
    node_id, port, peers = get_config()

    # 创建服务器
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # 创建Raft节点并添加到服务器
    raft_node = RaftNode(node_id, peers)
    raft_pb2_grpc.add_RaftServicer_to_server(raft_node, server)

    # 添加服务器端口
    server.add_insecure_port(f'[::]:{port}')

    # 启动服务器
    server.start()
    logger.info(f"Node {node_id} started on port {port}")
    logger.info(f"Peers: {peers}")

    # 注册关闭信号处理
    def handle_shutdown(signum, frame):
        logger.info(f"Node {node_id} shutting down...")
        server.stop(0)
        sys.exit(0)

    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        server.stop(0)
        logger.info(f"Node {node_id} stopped by keyboard interrupt")
    except Exception as e:
        logger.error(f"Node {node_id} error: {e}")
        server.stop(0)
        sys.exit(1)


if __name__ == '__main__':
    serve()