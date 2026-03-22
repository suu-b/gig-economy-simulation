import logging
from models import Request
from request_lifecycle import Status
import uuid

logger = logging.getLogger(__name__)

class Client:
    def __init__(self, client_id: str, gateway, activation_event):
        self.client_id = client_id
        self.gateway = gateway
        self.activation_event = activation_event

    def start_loop(self):
        logger.info(f"CLIENT START: {self.client_id} is dormant and waiting...")
        
        while True:
            self.activation_event.wait()
            new_request = self._create_request()
            logger.info(f"{self.client_id}: Submitting {new_request.id} to Gateway.")
            self.gateway.post_request(new_request)
            
            self.activation_event.clear()
            logger.info(f"{self.client_id}: Returning to dormancy.")

    def _create_request(self) -> Request:
        return Request(
            id=f"REQ-{uuid.uuid4().hex[:6].upper()}",
            content=f"Payload from {self.client_id}",
        )