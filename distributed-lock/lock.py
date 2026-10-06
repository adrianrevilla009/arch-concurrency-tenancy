"""Redis lock with a fencing token. A stale holder's write is rejected by the resource."""
import subprocess, time


def redis(*args):
    return subprocess.run(["docker", "exec", "act-lock-redis", "redis-cli", *args],
                          capture_output=True, text=True, check=True).stdout.strip()


def acquire(name, owner, ttl_ms):
    """SET NX PX gives mutual exclusion; INCR gives a monotonically increasing fencing token."""
    if redis("SET", f"lock:{name}", owner, "NX", "PX", str(ttl_ms)) != "OK":
        return None
    return int(redis("INCR", f"fence:{name}"))


class FencedResource:
    """Storage that refuses writes carrying a token older than the newest it has seen."""

    def __init__(self):
        self.max_token, self.value = 0, None

    def write(self, token, value):
        if token < self.max_token:
            return False
        self.max_token, self.value = token, value
        return True


def main():
    redis("FLUSHALL")
    res = FencedResource()
    t1 = acquire("job", "client-A", 2000)
    assert t1 == 1 and res.write(t1, "A-first")
    assert acquire("job", "client-B", 2000) is None, "lock must be exclusive"
    time.sleep(2.5)  # client A stalls (GC pause) past its TTL, so the lock expires
    t2 = acquire("job", "client-B", 5000)
    assert t2 == 2 and res.write(t2, "B")
    # A wakes up, still believes it holds the lock, and writes with its old token
    assert not res.write(t1, "A-stale"), "fencing must reject the stale token"
    assert res.value == "B"
    print("OK: exclusive, tokens 1->2, stale write rejected")


if __name__ == "__main__":
    main()
