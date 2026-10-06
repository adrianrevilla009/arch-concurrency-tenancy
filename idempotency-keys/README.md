# idempotency-keys

An order-creation function in `idempotency.py` that claims an idempotency key in Redis before running its side effect.

## Goal

Make `POST /orders` safe to retry: one key runs the side effect once and later calls replay the stored response.

## Run it

```bash
docker compose up -d && sleep 2 && python3 idempotency.py; docker compose down
```

Expected output (the status list can contain 409 if a request arrives while the first is still running):

```
OK: replay returns stored response, payload mismatch 422, 5 concurrent -> 1 charge [200, 200, 200, 200, 200]
```

## What it proves

- A retry with the same key and payload returns `(200, "order-1:book")` and `CHARGES` still holds one entry.
- The same key with a different payload is rejected with 422, using a SHA-256 fingerprint of the body.
- Five threads sending one new key cause exactly one side effect, because `SET NX` lets only one claim it; the others get 409 or the replay.

## Trade-offs

- The claim and the side effect are not one transaction. A crash after the effect but before the result is stored leaves the key `in_progress` until the 60 s TTL expires. Production code stores key and effect in the same database transaction.
- Keys expire; pick a TTL longer than any client retry window.
- The side effect is an in-process list standing in for a payment or insert, and there is no HTTP layer.

## When not to use it

- When the operation is naturally idempotent (PUT, upsert, delete).
- When a database unique constraint on a business key already prevents duplicates.
