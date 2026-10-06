# api-versioning

A pure routing function in `versioning.py` that resolves the API version from the URL path, a custom header or the `Accept` media type.

## Goal

Compare three versioning strategies on one Orders resource whose `total` changed shape between v1 and v2.

## Run it

```bash
python3 versioning.py
```

Expected output:

```
OK: 5 routing cases; v1 and v2 serve the same order with a breaking total change
```

There is no HTTP server; the script calls `handle(path, headers, order)` directly.

## What it proves

- `/v1/orders/7`, `X-Api-Version: 2` and `Accept: application/vnd.orders.v1+json` all reach the versioned handlers (v1 returns `12.5`, v2 returns `{"amount": 1250, "currency": "EUR"}`).
- Precedence is explicit in `route`: path, then header, then `Accept`, then the latest version.
- `/v9/orders/7` gets a 406 instead of a silent fallback.

## Trade-offs

- Path versions are visible, cacheable and easy to route, but the version becomes part of the resource URL.
- Header and media-type versions keep URLs clean but are harder to test in a browser and need `Vary` for caches (not modelled here).
- Defaulting to latest means clients that send nothing receive breaking changes; many teams default to the oldest instead.

## When not to use it

- For internal APIs where producer and consumer deploy together.
- When additive, backward-compatible changes (new optional fields) are enough.
