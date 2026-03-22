import multiprocessing
import logging
from models import Request

logger = logging.getLogger(__name__)

class Gateway:
    def __init__(self, redis_client):
        self._queue = multiprocessing.Queue()
        self._redis_client = redis_client
        self._ttl = 3600 # in seconds
        
        self._worker_process = multiprocessing.Process(
            target=self._worker_loop, 
            name="GatewayDaemon",
            daemon=True 
        )

    def start(self):
        if not self._worker_process.is_alive():
            self._worker_process.start()
            logger.info("Gateway daemon started.")

    def post_request(self, request: Request):
        self._queue.put(request)
        logger.info(f"Queued request: {request.id}")

    def _worker_loop(self):
        logger.info("Worker loop is now running...")
        while True:
            try:
                request = self._queue.get()
                self._redis_client.create_request_hash(request, self._ttl)
                self._redis_client.pub_request(request)
                
            except Exception as e:
                logger.error(f"Error in Gateway daemon: {e}")