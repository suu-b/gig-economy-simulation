import multiprocessing
import sys
import time
import random
import logging
import redis

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] (%(processName)-10s) %(message)s',
    datefmt='%H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

REDIS_CONF = {
    'host': 'localhost',
    'port': 6379,
    'decode_responses': True
}

CH_REQUESTS = "broadcast:requests"  
KEY_REQ_DATA = "req_data:{req_id}"    
KEY_WINNER = "winner:{req_id}"        

def get_redis_conn():
    """Utility to get a fresh Redis connection."""
    return redis.Redis(**REDIS_CONF)

def create_new_request(client_name):
    return {
        "id": f"REQ-{client_name}-{int(time.time())}",
        "content": f"Task from {client_name}",
        "timestamp": time.time()
    }

def server_process(name):
    r = get_redis_conn()
    pubsub = r.pubsub()
    pubsub.subscribe(CH_REQUESTS)
    
    logger.info(f"--- Server {name} tuned into {CH_REQUESTS} ---")

    for message in pubsub.listen():
        if message['type'] != 'message':
            continue
            
        req_id = message['data']
        
        if random.choice([0, 1]) == 1:
            logger.info(f"Server {name}: Interested in {req_id}. Processing...")
            time.sleep(random.uniform(1, 2))

            if r.set(f"winner:{req_id}", name, nx=True, ex=60):
                logger.info(f"*** Server {name}: WON THE RACE for {req_id}! ***")
                
                r.hset(f"req_data:{req_id}", mapping={
                    "status": "picked_up",
                    "winner": name
                })
            else:
                winner = r.get(f"winner:{req_id}")
                logger.info(f"Server {name}: EXPIRED ({req_id} taken by {winner})")
        else:
            logger.info(f"Server {name}: Ignoring {req_id}")

def gateway_process(gateway_queue):
    r = get_redis_conn()
    logger.info("GATEWAY START: Monitoring incoming queue...")

    while True:
        request = gateway_queue.get() 
        req_id = request['id']

        r.hset(f"req_data:{req_id}", mapping={
            "id": req_id,
            "content": request['content'],
            "status": "pending",
            "timestamp": request['timestamp']
        })
        r.expire(f"req_data:{req_id}", 3600)

        r.publish(CH_REQUESTS, req_id)
        logger.info(f"Gateway: Broadcasted {req_id} to all listeners.")

def client_process(client_id, gateway_queue, activation_event):
    logger.info(f"CLIENT START: Client {client_id} is dormant.")
    
    while True:
        activation_event.wait()
        
        request = create_new_request(f"Client-{client_id}")
        logger.info(f"Client {client_id}: Submitting {request['id']} to Gateway.")
        
        gateway_queue.put(request)
        
        activation_event.clear()
        logger.info(f"Client {client_id}: Returning to dormancy.")

def main():
    try:
        get_redis_conn().ping()
    except Exception as e:
        logger.error(f"Redis not found. Error: {e}")
        return

    gateway_queue = multiprocessing.Queue()
    
    for i in range(3):
        multiprocessing.Process(target=server_process, args=(f"Srv-{i}",), name=f"Srv-{i}", daemon=True).start()

    multiprocessing.Process(target=gateway_process, args=(gateway_queue,), name="Gateway", daemon=True).start()

    client_triggers = {}
    for i in range(2):
        trigger = multiprocessing.Event()
        client_triggers[i] = trigger
        multiprocessing.Process(target=client_process, args=(i, gateway_queue, trigger), name=f"Client-{i}", daemon=True).start()

    time.sleep(1)
    print("Type '0' or '1' to trigger clients, or 'q' to quit.")

    while True:
        try:
            cmd = input("Command > ").strip().lower()
            if cmd == 'q':
                break
            elif cmd.isdigit() and int(cmd) in client_triggers:
                client_triggers[int(cmd)].set()
            else:
                print("Invalid command. Try 0, 1, or q.")
        except EOFError:
            break

if __name__ == "__main__":
    main()