"""Idempotency keys on Redis: a retried or concurrent request replays the stored response."""
import hashlib, json, subprocess
from concurrent.futures import ThreadPoolExecutor


def redis(*args):
    return subprocess.run(["docker", "exec", "act-idem-redis", "redis-cli", *args],
                          capture_output=True, text=True, check=True).stdout.strip()


CHARGES = []  # the side effect we must not repeat


def create_order(key, body):
    fp = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    rkey = f"idem:{key}"
    # claim the key atomically; the loser never runs the side effect
    if redis("SET", rkey, json.dumps({"fp": fp, "state": "in_progress"}), "NX", "EX", "60") != "OK":
        rec = json.loads(redis("GET", rkey))
        if rec["fp"] != fp:
            return 422, "key reused with a different payload"
        if rec["state"] == "in_progress":
            return 409, "request in progress, retry later"
        return 200, rec["response"]
    CHARGES.append(body["item"])
    response = f"order-{len(CHARGES)}:{body['item']}"
    redis("SET", rkey, json.dumps({"fp": fp, "state": "done", "response": response}), "EX", "60")
    return 200, response


def main():
    redis("FLUSHALL")
    first = create_order("k1", {"item": "book"})
    retry = create_order("k1", {"item": "book"})
    assert first == retry == (200, "order-1:book") and CHARGES == ["book"]
    assert create_order("k1", {"item": "pen"})[0] == 422
    with ThreadPoolExecutor(5) as pool:  # five simultaneous retries of a new key
        out = list(pool.map(lambda _: create_order("k2", {"item": "ink"}), range(5)))
    assert CHARGES.count("ink") == 1, CHARGES
    assert sum(1 for s, _ in out if s == 200) >= 1
    print(f"OK: replay returns stored response, payload mismatch 422, 5 concurrent -> 1 charge {sorted(s for s, _ in out)}")


if __name__ == "__main__":
    main()
