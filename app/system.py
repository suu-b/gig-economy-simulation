import multiprocessing
import sys
import time
import random
import logging
import redis

from models import App_Channels, Request
from redis_client import RedisClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] (%(processName)-10s) %(message)s',
    datefmt='%H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)]
)


class System:
    def __init__(self):
        # Redis client params
        host = 'localhost'
        port = 6379
        channels = App_Channels(request_channel="broadcast:requests")

        self.redis_client = RedisClient(channels=channels, host=host, port=port,decode_responses=True)
        self.logger = logging.getLogger(__name__)

        

        