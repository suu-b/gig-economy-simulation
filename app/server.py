import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] (%(processName)-10s) %(message)s',
    datefmt='%H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)]
)

class Server:
    def __init__(self, name, redis_client):
        self.name = name
        self._logger = logging.getLogger(__name__)
        self._redis_client = redis_client

    def start(self):
        self._redis_client.start_listening(callback=self._handle_incoming_request)

    def _handle_incoming_request(self, message):
        req_id = message['data']
        
        if random.choice([0, 1]) == 0:
            logger.info(f"Server {self.name}: Ignoring {req_id}")
            return

        logger.info(f"Server {self.name}: Interested in {req_id}. Processing...")
        time.sleep(random.uniform(0.5, 1.5)) # Simulate some "thinking" time

        if self._redis.create_claim(req_id, self.name):
            logger.info(f"*** Server {self.name}: WON THE RACE for {req_id}! ***")
        
            update_data = {
                "status": Status.PICKED_UP.value,
                "picked_up_by": self.name
            }
            self._redis.update_request_hash(req_id, update_data)
        else:
            logger.info(f"Server {self.name}: LOST. Request taken other server")

