import multiprocessing
import sys
import time
import random
import logging


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] (%(processName)-10s) %(message)s',
    datefmt='%H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def init_global_scope():
    
    # The global scope
    manager = multiprocessing.Manager()

    # The request namespace
    request_slot = manager.Namespace()
    request_slot.id = None
    request_slot.content = None

    # Winner Ledger
    # No one has won yet
    winner_ledger = manager.Value('u', "NONE")

    # Condition that allows servers to sleep until a request arrives
    broadcast = manager.Condition()

    # Winner lock to prevent race
    winner_lock = manager.Lock()

    return {
        "manager": manager,
        "request_slot": request_slot,
        "winner_ledger": winner_ledger,
        "broadcast": broadcast,
        "winner_lock": winner_lock,
    }

def create_new_request(client_name):
    return {
        "id": f"REQ-{client_name}-{int(time.time())}",
        "content": f"Task from {client_name}",
    }

def server_process(name, global_scope):
    logger.info(f"--- Server {name} is now on VIGIL ---")

    while True:
        with global_scope['broadcast']:
            global_scope['broadcast'].wait()
        
        request_id = global_scope['request_slot'].id

        # The server decides either to take it or not to take it
        decision = random.choice([0,1])
        logger.info(f"Server {name}: Woke up for Request {request_id}. Decision: {decision}")

        if decision == 1:
            delay = random.uniform(1, 2)
            time.sleep(delay)

            # Race to accept the request
            with global_scope['winner_lock']:
                if global_scope['winner_ledger'].value == 'NONE':
                    global_scope['winner_ledger'].value = name
                    logger.info(f"*** Server {name}: ACCEPTED Request {request_id} first! ***")
                else:
                    current_winner = global_scope['winner_ledger'].value 
                    logger.info(f"Server {name}: EXPIRED (Request {request_id} already taken by {current_winner})")
        else:
            logger.info(f"Server {name}: REJECTED Request {request_id} based on logic.")

def gateway_process(gateway_queue, global_scope):
    logger.info("Gateway is listening. Monitoring incoming queue...")

    while True:
        request = gateway_queue.get() 
        logger.info(f"Gateway: New request {request['id']} found. Resetting stage...")

        global_scope['winner_ledger'].value = 'NONE'

        with global_scope['broadcast']:
            global_scope['request_slot'].id = request['id']
            global_scope['request_slot'].content = request['content']
            
            logger.info(f"Gateway: broadcasting {request['id']} now!")
            global_scope['broadcast'].notify_all()

        final_winner = global_scope['winner_ledger'].value
        if final_winner != "NONE":
            logger.info(f"Gateway: {request['id']} was handled by {final_winner}")
        else:
            logger.warning(f"Gateway: {request['id']} EXPIRED (No server accepted)")

def client_process(client_id, gateway_queue, activation_event):
    logger.info(f"Client {client_id} is dormant.")
    
    while True:
        activation_event.wait()
        
        request = create_new_request(f"Client-{client_id}")
        logger.info(f"Client {client_id}: Submitting {request['id']} to Gateway.")
        
        gateway_queue.put(request)
        
        activation_event.clear()
        logger.info(f"Client {client_id}: Returning to dormancy.")

def master_process():
    global_scope = init_global_scope()
    logger.info("Global scope initialized")
    gateway_queue = multiprocessing.Queue()
    
    number_of_servers = 3

    logger.info(f"Spawning {number_of_servers} server processes")
    for i in range(number_of_servers):
        p = multiprocessing.Process(target=server_process, args=(f"Srv-{i}", global_scope), daemon=True)
        p.start()
    logger.info(f"Spawned all!")

    logger.info("Spinning up the gateway")

    multiprocessing.Process(
        target=gateway_process, 
        args=(gateway_queue, global_scope), 
        name="Gateway", 
        daemon=True
    ).start()

    number_of_clients = 2
    client_triggers = {}
    logger.info(f"Spawning {number_of_clients} client processes")
    for i in range(number_of_clients):
        trigger = multiprocessing.Event()
        client_triggers[i] = trigger
        p = multiprocessing.Process(target=client_process, args=(i, gateway_queue, trigger), daemon=True)
        p.start()

    time.sleep(1) # let all spawn
    logger.info(f"Spawned all!")


    logger.info("\nREADY. Type '0' to trigger Client 0, '1' for Client 1, or 'q' to quit.")
    while True:
        cmd = input("Command > ").strip()
        if cmd == 'q':
            break
        elif cmd.isdigit() and int(cmd) in client_triggers:
            client_triggers[int(cmd)].set()
        else:
            logger.info("Invalid command. Try 0, 1, or q.")


if __name__ == "__main__":
    master_process()