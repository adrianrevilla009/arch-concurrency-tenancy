# distributed-lock

A Redis lock (`SET NX PX` plus `INCR`) that hands out fencing tokens, and a small resource in `lock.py` that rejects stale tokens.

## Goal

Show why a lock with a TTL is not safe on its own, and how a fencing token makes the protected resource reject a writer whose lock already expired.

## Run it

```bash
docker compose up -d && sleep 2 && python3 lock.py; docker compose down
```

Expected output (about 3 seconds, the script sleeps past the lock TTL):

```
OK: exclusive, tokens 1->2, stale write rejected
```

## What it proves

- `client-A` gets token 1 and writes; `client-B` is refused while the lock is held.
- After A stalls for 2.5 s (TTL 2 s), B acquires the lock and gets token 2.
- When A wakes up and writes with token 1, `FencedResource.write` returns False and the value stays `B`.

## Trade-offs

- Single Redis node: a failover can lose the lock key. A multi-node lock does not fix the stale-writer problem; only the token check at the resource does.
- `SET` and `INCR` are two commands, not one atomic step. A crash between them burns a token number, which is harmless because tokens stay increasing. A Lua script would make it atomic.
- The resource must understand tokens. That is the real cost of the pattern.
- The script talks to Redis through `docker exec ... redis-cli`, so it needs the container name `act-lock-redis` from `compose.yaml`.

## When not to use it

- When a database row lock or a unique constraint can do the job, or when the work is idempotent.
- When losing the lock is unacceptable: use a consensus store such as etcd or ZooKeeper (not covered here).
