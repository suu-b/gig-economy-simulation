from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from models import Request
import uvicorn
import logging

from redis_client import RedisClient
from models import App_Channels
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
redis_client = RedisClient(
    channels=App_Channels(request_channel="broadcast:requests"),
    host="localhost",
    port=6379
)

@app.post("/request")
def create_request(req: Request):
    logger.info(f"Received request payload: {req.dict()}")
    redis_client.create_request_hash(req, 3600)
    redis_client.pub_request(req)
    logger.info(f"Request {req.id} submitted successfully")
    return {"status": "submitted", "request_id": req.id}

@app.get("/stream/{request_id}")
def stream(request_id: str):
    def event_stream():
        pubsub = redis_client.instance.pubsub()
        pubsub.subscribe(f"progress:{request_id}")

        try:
            for message in pubsub.listen():
                if message['type'] != 'message':
                    continue
                
                data = message['data']
                logger.info(f"Stream payload for {request_id}: {data}")
                yield f"data: {data}\n\n"
        finally:
            pubsub.close()

    return StreamingResponse(event_stream(), media_type="text/event-stream")

@app.get("/history")
def get_history(limit: int = 20):
    logger.info(f"Fetching history with limit: {limit}")
    ids = redis_client.instance.lrange("requests:completed", 0, limit - 1)
    logger.info(f"Retrieved {len(ids)} completed request IDs")

    results = []
    # ignore if pylance throws error here
    for req_id in ids:
        data =  redis_client.instance.hgetall(f"request_data:{req_id}")

        if not data:
            continue

        result_item = {
            "request_id": data.get("id"),
            "client_id": data.get("client_id"),
            "status": data.get("status"),
            "server_id": data.get("picked_up_by"),
            "completed_at": data.get("completed_at"),
            "duration": data.get("duration"),
            "created_at":  data.get("created_at"),
        }
        logger.debug(f"History payload: {result_item}")
        results.append(result_item)

    logger.info(f"Returning {len(results)} historical records")
    return results

if __name__ == '__main__':
    uvicorn.run(app=app, host='0.0.0.0', port=8000)