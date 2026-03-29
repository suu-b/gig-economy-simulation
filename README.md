# About

The repository birthed from my fascination towards the technical models of gig businesses like Rapido and Swiggy, specifically the way they handle requests of clients and distributedly operate with their on-field employees i.e. delivery men.

Note: Servers and Workers are interchangeable in this case.

# Evolution

## Single Request-Slot Universe

I leveraged `multiprocessing` library of python to spin up a distributed system in the project. Servers (Workers) and Clients were all different python processes. A Client could put their request in a single global slot, once filled every server will be notified. Some of them would ignore the request, others would show interest. Only one will be able to claim it and proceed further.

This was a first step and a naive approach. Consequently, there were many issues. The major issue was that no other client can put their request until the slot's empty.

## Illusion: Users can make multiple requests now!

To allow multiple users make request simultaneously (or at least without waiting for one to finish), I introduced a gateway queue which would act like a buffer. It would collect client's requests but the single-request slot universe is still intact. Until the slot is empty, the queue cannot put a request in it. Client would not require to wait just to put their request, but the turnaround time won't be decreased because the requests will still be waiting. So essentially, it is an illusion.

## Master: A better, more rich, decoupled approach to the problem

Then I introduced redis pubsub into the scene. It removed the queue. I made a few architectural choices to divide the whole system into components. I made efforts to keep them decoupled as much I could do.

Redis allowed multi-user support as it gave a distributed cache to store requests with a pubsub mechanism to notify workers. Native `notify_all()` was used previously to notify servers about a new request. But it had one major issue: I could notify them that a request has arrived but couldn't directly publish the request to them. They had to read from a common, critical dictionary. Redis abstracted this a lot.

All clients are exposed an API. They can make requests, once picked up - track the progress, and can get history of all the completed requests. All this through simple HTTP calls.

Redis operates on a host and port. Each worker and the server initialize their own redis instance on them. This proves to be very decoupled and flexible approach.

Real-time updates are provided to the client about their request completion by the respective server. All this through SSE - Server Sent Events.

# Project State

This brings the state of the project to as follows:

_A Distributed Request Dispatch System where work is broadcast to multiple workers. Ownership is determined through first-claim mechanism.
Workers stream real-time updates back to clients until completed._

# Project Structure

1. `app/`: contains the master approach to the problem. `main.py` contains the api that exposes endpoints to client. `client.py` is a sample script client. `server.py` is an individual worker. `redis_client.py` is an abstraction of Redis and is initialized by workers and main. `system.py` spins up the workers. Others are metadata files.
2. `multiprocessing/`: contains the native python approach.
3. `redis-pub-sub/`: contains the redis-pub-sub paired with native python. It is kinda intermediary stage between `app/` and `multiprocessing`.
4. `ui/`: contains an HTML and vanilla-JS frontend that provides sample usage of the api. It contains a dashboard that shows the history of all completed requests. It can create clients to simulate a real-world scenario by putting our system to work.

# Setup

1. Ensure latest version of python installed. Mine is `Python 3.13.7`.
2. Create a virtual env and activate it.
3. `pip install -r requirements.txt`
4. `cd app`
5. In separate terminal tabs do the following:
6. Spin up system with 10 workers -> `python system.py --servers 10`
7. Spin up api -> `python main.py`
8. Open `ui/dashboard.html` in some web browser.
9. You can see history in the dashboard (visible once you make some requests).
10. Use the button to create a new client and submit request. You will able to see its realtime updates below, once completed it will be visible in the dashboard view as well.
