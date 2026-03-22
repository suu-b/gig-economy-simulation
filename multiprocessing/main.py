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
logger.setLevel(logging.INFO)

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


def client_process(name, global_scope, activation_event):
    logger.info(f"--- Client {name} is DORMANT and waiting for activation ---")

    while True:
        # wait for activation
        activation_event.wait()

        logger.info(f"Client {name} woke up! Creating a request")
        global_scope['winner_ledger'].value = 'NONE'

        # Create request
        global_scope['request_slot'].id = f"REQ-{name}-{int(time.time())}"
        global_scope['request_slot'].content = "Some task"


        with global_scope['broadcast']:
            logger.info("Notifying all servers about the request...")
            global_scope['broadcast'].notify_all()

        time.sleep(3)
        final_winner = global_scope['winner_ledger'].value
        if final_winner != "NONE":
            logger.info(f"[Client {name}] SUCCESS: Request handled by {final_winner}")
        else:
            logger.info(f"[Client {name}] FAILURE: No server accepted the request.")

        activation_event.clear()
        logger.info(f"--- Client {name} is now DORMANT again ---\n")


def master_process():
    global_scope = init_global_scope()
    logger.info("Global scope initialized")
    
    number_of_servers = 3

    logger.info(f"Spawning {number_of_servers} server processes")
    for i in range(number_of_servers):
        p = multiprocessing.Process(target=server_process, args=(f"Srv-{i}", global_scope), daemon=True)
        p.start()
    logger.info(f"Spawned all!")

    number_of_clients = 2
    client_triggers = {}
    logger.info(f"Spawning {number_of_clients} client processes")
    for i in range(number_of_clients):
        trigger = multiprocessing.Event()
        client_triggers[i] = trigger
        p = multiprocessing.Process(target=client_process, args=(i, global_scope, trigger), daemon=True)
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
    
    
    
    