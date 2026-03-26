from fastapi import FastAPI
from models import Request
import uvicorn

from system import System
from redis_client import RedisClient
from models import App_Channels

app = FastAPI()

redis_client = RedisClient(
    channels=App_Channels(request_channel="broadcast:requests"),
    host="localhost",
    port=6379
)

@app.post("/request")
def create_request(req: Request):
    redis_client.create_request_hash(req, 3600)
    redis_client.pub_request(req)
    return {"status": "submitted"}

if __name__ == '__main__':
    uvicorn.run(app=app, host='0.0.0.0', port=8000)