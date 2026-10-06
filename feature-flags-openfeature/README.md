# feature-flags-openfeature

An in-memory provider and client in `flags.py` that follow the OpenFeature shape (client, provider, evaluation context).

## Goal

Show how flag evaluation is split between a client and a provider, with tenant targeting, a sticky percentage rollout and a safe default.

## Run it

```bash
python3 flags.py
```

Expected output:

```
OK: tenant targeting, sticky 30% rollout (275/1000), static flag, safe default
```

## What it proves

- The `new-checkout` flag is on for tenant `acme`, regardless of the rollout percentage.
- For other users, a 30% rollout hashes `flag:targeting_key`, so 275 of 1000 users get it and a second pass returns the identical set.
- An unknown flag returns the caller's default, and the `kill-switch` flag returns its static `False`.

## Trade-offs

- The official OpenFeature SDK and a flagd provider are not installed. `InMemoryProvider` only mimics the `resolve_boolean_details` interface, so the real SDK is not exercised and only boolean flags exist.
- In-memory flags have no hot reload, audit trail or UI; that is what flagd or a vendor adds.
- Flags left in code become debt; remove them after the rollout.

## When not to use it

- For a config value that never varies per user or tenant, use plain configuration.
- For safety-critical gating, do not rely on a flag service being reachable without a defined default.
