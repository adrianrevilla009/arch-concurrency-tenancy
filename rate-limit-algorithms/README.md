# rate-limit-algorithms

Token bucket, leaky bucket (meter form) and sliding-window log in `limiters.py`, driven by the same traffic with an injected clock.

## Goal

Compare how three limiters treat one burst and how fast each recovers, without any infrastructure or real time.

## Run it

```bash
python3 limiters.py
```

Expected output:

```
token-bucket (2/s, burst 5)    YYYYYnnnnnYYnnn
leaky-bucket (2/s, cap 5)      YYYYYnnnnnYYnnn
sliding-log (5 per 1s)         YYYYYnnnnnYYYYY
OK: same burst handling, different recovery (sliding log allows 2x at the window edge)
```

## What it proves

- The traffic is 10 requests at t=0 and 5 more at t=1.0; all three admit 5 and reject 5 of the first burst.
- One second later the token and leaky buckets have refilled only 2 slots (`YYnnn`), because they are rate-bound.
- The sliding log has forgotten the whole burst and admits all 5 (`YYYYY`), so up to twice the limit passes across a window edge.

## Trade-offs

- Token bucket allows bursts and needs O(1) memory per key. The leaky bucket here is the meter form, which behaves the same on this input; the queue form that smooths output at a fixed rate is not modelled.
- Sliding log is exact but stores one timestamp per allowed request, O(limit) per key.
- Everything is in-process. A shared limiter would run the same logic in an atomic Redis script, which this folder does not do.

## When not to use it

- When a gateway or CDN already rate limits for you.
- When you need a limiter shared across instances: these classes keep state in memory only.
