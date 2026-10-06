# leader-election

Lease-based leader election on Redis: two simulated nodes in `election.py` compete for one expiring key.

## Goal

Elect a single leader with an expiring lease, and show failover when the leader stops renewing.

## Run it

```bash
docker compose up -d && sleep 2 && python3 election.py; docker compose down
```

Expected output (about 4 seconds):

```
OK: a led, lease lapsed, b took over, a stayed follower
```

## What it proves

- Node `a` takes the `leader` key with `SET NX PX 2000` and keeps it by renewing with `PEXPIRE`; node `b` is refused on every tick.
- When `a` stops renewing, the key expires after 2 s and `b` takes over.
- When `a` ticks again, it sees `b` as holder and does not take leadership back.

## Trade-offs

- Redis stands in for ZooKeeper or etcd so the lab runs offline with one small image. Etcd leases and ZooKeeper ephemeral nodes are the usual production choices.
- Check-then-renew (`GET`, then `PEXPIRE`) is not atomic, so a stalled leader can still believe it leads. Pair it with fencing tokens, as in `distributed-lock`.
- Failover time is bounded by the lease length; shorter leases fail over faster but flap more.
- Both nodes run in one process, not on separate machines, so network partitions are not exercised.

## When not to use it

- When two leaders must never exist: use a consensus store plus fencing.
- When a database job queue (`SELECT ... FOR UPDATE SKIP LOCKED`) can spread the work without electing anyone.
