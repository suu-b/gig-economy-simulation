import logging
import sys

from redis_client import RedisClient
from models import Request

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] (%(processName)-10s) %(message)s',
    datefmt='%H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)]
)

class Gateway:
    def __init__(self, redis_config: dict, channels, queue):
        self._queue = queue
        self._redis_client = RedisClient(
            channels=channels,
            **redis_config
        )
        self._ttl = 3600
        self._logger = logging.getLogger(__name__)

    def run(self):
        self._logger.info("Worker loop is now running...")
        while True:
            try:
                request = self._queue.get()
                self._redis_client.create_request_hash(request, self._ttl)
                self._redis_client.pub_request(request)
            except Exception as e:
                self._logger.error(f"Error in Gateway: {e}")

    def post_request(self, request: Request):
        self._queue.put(request)
        self._logger.info(f"Queued request: {request.id}")