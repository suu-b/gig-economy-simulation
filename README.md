# About

The repository is a python simulation of Gig Economy -- the technical models of businesses like Rapido and Swiggy.

# Terminologies

## The System

The system refers to the Global Scope + Servers that listen to and serve client's requests.

## Single-Request Slot universe

It's the universe where only one incomplete request can exist at a time in the system. This further implies that at most one winner can exist in the system at a time.

## Request Lifecycle

Request Lifecycle is the process where the a request once emitted from the client undergoes various stages. It was undefined in the single request slot universe as no two requests could exist in the system simultaneously and the system was naive.  
Since we wish that more than one request can exist in the system, we need to introduce a standard request lifecycle which could be as follows:  
CREATED -> PENDING -> PICKED_UP -> PROCESSING -> DONE -> EXPIRED

CREATED: The request has been emitted by the client but has not entered the system yet.  
PENDING: Has entered the system and waiting to be picked up.  
PICKED_UP: Has been picked up but processing has not yet started.  
PROCESSING: Being processed not yet done.  
DONE: Done waiting to be expired.  
EXPIRED: Expired -- EOL.

# Vision Board

v0.3

1. Redis Integration

~~v0.2~~

~~ 1. Define a request lifecycle.~~
~~ 2. Let multiple clients create requests at one single time, pass them all through a buffer queue that pushes one request at a time in the system~~

~~v0.1~~

~~1. Enable a single request-slot universe with multiprocessing in python~~
