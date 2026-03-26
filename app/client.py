import requests
import time
import uuid

API_URL = "http://localhost:8000/request"

def create_request():
    return {
        "id": f"REQ-{uuid.uuid4()}",
        "content": "some work to be done",
        "timestamp": time.time()
    }

def main():
    while True:
        req = create_request()
        try:
            res = requests.post(API_URL, json=req)
            print(f"Sent {req['id']} | Status: {res.status_code}")
        except Exception as e:
            print(f"Failed to send request: {e}")

        time.sleep(2)


if __name__ == "__main__":
    main()