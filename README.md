# arch-concurrency-tenancy

Seven small, runnable examples of concurrency and multi-tenancy patterns (fencing locks, leader election, rate limiters, tenant isolation, feature flags, API versioning, idempotency keys), all around a tiny Orders domain.

## What is inside

| Folder | What it shows | Run |
| --- | --- | --- |
| [`distributed-lock`](./distributed-lock) | Redis lock with a fencing token that rejects a stale writer | `docker compose up -d && sleep 2 && python3 lock.py; docker compose down` |
| [`leader-election`](./leader-election) | Lease-based leader election on Redis with failover | `docker compose up -d && sleep 2 && python3 election.py; docker compose down` |
| [`rate-limit-algorithms`](./rate-limit-algorithms) | Token bucket, leaky bucket and sliding-window log on the same burst | `python3 limiters.py` |
| [`multi-tenancy-schema-and-row-level`](./multi-tenancy-schema-and-row-level) | Schema-per-tenant versus row-level security in Postgres | `docker compose up -d && sleep 5 && python3 tenancy.py; docker compose down` |
| [`feature-flags-openfeature`](./feature-flags-openfeature) | OpenFeature-shaped client and provider with targeting and percentage rollout | `python3 flags.py` |
| [`api-versioning`](./api-versioning) | Path, header and media-type versioning routed to the same handlers | `python3 versioning.py` |
| [`idempotency-keys`](./idempotency-keys) | Retry-safe order creation with an idempotency key on Redis | `docker compose up -d && sleep 2 && python3 idempotency.py; docker compose down` |

Run each command from inside its folder.

## Prerequisites

- Python 3 (standard library only, no packages to install)
- Docker with Compose, for the four folders that use Redis 7.4.1 or Postgres 16.4 (the scripts call `redis-cli` and `psql` through `docker exec`)

## How to read it

Start with `rate-limit-algorithms` (no infrastructure), then `distributed-lock`, which `leader-election` builds on conceptually. ZooKeeper, etcd and the OpenFeature SDK are not used; each folder's Trade-offs says what stands in for them.
