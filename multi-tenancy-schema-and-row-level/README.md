# multi-tenancy-schema-and-row-level

Two tenant isolation models on one Postgres 16.4 container, set up and checked by `tenancy.py` with the Orders table.

## Goal

Contrast schema-per-tenant (`tenant_a`, `tenant_b`) with a shared `orders` table protected by row-level security (RLS).

## Run it

```bash
docker compose up -d && sleep 5 && python3 tenancy.py; docker compose down
```

Expected output:

```
OK: schema isolation, RLS isolation, fail-closed default, owner bypass shown
```

The password in `compose.yaml` is a throwaway for a local container. The script runs `psql` through `docker exec`.

## What it proves

- With `search_path` set to `tenant_a` or `tenant_b`, the role `app` sees only that tenant's order (`a-book` or `b-pen`).
- On the shared table, the policy `by_tenant` filters by `app.tenant`; with no tenant set, `app` gets 0 rows (fail-closed).
- The owner (`postgres`) still sees both rows, because RLS is not forced for the table owner; the application must connect as a non-owner.

## Trade-offs

- Schema-per-tenant gives strong separation and easy per-tenant backup or drop, but migrations run once per tenant and thousands of schemas strain the catalog.
- RLS needs one migration and scales to many tenants, but one missing policy or an owner connection leaks data, and the setting must be applied per connection or transaction (watch pooling).
- The script uses a session `SET` in a single `psql -c` call; an application should use `SET LOCAL` inside a transaction.
- Only `SELECT` is exercised; writes and `WITH CHECK` policies are not.

## When not to use it

- For a few high-value tenants that need hard isolation or separate SLAs, use a database per tenant.
- For a single-tenant application, none of this is needed.
