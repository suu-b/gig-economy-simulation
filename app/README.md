# Architecture

## System Roles

### Gateway

- accepts requests
- persists them
- broadcasts their existence

### Servers

- observe all requests
- decide independently whether to act
- compete to claim

### Gateway

- memory (request state)
- messenger (pub/sub)
- judge (atomic claim)
