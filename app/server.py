import logging
import sys
import random
import time
import json

from redis_client import RedisClient
from request_lifecycle import Status

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] (%(processName)-10s) %(message)s',
    datefmt='%H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)]
)

class Server:
    def __init__(self, name, redis_config: dict, channels):
        self.name = name
        self._logger = logging.getLogger(__name__)

        self._redis_client = RedisClient(
            channels=channels,
            **redis_config
        )

    def start(self):
        self._redis_client.start_listening(
            callback=self._handle_incoming_request
        )

    def _handle_incoming_request(self, message):
        request = json.loads(message['data'])
        req_id = request['id']
        
        if random.choice([0, 1]) == 0:
            self._logger.info(f"Server {self.name}: Ignoring {req_id}")
            return

        self._logger.info(f"Server {self.name}: Interested in {req_id}. Processing...")
        time.sleep(random.uniform(0.5, 1.5))

        if self._redis_client.create_claim(req_id, self.name):
            self._logger.info(f"*** Server {self.name}: WON THE RACE for {req_id}! ***")
        
            update_data = {
                "status": Status.PICKED_UP.value,
                "picked_up_by": self.name
            }
            self._redis_client.update_request_hash(req_id, update_data)
        else:
            self._logger.info(f"Server {self.name}: LOST. Request taken by another server")