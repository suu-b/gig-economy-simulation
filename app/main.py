from fastapi import FastAPI
from models import Request
import uvicorn

from system import System

app = FastAPI()

# This initializes our system
# Now our client needs to just make request here!``
system = System(total_servers=3)

@app.post("/request")
def create_request(req: Request):
    system.gateway_queue.post_request(req)
    return {"status": "queued"}


if __name__ == '__main__':
    uvicorn.run(app=app, host='0.0.0.0', port=8000)