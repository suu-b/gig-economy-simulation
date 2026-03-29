from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from models import Request
import uvicorn

from redis_client import RedisClient
from models import App_Channels
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    redis_client.create_request_hash(req, 3600)
    redis_client.pub_request(req)
    return {"status": "submitted", "request_id": req.id}

@app.post("/stream/{request_id}")
def stream(request_id: str):
    def event_stream():
        pubsub = redis_client.instance.pubsub()
        pubsub.subscribe(f"progress:{request_id}")

        try:
            for message in pubsub.listen():
                if message['type'] != 'message':
                    continue
                
                data = message['data']
                yield f"data: {data}\n\n"
        finally:
            pubsub.close()

    return StreamingResponse(event_stream(), media_type="text/event-stream")

if __name__ == '__main__':
    uvicorn.run(app=app, host='0.0.0.0', port=8000)